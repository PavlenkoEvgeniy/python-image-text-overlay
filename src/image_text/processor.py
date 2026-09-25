"""Core image processing logic."""

import logging
import os
from enum import Enum
from typing import Optional, Tuple

from typing import Union

from PIL import Image, ImageDraw, ImageFont, ImageOps

# Type alias for font objects
FontType = Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]

from .config import config

logger = logging.getLogger(__name__)


def load_image(path: str) -> Image.Image:
    """Load an image with its visual orientation baked into pixels.

    Viewers display an image according to its EXIF Orientation tag, which may
    differ from how pixels are physically stored in the file. This function
    transposes the pixels to match the visual orientation, so all further
    processing works on what the user sees.

    Args:
        path: Path to the image file.

    Returns:
        PIL Image in visual orientation.
    """
    return ImageOps.exif_transpose(Image.open(path))


class FontStyle(Enum):
    """Font style enumeration."""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold italic"


class TextPosition(Enum):
    """Text position enumeration."""
    TOP_LEFT = "top left"
    TOP_RIGHT = "top right"
    BOTTOM_LEFT = "bottom left"
    BOTTOM_RIGHT = "bottom right"
    CENTER = "center"


class ImageProcessor:
    """Handles image text overlay processing."""

    # Shear factor used to synthesize italic (oblique) text.
    ITALIC_SHEAR = 0.25

    def __init__(
        self,
        text: str = "",
        color: str = "#FFFFFF",
        font_family: Optional[str] = None,
        font_path: Optional[str] = None,
        font_size: int = 40,
        font_style: str = "Normal",
        position: str = "bottom right",
        offset_up: int = 20,
        offset_left: int = 20,
    ):
        """Initialize the image processor.

        Args:
            text: Text to overlay on images.
            color: Text color (hex format).
            font_family: System font family name. Ignored when font_path is set.
            font_path: Path to custom font file; takes precedence over font_family.
            font_size: Font size in pixels.
            font_style: Font style (Normal, Bold, Italic, Bold Italic).
            position: Text position on image.
            offset_up: Vertical offset in pixels.
            offset_left: Horizontal offset in pixels.
        """
        self.text = text
        self.color = color
        self.font_family = font_family
        self.font_path = font_path
        self.font_size = font_size
        self.font_style = font_style
        self.position = position
        self.offset_up = offset_up
        self.offset_left = offset_left

    # Suffix appended to a family name to probe its styled variant
    STYLE_SUFFIXES = {
        "Normal": "",
        "Bold": " Bold",
        "Italic": " Italic",
        "Bold Italic": " Bold Italic",
    }

    # Style names as fontconfig reports them
    FC_STYLE_NAMES = {
        "Normal": "Regular",
        "Bold": "Bold",
        "Italic": "Italic",
        "Bold Italic": "Bold Italic",
    }

    def _load_system_font(self, size: int) -> Optional[FontType]:
        """Load a system font by the selected family name.

        The styled variant of the family (e.g. "DejaVu Sans Bold") is probed
        before the plain family name. Family names are resolved to font files
        via fontconfig, falling back to direct TrueType name lookups.

        Args:
            size: Font size in pixels.

        Returns:
            ImageFont object, or None when the family is not set or cannot
            be resolved (the fallback chain then applies).
        """
        family = (self.font_family or "").strip()
        if not family:
            return None

        style = (self.font_style or "").strip()
        suffix = self.STYLE_SUFFIXES.get(style, "")

        # Try the styled variant name before the plain family name
        for name in ([family + suffix] if suffix else []) + [family]:
            try:
                font = ImageFont.truetype(name, size)
                logger.debug(f"Loaded system font: {name}")
                return font
            except Exception:
                continue

        fc_style = self.FC_STYLE_NAMES.get(style, "Regular")
        for path in self._fontconfig_candidates(family, fc_style):
            try:
                font = ImageFont.truetype(path, size)
                logger.debug(f"Loaded system font: {path}")
                return font
            except Exception:
                continue

        logger.debug(f"Could not resolve system font family: {family}")
        return None

    @staticmethod
    def _fontconfig_candidates(family: str, fc_style: str) -> list:
        """Query fontconfig for font files of a family, best style first.

        Args:
            family: Font family name.
            fc_style: Requested style in fontconfig terms (e.g. "Bold").

        Returns:
            List of file paths matching the family, with files carrying the
            requested style first, then Regular, then the rest.
        """
        import subprocess

        try:
            result = subprocess.run(
                ["fc-list", f":family={family}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as e:
            logger.debug(f"fontconfig query failed for {family}: {e}")
            return []

        exact, regular, others = [], [], []
        for line in result.stdout.splitlines():
            path, _, meta = line.partition(":")
            path = path.strip()
            if not path or not os.path.exists(path):
                continue
            styles = (
                [s.strip().lower() for s in meta.split("style=")[-1].split(",")]
                if "style=" in meta
                else []
            )
            if fc_style.lower() in styles:
                exact.append(path)
            elif "regular" in styles:
                regular.append(path)
            else:
                others.append(path)
        return exact + regular + others

    def _font_candidates(self, size: int):
        """Yield loadable font candidates in priority order.

        The single-font rule orders the chain: a custom font file first,
        then the selected system family, then the fallback system fonts,
        and finally the default PIL font.

        Args:
            size: Font size in pixels.

        Yields:
            Loadable ImageFont objects.
        """
        # Custom font first
        if self.font_path and os.path.exists(self.font_path):
            try:
                font = ImageFont.truetype(self.font_path, size)
                logger.debug(f"Loaded custom font: {self.font_path}")
                yield font
            except Exception as e:
                logger.warning(
                    f"Failed to load custom font {self.font_path}: {e}. Using fallback."
                )

        # System font selected by family name
        font = self._load_system_font(size)
        if font is not None:
            yield font

        # Fallback system fonts
        for font_name in config.system_fonts:
            try:
                yield ImageFont.truetype(font_name, size)
            except Exception:
                continue

        # Fallback to default font
        logger.info("Using default PIL font")
        yield ImageFont.load_default()

    def get_font(self, size: int) -> FontType:
        """Get PIL ImageFont honoring the single-font rule.

        A custom font file, when set, is the active font. Otherwise the
        selected system family is used. If neither resolves, the fallback
        chain applies.

        Args:
            size: Font size in pixels.

        Returns:
            ImageFont object.
        """
        for font in self._font_candidates(size):
            return font
        # Unreachable: the candidate chain always ends with the default font
        return ImageFont.load_default()

    def get_font_for_text(self, size: int, text: str) -> FontType:
        """Get a PIL ImageFont that actually renders the given text.

        Candidates are tried in priority order (see get_font). A font that
        loads but draws no visible glyphs for the text — its glyph set may
        not cover it, rendering everything as blank — is skipped with a
        warning in favor of the next candidate. When even the final default
        font renders nothing, it is still returned.

        Args:
            size: Font size in pixels.
            text: Text the font must be able to draw.

        Returns:
            ImageFont object.
        """
        last: Optional[FontType] = None
        for font in self._font_candidates(size):
            last = font
            if self._renders_text(font, text):
                return font
            source = getattr(font, "path", "default PIL font")
            logger.warning(f"Font {source} lacks glyphs for the text; trying next")
        return last if last is not None else ImageFont.load_default()

    @staticmethod
    def _renders_text(font: FontType, text: str) -> bool:
        """Check the font draws at least one visible pixel for the text.

        A font can load cleanly and still have no glyphs for the text, so
        every character falls back to a blank .notdef glyph and the overlay
        disappears. Whitespace-only text renders nothing with any font and
        is always considered renderable.

        Args:
            font: Font to probe.
            text: Text to draw.

        Returns:
            True when at least one pixel is drawn.
        """
        if not text.strip():
            return True

        try:
            left, top, right, bottom = font.getbbox(text)
        except Exception:
            # Cannot measure the text: assume the font renders it
            return True

        layer = Image.new(
            "RGBA",
            (max(1, right - left + 4), max(1, bottom - top + 4)),
            (0, 0, 0, 0),
        )
        draw = ImageDraw.Draw(layer)
        draw.text((2 - left, 2 - top), text, fill=(255, 255, 255, 255), font=font)
        _, max_alpha = layer.getchannel("A").getextrema()
        return max_alpha > 0

    def _get_style_flags(self) -> Tuple[bool, bool]:
        """Get (bold, italic) flags from the font style setting.

        Returns:
            Tuple of (bold, italic) flags.
        """
        style = (self.font_style or "").strip().lower()
        return "bold" in style, "italic" in style

    def _get_stroke_width(self, size: int, bold: bool) -> int:
        """Get stroke width used to synthesize bold text.

        Args:
            size: Font size in pixels.
            bold: Whether bold style is requested.

        Returns:
            Stroke width in pixels (0 for non-bold text).
        """
        if not bold:
            return 0
        return max(1, round(size / 25))

    def get_text_size(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: FontType,
        stroke_width: int = 0,
    ) -> Tuple[int, int, int, int]:
        """Calculate text bounding box dimensions.

        Args:
            draw: PIL ImageDraw object.
            text: Text to measure.
            font: Font to use.
            stroke_width: Stroke width the text will be drawn with.

        Returns:
            Tuple of (width, height, offset_x, offset_y) — the size of the
            bounding box and the offset of its top-left corner from the
            layout origin.
        """
        try:
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            offset_x, offset_y = bbox[0], bbox[1]
        except Exception:
            # Fallback for older PIL versions
            width, height = draw.textsize(text, font=font)
            offset_x, offset_y = 0, 0
        return int(width), int(height), int(offset_x), int(offset_y)

    def calculate_position(
        self,
        img_width: int,
        img_height: int,
        text_width: int,
        text_height: int,
    ) -> Tuple[int, int]:
        """Calculate text position based on settings.

        Args:
            img_width: Image width in pixels.
            img_height: Image height in pixels.
            text_width: Text width in pixels.
            text_height: Text height in pixels.

        Returns:
            Tuple of (x, y) coordinates.
        """
        position = self.position

        offset_up = self.offset_up
        offset_left = self.offset_left

        x = 0
        y = 0

        if position == "top left":
            x = offset_left
            y = offset_up
        elif position == "top right":
            x = img_width - text_width - offset_left
            y = offset_up
        elif position == "bottom left":
            x = offset_left
            y = img_height - text_height - offset_up
        elif position == "bottom right":
            x = img_width - text_width - offset_left
            y = img_height - text_height - offset_up
        elif position == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2

        return x, y

    def apply_text(self, image: Image.Image) -> Optional[Image.Image]:
        """Apply text overlay to image.

        Args:
            image: PIL Image object.

        Returns:
            New PIL Image with text overlay, or None if text is empty.
        """
        if not self.text:
            logger.warning("No text provided for overlay")
            return None

        img = image.copy()
        draw = ImageDraw.Draw(img)

        font = self.get_font_for_text(self.font_size, self.text)
        bold, italic = self._get_style_flags()
        stroke_width = self._get_stroke_width(self.font_size, bold)

        text_width, text_height, offset_x, offset_y = self.get_text_size(
            draw, self.text, font, stroke_width
        )

        # Italic shear widens the rendered text to the right
        shear_extra = int(self.ITALIC_SHEAR * text_height) if italic else 0
        text_width += shear_extra

        x, y = self.calculate_position(img.width, img.height, text_width, text_height)

        if italic:
            self._draw_italic_text(
                img, x, y, text_width, text_height, offset_x, offset_y,
                font, stroke_width,
            )
        else:
            draw.text(
                (x, y),
                self.text,
                fill=self.color,
                font=font,
                stroke_width=stroke_width,
                stroke_fill=self.color,
            )

        logger.info(
            f"Applied text overlay: '{self.text}' at position ({x}, {y}) "
            f"(style: {self.font_style})"
        )
        return img

    def _draw_italic_text(
        self,
        img: Image.Image,
        x: int,
        y: int,
        text_width: int,
        text_height: int,
        offset_x: int,
        offset_y: int,
        font: FontType,
        stroke_width: int,
    ) -> None:
        """Draw text with a synthesized oblique (italic) shear.

        The text is rendered onto a transparent layer, sheared so that the
        top leans right while the baseline stays in place, then pasted onto
        the target image.

        Args:
            img: Target image.
            x: Left coordinate of the text bounding box.
            y: Top coordinate of the text bounding box.
            text_width: Rendered text width in pixels (shear extra included).
            text_height: Rendered text height in pixels.
            offset_x: Horizontal offset of the text bounding box.
            offset_y: Vertical offset of the text bounding box.
            font: Font to draw with.
            stroke_width: Stroke width for bold synthesis.
        """
        pad = stroke_width + 2
        layer = Image.new(
            "RGBA", (text_width + 2 * pad, text_height + 2 * pad), (0, 0, 0, 0)
        )
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.text(
            (pad - offset_x, pad - offset_y),
            self.text,
            fill=self.color,
            font=font,
            stroke_width=stroke_width,
            stroke_fill=self.color,
        )

        shear = self.ITALIC_SHEAR
        offset = int(shear * layer.height)
        layer = layer.transform(
            (layer.width + offset, layer.height),
            Image.AFFINE,
            (1, shear, -shear * layer.height, 0, 1, 0),
        )

        img.paste(layer, (x - pad, y - pad), layer)

    def process_image_path(self, image_path: str) -> Optional[Image.Image]:
        """Load and process an image from path.

        Args:
            image_path: Path to image file.

        Returns:
            Processed PIL Image, or None on error.
        """
        try:
            img = load_image(image_path)
            return self.apply_text(img)
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return None

    def get_output_path(self, original_path: str, output_dir: str) -> str:
        """Generate output file path.

        Args:
            original_path: Original image file path.
            output_dir: Output directory path.

        Returns:
            Output file path (unique if file exists).
        """
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(original_path)
        name, ext = os.path.splitext(base_name)
        output_filename = f"{name}_text{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # Add suffix if file exists
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{name}_text_{counter}{ext}")
            counter += 1

        return output_path

    @classmethod
    def from_dict(cls, settings: dict) -> "ImageProcessor":
        """Create ImageProcessor from dictionary.

        Args:
            settings: Dictionary with settings.

        Returns:
            ImageProcessor instance.
        """
        return cls(
            text=settings.get("text", ""),
            color=settings.get("color", config.default_color),
            font_family=settings.get("font_family"),
            font_path=settings.get("font_path"),
            font_size=settings.get("font_size", config.default_font_size),
            font_style=settings.get("font_style", config.default_font_style),
            position=settings.get("position", config.default_position),
            offset_up=settings.get("offset_up", config.default_offset_up),
            offset_left=settings.get("offset_left", config.default_offset_left),
        )

    def to_dict(self) -> dict:
        """Convert processor settings to dictionary.

        Returns:
            Dictionary with settings.
        """
        return {
            "text": self.text,
            "color": self.color,
            "font_family": self.font_family,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "font_style": self.font_style,
            "position": self.position,
            "offset_up": self.offset_up,
            "offset_left": self.offset_left,
        }