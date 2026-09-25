"""Persistence of Saved settings between sessions.

The Saved settings (see CONTEXT.md) are stored as versioned JSON in the
user's platform config directory and loaded back on the next launch.
Loading is forgiving: a corrupt file falls back silently to defaults and
invalid single fields fall back to their own defaults (Field fallback).
"""

import json
import os
import re
import sys
import tempfile
from typing import Any, Optional

from .config import config
from .logging_config import get_logger

logger = get_logger(__name__)

SETTINGS_VERSION = 1
SETTINGS_DIR_NAME = "image-text"
SETTINGS_FILENAME = "settings.json"

_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def get_settings_path() -> str:
    """Get the platform-specific path of the Settings file."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    return os.path.join(base, SETTINGS_DIR_NAME, SETTINGS_FILENAME)


def validate_settings(raw: dict) -> dict:
    """Validate saved values one by one; invalid ones fall back to defaults.

    Args:
        raw: Raw settings mapping as read from the Settings file.

    Returns:
        A complete settings dict with every known key holding a safe value.
    """
    settings: dict[str, Any] = {}

    text = raw.get("text")
    settings["text"] = text if isinstance(text, str) else config.default_text

    color = raw.get("color")
    settings["color"] = (
        color
        if isinstance(color, str) and _HEX_COLOR.fullmatch(color)
        else config.default_color
    )

    family = raw.get("font_family")
    if family is None and "font_family" not in raw:
        settings["font_family"] = config.default_font_family
    elif family is None or isinstance(family, str):
        # None is meaningful: a custom font file is in use
        settings["font_family"] = family
    else:
        settings["font_family"] = config.default_font_family

    font_path = raw.get("font_path")
    settings["font_path"] = (
        font_path if font_path is None or isinstance(font_path, str) else None
    )

    font_size = raw.get("font_size")
    if isinstance(font_size, int) and not isinstance(font_size, bool):
        settings["font_size"] = min(
            max(font_size, config.min_font_size), config.max_font_size
        )
    else:
        settings["font_size"] = config.default_font_size

    font_style = raw.get("font_style")
    settings["font_style"] = (
        font_style if font_style in config.font_styles else config.default_font_style
    )

    position = raw.get("position")
    settings["position"] = (
        position if position in config.text_positions else config.default_position
    )

    for key, default in (
        ("offset_up", config.default_offset_up),
        ("offset_left", config.default_offset_left),
    ):
        value = raw.get(key)
        settings[key] = (
            value if isinstance(value, int) and not isinstance(value, bool) else default
        )

    output_dir = raw.get("output_dir")
    settings["output_dir"] = (
        output_dir if isinstance(output_dir, str) else config.default_output_dir
    )

    overwrite = raw.get("overwrite")
    settings["overwrite"] = overwrite if isinstance(overwrite, bool) else False

    return settings


def save_settings(settings: dict, path: Optional[str] = None) -> bool:
    """Save settings atomically to the Settings file.

    Args:
        settings: Complete settings mapping to persist.
        path: Target path; defaults to the platform settings path.

    Returns:
        True on success, False if writing failed (already logged).
    """
    target = path or get_settings_path()
    payload = {"version": SETTINGS_VERSION, "settings": settings}
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix=".settings-", suffix=".tmp", dir=os.path.dirname(target)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, target)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise
        return True
    except Exception as e:
        logger.warning(f"Failed to save settings to {target}: {e}")
        return False


def load_settings(path: Optional[str] = None) -> Optional[dict]:
    """Load and validate Saved settings.

    Args:
        path: Source path; defaults to the platform settings path.

    Returns:
        A validated settings dict, or None when defaults should be used.
    """
    target = path or get_settings_path()
    try:
        with open(target, encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        logger.warning(f"Ignoring corrupt settings file {target}: {e}")
        return None

    if not isinstance(payload, dict) or payload.get("version") != SETTINGS_VERSION:
        logger.warning(f"Ignoring settings file {target}: unsupported format")
        return None

    raw = payload.get("settings")
    if not isinstance(raw, dict):
        logger.warning(f"Ignoring settings file {target}: no settings object")
        return None

    return validate_settings(raw)


def clear_settings(path: Optional[str] = None) -> bool:
    """Delete the Settings file (Reset settings).

    Args:
        path: Target path; defaults to the platform settings path.

    Returns:
        True when the file is gone (or was never there), False on failure.
    """
    target = path or get_settings_path()
    try:
        os.remove(target)
        return True
    except FileNotFoundError:
        return True
    except OSError as e:
        logger.warning(f"Failed to delete settings file {target}: {e}")
        return False