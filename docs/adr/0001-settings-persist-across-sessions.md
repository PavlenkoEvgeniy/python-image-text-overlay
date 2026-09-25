# Persist user settings across sessions

The app previously kept all state in widgets, so every launch started from defaults.
We decided to persist the Saved settings (the 9 styling/position fields, output folder
and the overwrite flag — not the image path, not window geometry) by autosaving with a
short debounce on every change, plus a synchronous flush when the window closes.

The Settings file lives in the platform config directory (no new dependencies) as
`{"version": 1, "settings": {...}}`; unknown keys are ignored and the version field
lets future builds migrate instead of silently discarding user settings — important
because PyInstaller binaries for 3 OSes stay in use long after newer releases.

Loading is deliberately forgiving: a corrupt file falls back silently to defaults,
and a valid file with out-of-range values gets per-field fallback (clamped by the
`AppConfig` rules). A "Reset Settings" menu item (with confirmation) returns both the
UI and the file to defaults.

## Considered Options

- Save on app close only — rejected: a crash loses everything since launch.
- Save the last image path / reopen it on start — rejected: a stale path (renamed
  file, unplugged drive) becomes a startup failure mode for no real gain.
- Flat unversioned JSON — rejected: binaries distributed to users make old/new
  version coexistence likely; the version field costs one line.
- Strict validation with an error dialog — rejected: settings are a non-critical
  subsystem; a dialog on every launch annoys more than silent defaults hurt.