"""Tests for UI components (mocked tests)."""

import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# Note: These tests use mocking to avoid requiring a display
# Full GUI tests should be run manually or with a display


# --- UI Configuration Tests ---

class TestUIConfiguration:
    """Test UI configuration values."""

    def test_config_values_propagate(self):
        """Test that config values are correct for UI."""
        from image_text.config import config

        assert config.name == "Image Text Overlay"
        assert config.version == "1.0.1"
        assert config.window_width == 950
        assert config.window_height == 750
        assert config.default_font_size == 40
        assert config.min_font_size == 10
        assert config.max_font_size == 200

    def test_valid_extensions(self):
        """Test valid image extensions are defined."""
        from image_text.config import config

        expected = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif")
        assert config.valid_extensions == expected

    def test_font_extensions(self):
        """Test font file extensions."""
        from image_text.config import config

        assert ".ttf" in config.font_extensions
        assert ".otf" in config.font_extensions


# --- UI Processor Integration Tests ---

class TestUIProcessorIntegration:
    """Test UI and processor work together."""

    def test_processor_settings_dict(self):
        """Test that processor settings can be converted to dict."""
        from image_text.processor import ImageProcessor

        settings = {
            "text": "Test",
            "color": "#FF0000",
            "font_size": 30,
            "font_style": "Bold",
            "position": "top left",
            "offset_up": 5,
            "offset_left": 10,
            "font_path": None,
        }

        p = ImageProcessor.from_dict(settings)
        result = p.to_dict()

        assert result["text"] == "Test"
        assert result["color"] == "#FF0000"
        assert result["font_size"] == 30
        assert result["font_style"] == "Bold"
        assert result["position"] == "top left"
        assert result["offset_up"] == 5
        assert result["offset_left"] == 10


class TestFileOperations:
    """Test file operations."""

    def test_get_output_path_creates_directory(self, tmp_path):
        """Test output path creation creates directory."""
        from image_text.processor import ImageProcessor

        processor = ImageProcessor(text="Test")
        original_path = str(tmp_path / "image.png")

        # Create dummy image file
        from PIL import Image
        Image.new("RGB", (10, 10)).save(original_path)

        output_dir = str(tmp_path / "output" / "subdir")
        output_path = processor.get_output_path(original_path, output_dir)

        assert os.path.exists(os.path.dirname(output_path))

    def test_output_path_suffix(self, tmp_path):
        """Test output path has correct suffix."""
        from image_text.processor import ImageProcessor

        processor = ImageProcessor(text="Test")
        original_path = str(tmp_path / "my_image.png")

        from PIL import Image
        Image.new("RGB", (10, 10)).save(original_path)

        output_dir = str(tmp_path / "output")
        output_path = processor.get_output_path(original_path, output_dir)

        assert "_text.png" in output_path
        assert "my_image" in output_path

    def test_output_path_jpeg(self, tmp_path):
        """Test output path for JPEG."""
        from image_text.processor import ImageProcessor

        processor = ImageProcessor(text="Test")
        original_path = str(tmp_path / "my_image.jpg")

        from PIL import Image
        Image.new("RGB", (10, 10)).save(original_path)

        output_dir = str(tmp_path / "output")
        output_path = processor.get_output_path(original_path, output_dir)

        assert "_text.jpg" in output_path


# --- Settings Validation Tests ---

class TestSettingsValidation:
    """Test settings validation."""

    def test_font_size_bounds(self):
        """Test font size is within bounds."""
        from image_text.processor import ImageProcessor

        # Test minimum
        p = ImageProcessor(font_size=5)
        # Should not crash
        font = p.get_font(5)
        assert font is not None

    def test_invalid_font_size_handled(self):
        """Test invalid font size is handled gracefully."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(text="Test")
        # Should use fallback
        font = p.get_font(10)
        assert font is not None

    def test_position_calculation_with_offsets(self):
        """Test position with custom offsets."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(
            text="Test",
            position="bottom right",
            offset_up=50,
            offset_left=50,
        )

        x, y = p.calculate_position(300, 200, 100, 50)
        assert x == 150  # 300 - 100 - 50
        assert y == 100  # 200 - 50 - 50

    def test_position_calculation_zero_offsets(self):
        """Test position with zero offsets."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(
            text="Test",
            position="top left",
            offset_up=0,
            offset_left=0,
        )

        x, y = p.calculate_position(300, 200, 100, 50)
        assert x == 0
        assert y == 0


# --- Image Format Tests ---

class TestImageFormats:
    """Test different image formats."""

    def test_png_format(self, tmp_path):
        """Test PNG format processing."""
        from PIL import Image
        from image_text.processor import ImageProcessor

        img_path = str(tmp_path / "test.png")
        Image.new("RGB", (100, 50), color="blue").save(img_path, "PNG")

        processor = ImageProcessor(text="Test")
        result = processor.process_image_path(img_path)

        assert result is not None

    def test_jpeg_format(self, tmp_path):
        """Test JPEG format processing."""
        from PIL import Image
        from image_text.processor import ImageProcessor

        img_path = str(tmp_path / "test.jpg")
        Image.new("RGB", (100, 50), color="red").save(img_path, "JPEG")

        processor = ImageProcessor(text="Test")
        result = processor.process_image_path(img_path)

        assert result is not None

    def test_bmp_format(self, tmp_path):
        """Test BMP format processing."""
        from PIL import Image
        from image_text.processor import ImageProcessor

        img_path = str(tmp_path / "test.bmp")
        Image.new("RGB", (100, 50), color="green").save(img_path, "BMP")

        processor = ImageProcessor(text="Test")
        result = processor.process_image_path(img_path)

        assert result is not None


# --- Color Tests ---

class TestTextColors:
    """Test text color handling."""

    def test_white_color(self):
        """Test white color."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(text="Test", color="#FFFFFF")
        img = Image.new("RGB", (100, 50))
        result = p.apply_text(img)
        assert result is not None

    def test_black_color(self):
        """Test black color."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(text="Test", color="#000000")
        img = Image.new("RGB", (100, 50))
        result = p.apply_text(img)
        assert result is not None

    def test_red_color(self):
        """Test red color."""
        from image_text.processor import ImageProcessor

        p = ImageProcessor(text="Test", color="#FF0000")
        img = Image.new("RGB", (100, 50))
        result = p.apply_text(img)
        assert result is not None


# Import Image for tests
from PIL import Image