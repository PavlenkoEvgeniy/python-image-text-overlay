"""Core image processing logic."""

import logging
import os
from enum import Enum
from typing import Optional, Tuple

from typing import Union

from PIL import Image, ImageDraw, ImageFont

# Type alias for font objects
FontType = Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]

from .config import config

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        text: str = "",
        color: str = "#FFFFFF",
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
            font_path: Path to custom font file.
            font_size: Font size in pixels.
            font_style: Font style (Normal, Bold, Italic, Bold Italic).
            position: Text position on image.
            offset_up: Vertical offset in pixels.
            offset_left: Horizontal offset in pixels.
        """
        self.text = text
        self.color = color
        self.font_path = font_path
        self.font_size = font_size
        self.font_style = font_style
        self.position = position
        self.offset_up = offset_up
        self.offset_left = offset_left

    def get_font(self, size: int) -> FontType:
        """Get PIL ImageFont with specified style.

        Args:
            size: Font size in pixels.

        Returns:
            ImageFont object.
        """
        style = self.font_style

        if style == "Bold":
            pil_style = "bold"
        elif style == "Italic":
            pil_style = "italic"
        elif style == "Bold Italic":
            pil_style = "bold italic"
        else:
            pil_style = "normal"

        # Try custom font first
        if self.font_path and os.path.exists(self.font_path):
            try:
                font = ImageFont.truetype(self.font_path, size)
                logger.debug(f"Loaded custom font: {self.font_path}")
                return font
            except Exception as e:
                logger.warning(f"Failed to load custom font {self.font_path}: {e}. Using fallback.")

        # Try system fonts
        for font_name in config.system_fonts:
            try:
                font = ImageFont.truetype(font_name, size)
                logger.debug(f"Loaded system font: {font_name}")
                return font
            except Exception:
                continue

        # Fallback to default font
        logger.info("Using default PIL font")
        return ImageFont.load_default()

    def get_text_size(self, draw: ImageDraw.ImageDraw, text: str, font: FontType) -> Tuple[int, int]:
        """Calculate text bounding box dimensions.

        Args:
            draw: PIL ImageDraw object.
            text: Text to measure.
            font: Font to use.

        Returns:
            Tuple of (width, height).
        """
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except Exception:
            # Fallback for older PIL versions
            width, height = draw.textsize(text, font=font)
        return int(width), int(height)

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

        font = self.get_font(self.font_size)
        text_width, text_height = self.get_text_size(draw, self.text, font)
        x, y = self.calculate_position(img.width, img.height, text_width, text_height)

        draw.text((x, y), self.text, fill=self.color, font=font)

        logger.info(f"Applied text overlay: '{self.text}' at position ({x}, {y})")
        return img

    def process_image_path(self, image_path: str) -> Optional[Image.Image]:
        """Load and process an image from path.

        Args:
            image_path: Path to image file.

        Returns:
            Processed PIL Image, or None on error.
        """
        try:
            img = Image.open(image_path)
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
            "font_path": self.font_path,
            "font_size": self.font_size,
            "font_style": self.font_style,
            "position": self.position,
            "offset_up": self.offset_up,
            "offset_left": self.offset_left,
        }