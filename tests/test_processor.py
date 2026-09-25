"""Tests for image_text package."""

import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from PIL import Image, ImageFont

from image_text.config import AppConfig, config
from image_text.processor import ImageProcessor, load_image


# --- Fixtures ---

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    img_path = os.path.join(temp_dir, "test_image.png")
    img = Image.new("RGB", (200, 100), color="white")
    img.save(img_path)
    return img_path


@pytest.fixture
def sideways_image(temp_dir):
    """Create a JPEG whose pixels are stored horizontally but with an EXIF
    Orientation tag (6) telling viewers to rotate them 90° clockwise."""
    img_path = os.path.join(temp_dir, "sideways_image.jpg")
    img = Image.new("RGB", (200, 100), color="white")
    # Distinct top-right corner region to verify transposition
    for x in range(190, 200):
        for y in range(10):
            img.putpixel((x, y), (255, 0, 0))
    exif = img.getexif()
    exif[274] = 6  # Orientation: rotate 90° CW for display
    img.save(img_path, exif=exif)
    return img_path


@pytest.fixture
def processor():
    """Create an ImageProcessor with default settings."""
    return ImageProcessor(
        text="Test Text",
        color="#FFFFFF",
        font_size=20,
    )


# --- Config Tests ---

class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_values(self):
        """Test configuration default values."""
        cfg = AppConfig()
        assert cfg.name == "Image Text Overlay"
        assert cfg.version == "1.0.5"
        assert cfg.default_text == "Your text"
        assert cfg.default_color == "#FFFFFF"
        assert cfg.default_font_size == 40
        assert cfg.default_position == "bottom right"
        assert cfg.default_offset_up == 20
        assert cfg.default_offset_left == 20

    def test_valid_image_extensions(self):
        """Test valid image extensions."""
        assert ".png" in config.valid_extensions
        assert ".jpg" in config.valid_extensions
        assert ".jpeg" in config.valid_extensions

    def test_font_styles(self):
        """Test font styles."""
        assert "Normal" in config.font_styles
        assert "Bold" in config.font_styles
        assert "Italic" in config.font_styles
        assert "Bold Italic" in config.font_styles

    def test_text_positions(self):
        """Test text positions."""
        assert "top left" in config.text_positions
        assert "top right" in config.text_positions
        assert "bottom left" in config.text_positions
        assert "bottom right" in config.text_positions
        assert "center" in config.text_positions


# --- Processor Tests ---

