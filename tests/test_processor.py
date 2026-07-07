"""Tests for image_text package."""

import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from PIL import Image

from image_text.config import AppConfig, config
from image_text.processor import ImageProcessor


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
        assert cfg.version == "1.0.2"
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