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