class TestImageProcessor:
    """Tests for ImageProcessor."""

    def test_init_default_values(self):
        """Test processor initialization with defaults."""
        p = ImageProcessor()
        assert p.text == ""
        assert p.color == "#FFFFFF"
        assert p.font_path is None
        assert p.font_size == 40
        assert p.font_style == "Normal"
        assert p.position == "bottom right"
        assert p.offset_up == 20
        assert p.offset_left == 20

    def test_init_custom_values(self):
        """Test processor initialization with custom values."""
        p = ImageProcessor(
            text="Hello",
            color="#FF0000",
            font_size=30,
            font_style="Bold",
            position="center",
            offset_up=10,
            offset_left=15,
        )
        assert p.text == "Hello"
        assert p.color == "#FF0000"
        assert p.font_size == 30
        assert p.font_style == "Bold"
        assert p.position == "center"
        assert p.offset_up == 10
        assert p.offset_left == 15

    def test_get_font_default(self, processor):
        """Test getting default font."""
        font = processor.get_font(20)
        assert font is not None

    def test_apply_text_no_text(self, processor):
        """Test applying text with empty text returns None."""
        processor.text = ""
        img = Image.new("RGB", (100, 100), color="white")
        result = processor.apply_text(img)
        assert result is None

    def test_apply_text_with_text(self, processor):
        """Test applying text to image."""
        img = Image.new("RGB", (200, 100), color="white")
        result = processor.apply_text(img)
        assert result is not None
        assert result.size == img.size

    def test_process_image_path(self, processor, sample_image):
        """Test processing image from path."""
        result = processor.process_image_path(sample_image)
        assert result is not None

    def test_process_image_path_invalid(self, processor, temp_dir):
        """Test processing invalid image path."""
        invalid_path = os.path.join(temp_dir, "nonexistent.png")
        result = processor.process_image_path(invalid_path)
        assert result is None

    def test_get_output_path(self, processor, sample_image, temp_dir):
        """Test output path generation."""
        output_dir = os.path.join(temp_dir, "output")
        output_path = processor.get_output_path(sample_image, output_dir)
        assert output_path.startswith(output_dir)
        assert "_text.png" in output_path

    def test_get_output_path_unique(self, processor, sample_image, temp_dir):
        """Test unique output path when file exists."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # First call
        path1 = processor.get_output_path(sample_image, output_dir)
        # Create the file
        Image.new("RGB", (10, 10)).save(path1)

        # Second call should give unique path
        path2 = processor.get_output_path(sample_image, output_dir)
        assert path1 != path2
        assert "_text_1.png" in path2

    def test_calculate_position_top_left(self, processor):
        """Test position calculation for top left."""
        processor.position = "top left"
        processor.offset_up = 10
        processor.offset_left = 5
        x, y = processor.calculate_position(200, 100, 50, 20)
        assert x == 5
        assert y == 10

    def test_calculate_position_top_right(self, processor):
        """Test position calculation for top right."""
        processor.position = "top right"
        processor.offset_up = 10
        processor.offset_left = 5
        x, y = processor.calculate_position(200, 100, 50, 20)
        assert x == 145  # 200 - 50 - 5
        assert y == 10

    def test_calculate_position_bottom_left(self, processor):
        """Test position calculation for bottom left."""
        processor.position = "bottom left"
        processor.offset_up = 10
        processor.offset_left = 5
        x, y = processor.calculate_position(200, 100, 50, 20)
        assert x == 5
        assert y == 70  # 100 - 20 - 10

    def test_calculate_position_bottom_right(self, processor):
        """Test position calculation for bottom right."""
        processor.position = "bottom right"
        processor.offset_up = 10
        processor.offset_left = 5
        x, y = processor.calculate_position(200, 100, 50, 20)
        assert x == 145
        assert y == 70

    def test_calculate_position_center(self, processor):
        """Test position calculation for center."""
        processor.position = "center"
        x, y = processor.calculate_position(200, 100, 50, 20)
        assert x == 75  # (200 - 50) // 2
        assert y == 40  # (100 - 20) // 2

    def test_from_dict(self):
        """Test creating processor from dictionary."""
        settings = {
            "text": "Hello",
            "color": "#FF0000",
            "font_size": 30,
            "font_style": "Bold",
            "position": "top left",
            "offset_up": 5,
            "offset_left": 10,
        }
        p = ImageProcessor.from_dict(settings)
        assert p.text == "Hello"
        assert p.color == "#FF0000"
        assert p.font_size == 30
        assert p.font_style == "Bold"
        assert p.position == "top left"
        assert p.offset_up == 5
        assert p.offset_left == 10

    def test_from_dict_defaults(self):
        """Test creating processor from dict with defaults."""
        p = ImageProcessor.from_dict({})
        assert p.text == ""
        assert p.color == "#FFFFFF"
        assert p.font_size == 40
        assert p.position == "bottom right"

    def test_to_dict(self, processor):
        """Test converting processor to dictionary."""
        d = processor.to_dict()
        assert d["text"] == "Test Text"
        assert d["color"] == "#FFFFFF"
        assert d["font_size"] == 20
        assert "font_style" in d
        assert "position" in d
        assert "offset_up" in d
        assert "offset_left" in d

    def test_font_style_mapping(self, processor):
        """Test font style mapping."""
        processor.font_style = "Normal"
        font = processor.get_font(20)
        assert font is not None

        processor.font_style = "Bold"
        font = processor.get_font(20)
        assert font is not None

        processor.font_style = "Italic"
        font = processor.get_font(20)
        assert font is not None

        processor.font_style = "Bold Italic"
        font = processor.get_font(20)
        assert font is not None


# --- Font Style Rendering Tests ---

class TestFontStyleRendering:
    """Tests that font styles actually change the rendered output (issue #3)."""

    @staticmethod
    def _render(font_style: str, **kwargs) -> Image.Image:
        """Render 'Test' text on a black image with the given style."""
        processor = ImageProcessor(
            text="Test Text",
            color="#FFFFFF",
            font_size=30,
            font_style=font_style,
            position="top left",
            offset_up=5,
            offset_left=5,
            **kwargs,
        )
        img = Image.new("RGB", (300, 100), color="black")
        return processor.apply_text(img)

    def test_bold_differs_from_normal(self):
        """Test bold style changes rendered pixels."""
        normal = self._render("Normal")
        bold = self._render("Bold")
        assert normal.tobytes() != bold.tobytes()

    def test_italic_differs_from_normal(self):
        """Test italic style changes rendered pixels."""
        normal = self._render("Normal")
        italic = self._render("Italic")
        assert normal.tobytes() != italic.tobytes()

    def test_bold_italic_differs_from_bold(self):
        """Test bold italic style differs from bold only."""
        bold = self._render("Bold")
        bold_italic = self._render("Bold Italic")
        assert bold.tobytes() != bold_italic.tobytes()

    def test_bold_italic_differs_from_italic(self):
        """Test bold italic style differs from italic only."""
        italic = self._render("Italic")
        bold_italic = self._render("Bold Italic")
        assert italic.tobytes() != bold_italic.tobytes()

    def test_style_with_custom_font(self, temp_dir):
        """Test styles apply when a custom font file is used."""
        font_path = None
        for candidate in config.system_fonts:
            try:
                ImageFont.truetype(candidate, 20)
                # Resolve real path for fontconfig aliases like "arial.ttf"
                from PIL import ImageFont as _F
                font_path = _F.truetype(candidate, 20).path
                break
            except Exception:
                continue

        if font_path is None:
            pytest.skip("No system font available for custom font test")

        normal = self._render("Normal", font_path=font_path)
        bold = self._render("Bold", font_path=font_path)
        italic = self._render("Italic", font_path=font_path)
        assert normal.tobytes() != bold.tobytes()
        assert normal.tobytes() != italic.tobytes()

    def test_get_style_flags(self):
        """Test style flag extraction."""
        p = ImageProcessor()
        p.font_style = "Bold"
        assert p._get_style_flags() == (True, False)
        p.font_style = "Italic"
        assert p._get_style_flags() == (False, True)
        p.font_style = "Bold Italic"
        assert p._get_style_flags() == (True, True)
        p.font_style = "Normal"
        assert p._get_style_flags() == (False, False)

    def test_get_stroke_width(self):
        """Test stroke width for bold synthesis."""
        p = ImageProcessor()
        assert p._get_stroke_width(30, bold=False) == 0
        assert p._get_stroke_width(30, bold=True) >= 1
        assert p._get_stroke_width(200, bold=True) > p._get_stroke_width(30, bold=True)

    def test_all_styles_render_on_small_image(self):
        """Test all styles render without error on a small image."""
        for style in config.font_styles:
            result = self._render(style)
            assert result is not None, f"Failed for style: {style}"


# --- Integration Tests ---

class TestImageProcessing:
    """Integration tests for image processing."""

    def test_full_pipeline(self, sample_image, temp_dir):
        """Test full image processing pipeline."""
        processor = ImageProcessor(
            text="Watermark",
            color="#FF0000",
            font_size=24,
            position="bottom right",
            offset_up=10,
            offset_left=10,
        )

        # Process image
        result = processor.process_image_path(sample_image)
        assert result is not None

        # Save to output directory
        output_dir = os.path.join(temp_dir, "output")
        output_path = processor.get_output_path(sample_image, output_dir)
        result.save(output_path)

        # Verify file was created
        assert os.path.exists(output_path)

        # Verify we can load it back
        loaded = Image.open(output_path)
        assert loaded.size == result.size


# --- Edge Case Tests ---

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_text_returns_none(self, processor):
        """Test empty text returns None."""
        processor.text = ""
        img = Image.new("RGB", (100, 100))
        result = processor.apply_text(img)
        assert result is None

    def test_zero_size_image(self, processor):
        """Test processing zero-size image."""
        img = Image.new("RGB", (1, 1))
        # Should not crash
        result = processor.apply_text(img)
        assert result is not None

    def test_very_long_text(self, processor):
        """Test processing very long text."""
        processor.text = "A" * 1000
        img = Image.new("RGB", (200, 100))
        result = processor.apply_text(img)
        assert result is not None

    def test_all_positions(self, processor, sample_image):
        """Test all position options."""
        positions = ["top left", "top right", "bottom left", "bottom right", "center"]
        for pos in positions:
            processor.position = pos
            result = processor.process_image_path(sample_image)
            assert result is not None, f"Failed for position: {pos}"


# --- Orientation Tests ---

class TestOrientation:
    """Tests for visual orientation handling (EXIF-tagged rotation)."""

    def test_load_image_bakes_rotation(self, sideways_image):
        """load_image transposes pixels to the visual orientation."""
        img = load_image(sideways_image)
        assert img.size == (100, 200)
        # Raw top-right region becomes the visually bottom-right region after
        # a 90° CW rotation (JPEG-tolerant color check)
        r, g, b = img.getpixel((95, 195))
        assert r > 200 and g < 100 and b < 100

    def test_load_image_without_orientation_is_noop(self, sample_image):
        """load_image leaves images without an orientation tag untouched."""
        img = load_image(sample_image)
        assert img.size == (200, 100)

    def test_process_image_path_bakes_rotation(self, processor, sideways_image):
        """process_image_path works in the visual orientation."""
        result = processor.process_image_path(sideways_image)
        assert result is not None
        assert result.size == (100, 200)

    def test_saved_output_keeps_visual_orientation(
        self, processor, sideways_image, temp_dir
    ):
        """Full cycle: saved output shows the visual orientation without a tag."""
        result = processor.process_image_path(sideways_image)
        output_path = processor.get_output_path(sideways_image, temp_dir)
        result.save(output_path)

        reloaded = Image.open(output_path)
        assert reloaded.size == (100, 200)
        # No orientation tag that could re-rotate the baked image
        assert reloaded.getexif().get(274) in (None, 1)

# --- Font Selection Tests ---

class TestFontSelection:
    """Tests for the single-font rule and style variant probing."""

    @pytest.fixture
    def custom_font_file(self, temp_dir):
        """Copy a real system font into the temp dir as a custom font."""
        import glob
        import shutil

        candidates = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
        if not candidates:
            pytest.skip("No system ttf fonts available")
        font_path = os.path.join(temp_dir, "custom.ttf")
        shutil.copy(candidates[0], font_path)
        return font_path

    def test_custom_file_takes_precedence(self, custom_font_file):
        """Custom font file is the active font, family is ignored."""
        p = ImageProcessor(
            text="T", font_family="Nonexistent Family", font_path=custom_font_file
        )
        font = p.get_font(20)
        assert font is not None
        assert p._load_system_font(20) is None  # family unresolvable
        # The loaded font comes from the custom file, not the fallback chain
        assert font.path == custom_font_file

    def test_unknown_family_falls_back(self, processor):
        """Unknown family yields the fallback chain, never a crash."""
        processor.font_family = "Nonexistent Family 12345"
        processor.font_path = None
        font = processor.get_font(20)
        assert font is not None

    def test_no_family_uses_fallback_chain(self, processor):
        """No family set: the previous fallback chain still applies."""
        processor.font_family = None
        processor.font_path = None
        assert processor.get_font(20) is not None

    def test_style_variant_probed_before_plain_family(self, processor):
        """A styled variant name is tried before the plain family name."""
        processor.font_family = "Nonexistent Family 12345"
        processor.font_style = "Bold"
        # Must not raise; falls back to the chain
        assert processor.get_font(20) is not None

    def test_from_dict_roundtrip_font_family(self):
        """font_family survives the settings dict roundtrip."""
        settings = {"font_family": "Arial", "font_path": None, "font_style": "Italic"}
        p = ImageProcessor.from_dict(settings)
        assert p.font_family == "Arial"
        assert p.font_style == "Italic"
        assert p.to_dict()["font_family"] == "Arial"

    def test_custom_file_not_lost_on_family_reset(self, custom_font_file):
        """get_font keeps working when the custom file is set but family cleared."""
        p = ImageProcessor(
            text="T", font_family=None, font_path=custom_font_file
        )
        assert p.get_font(20) is not None
