"""Tests for the Saved settings persistence (settings_store)."""

import json

from image_text import settings_store
from image_text.config import config


FULL_SETTINGS = {
    "text": "Hello",
    "color": "#123456",
    "font_family": "Arial",
    "font_path": None,
    "font_size": 55,
    "font_style": "Bold",
    "position": "center",
    "offset_up": 5,
    "offset_left": 7,
    "output_dir": "/tmp/out",
    "overwrite": True,
}


# --- Round trip ---


class TestRoundTrip:
    """Test saving and loading a full settings snapshot."""

    def test_round_trip(self, tmp_path):
        """Saved settings survive a save/load cycle unchanged."""
        path = str(tmp_path / "settings.json")

        assert settings_store.save_settings(FULL_SETTINGS, path=path)
        assert settings_store.load_settings(path=path) == FULL_SETTINGS

    def test_file_is_versioned_json(self, tmp_path):
        """The file holds {"version": 1, "settings": {...}}."""
        path = tmp_path / "settings.json"
        settings_store.save_settings(FULL_SETTINGS, path=str(path))

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["version"] == settings_store.SETTINGS_VERSION
        assert payload["settings"]["text"] == "Hello"


# --- Load failure modes ---


class TestLoadFailureModes:
    """Test that unreadable files silently fall back to defaults."""

    def test_missing_file_returns_none(self, tmp_path):
        """No settings file means defaults."""
        assert settings_store.load_settings(path=str(tmp_path / "nope.json")) is None

    def test_corrupt_file_returns_none(self, tmp_path):
        """A file with broken JSON is ignored."""
        path = tmp_path / "settings.json"
        path.write_text("{not json", encoding="utf-8")

        assert settings_store.load_settings(path=str(path)) is None

    def test_non_object_json_returns_none(self, tmp_path):
        """A file holding a JSON list instead of an object is ignored."""
        path = tmp_path / "settings.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")

        assert settings_store.load_settings(path=str(path)) is None

    def test_wrong_version_returns_none(self, tmp_path):
        """A file from an unsupported format version is ignored."""
        path = tmp_path / "settings.json"
        payload = {"version": settings_store.SETTINGS_VERSION + 1, "settings": {}}
        path.write_text(json.dumps(payload), encoding="utf-8")

        assert settings_store.load_settings(path=str(path)) is None

    def test_missing_settings_object_returns_none(self, tmp_path):
        """A versioned file without a settings object is ignored."""
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"version": 1}), encoding="utf-8")

        assert settings_store.load_settings(path=str(path)) is None

    def test_unknown_keys_ignored(self, tmp_path):
        """Keys the current build does not know are dropped, not fatal."""
        path = tmp_path / "settings.json"
        payload = {"version": 1, "settings": {"text": "hi", "mystery": 123}}
        path.write_text(json.dumps(payload), encoding="utf-8")

        loaded = settings_store.load_settings(path=str(path))

        assert loaded is not None
        assert "mystery" not in loaded
        assert loaded["text"] == "hi"


# --- Field fallback ---


class TestFieldFallback:
    """Test per-field validation against the AppConfig rules."""

    def test_font_size_clamped_to_range(self):
        """Out-of-range font sizes are clamped, not dropped."""
        settings = settings_store.validate_settings({"font_size": 9999})
        assert settings["font_size"] == config.max_font_size

        settings = settings_store.validate_settings({"font_size": 1})
        assert settings["font_size"] == config.min_font_size

    def test_font_size_wrong_type_falls_back(self):
        """A non-integer font size falls back to the default."""
        for bad in ("40", 4.5, None, True):
            settings = settings_store.validate_settings({"font_size": bad})
            assert settings["font_size"] == config.default_font_size

    def test_invalid_enums_fall_back(self):
        """Unknown position and font style fall back to defaults."""
        settings = settings_store.validate_settings(
            {"position": "middle", "font_style": "Huge"}
        )
        assert settings["position"] == config.default_position
        assert settings["font_style"] == config.default_font_style

    def test_invalid_color_falls_back(self):
        """A non-hex color falls back to the default."""
        for bad in ("chartreuse", "#12345", "#GGGGGG", 123, None):
            settings = settings_store.validate_settings({"color": bad})
            assert settings["color"] == config.default_color

    def test_wrong_type_offsets_fall_back(self):
        """Non-integer offsets fall back to defaults."""
        settings = settings_store.validate_settings({"offset_up": "20", "offset_left": 1.5})
        assert settings["offset_up"] == config.default_offset_up
        assert settings["offset_left"] == config.default_offset_left

    def test_wrong_type_text_and_overwrite_fall_back(self):
        """Non-string text and non-bool overwrite fall back to defaults."""
        settings = settings_store.validate_settings({"text": 5, "overwrite": "yes"})
        assert settings["text"] == config.default_text
        assert settings["overwrite"] is False

    def test_wrong_type_font_path_becomes_none(self):
        """A non-string font path means 'no custom font'."""
        settings = settings_store.validate_settings({"font_path": 42})
        assert settings["font_path"] is None

    def test_result_always_complete(self):
        """Validation of an empty mapping yields every known key."""
        settings = settings_store.validate_settings({})

        assert set(settings) == set(FULL_SETTINGS)
        assert settings["text"] == config.default_text
        assert settings["color"] == config.default_color
        assert settings["font_family"] == config.default_font_family
        assert settings["font_path"] is None
        assert settings["font_size"] == config.default_font_size
        assert settings["font_style"] == config.default_font_style
        assert settings["position"] == config.default_position
        assert settings["offset_up"] == config.default_offset_up
        assert settings["offset_left"] == config.default_offset_left
        assert settings["output_dir"] == config.default_output_dir
        assert settings["overwrite"] is False

    def test_invalid_field_does_not_poison_others(self):
        """One bad field leaves the remaining saved values intact."""
        settings = settings_store.validate_settings(
            {"text": "Kept", "font_size": "broken", "color": "#ABCDEF"}
        )
        assert settings["text"] == "Kept"
        assert settings["font_size"] == config.default_font_size
        assert settings["color"] == "#ABCDEF"


# --- Save and clear ---


class TestSaveAndClear:
    """Test atomic saving and resetting."""

    def test_clear_missing_file_is_success(self, tmp_path):
        """Resetting without a settings file is not an error."""
        assert settings_store.clear_settings(path=str(tmp_path / "nope.json"))

    def test_clear_removes_file(self, tmp_path):
        """Resetting deletes the settings file."""
        path = tmp_path / "settings.json"
        settings_store.save_settings({}, path=str(path))
        assert path.exists()

        assert settings_store.clear_settings(path=str(path))
        assert not path.exists()

    def test_save_to_missing_directory_creates_it(self, tmp_path):
        """Saving creates the settings directory if needed."""
        path = tmp_path / "nested" / "dir" / "settings.json"

        assert settings_store.save_settings(FULL_SETTINGS, path=str(path))
        assert settings_store.load_settings(path=str(path)) == FULL_SETTINGS

    def test_load_after_clear_returns_none(self, tmp_path):
        """After a reset the next launch starts from defaults."""
        path = tmp_path / "settings.json"
        settings_store.save_settings(FULL_SETTINGS, path=str(path))
        settings_store.clear_settings(path=str(path))

        assert settings_store.load_settings(path=str(path)) is None