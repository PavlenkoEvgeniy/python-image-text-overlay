"""Application configuration and constants."""

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass
class AppConfig:
    """Application configuration."""

    name: str = "Image Text Overlay"
    version: str = "1.0.2"
    window_width: int = 950
    window_height: int = 750

    # Supported image formats
    valid_extensions: Tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif")

    # Supported font formats
    font_extensions: Tuple[str, ...] = (".ttf", ".otf")

    # Default values
    default_text: str = "Your text"
    default_color: str = "#FFFFFF"
    default_font_size: int = 40
    default_position: str = "bottom right"
    default_offset_up: int = 20
    default_offset_left: int = 20
    default_font_style: str = "Normal"

    # Font styles
    font_styles: Tuple[str, ...] = ("Normal", "Bold", "Italic", "Bold Italic")

    # Text positions
    text_positions: Tuple[str, ...] = ("top left", "top right", "bottom left", "bottom right", "center")

    # Font size range
    min_font_size: int = 10
    max_font_size: int = 200

    # Fallback system fonts
    system_fonts: Tuple[str, ...] = (
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "FreeSans.ttf",
    )

    @property
    def default_output_dir(self) -> str:
        """Get default output directory path."""
        return "processed_images"


def get_app_dir() -> str:
    """Get the application directory (works for both script and frozen executable)."""
    import sys
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource (works for dev and for PyInstaller).

    Args:
        relative_path: Relative path to resource.

    Returns:
        Absolute path to resource.
    """
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Global config instance
config = AppConfig()