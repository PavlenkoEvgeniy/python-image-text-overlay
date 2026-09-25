# Image Text Overlay

Desktop tool for overlaying text on images before saving. This context covers the
vocabulary of text styling, previewing and saving.

## Language

### Text styling

**Font file**:
A user-selected `.ttf`/`.otf` file that supplies the glyph shapes.
_Avoid_: custom font, font (alone — ambiguous with Font style)

**Font style**:
The visual variant (Normal, Bold, Italic, Bold Italic) applied on top of the Font file.
A Font style must always visibly affect both preview and saved output.
_Avoid_: font type, font family

**Glyph coverage**:
The requirement that the active font contains visible glyphs for the text being
overlaid. A font that renders no visible glyphs is rejected in favor of the next
font in the fallback chain.
_Avoid_: font support, missing symbols

### Preview and saving

**Live preview**:
The preview area that always reflects the current settings, re-rendered automatically
after any change and immediately after loading an image.
_Avoid_: auto preview

**Original image**:
The currently loaded, unmodified source image the text is overlaid on.
_Avoid_: current image, source picture

**Processed image**:
An image with the text overlay already applied, kept in memory for batch saving.
_Avoid_: preview image (reserved for what the preview area displays)

### Persistence

**Saved settings**:
The user's preferences persisted between sessions: text content and styling, positioning, Font file, output folder and the overwrite flag.
The loaded image path and window geometry are deliberately not part of Saved settings.
_Avoid_: app state, session state, user preferences

**Settings file**:
The document in the user's platform config directory that holds the Saved settings between sessions.
_Avoid_: config file, session file

**Field fallback**:
The rule that a saved value failing validation is replaced by its default while the remaining Saved settings load as-is.
A corrupt Settings file as a whole falls back entirely to defaults, silently.
_Avoid_: soft validation, graceful degradation

**Reset settings**:
Returning the Saved settings to their defaults in both the interface and the Settings file, after user confirmation.
_Avoid_: clear all (that empties the working images too), restore factory defaults
