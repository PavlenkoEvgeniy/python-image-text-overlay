"""Main entry point for Image Text Overlay application."""

import sys
import logging

# Check for drag and drop support before importing UI
try:
    from tkinterdnd2 import TkinterDnD
    TkinterDnD_available = True
except ImportError:
    TkinterDnD_available = False


def main() -> None:
    """Main entry point."""
    # Setup logging
    from image_text.logging_config import setup_logging
    setup_logging(level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Starting Image Text Overlay application")

    # Import here to ensure logging is configured
    import tkinter as tk
    from image_text.ui import TextOverlayUI, HAS_DND

    # Create root window
    if HAS_DND and TkinterDnD_available:
        logger.info("Using TkinterDnD for drag and drop support")
        root = TkinterDnD.Tk()
    else:
        logger.info("Using standard Tk")
        root = tk.Tk()

    # Create and run application
    app = TextOverlayUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()