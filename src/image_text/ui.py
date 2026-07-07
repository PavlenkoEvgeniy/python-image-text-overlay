"""Tkinter UI components for the Image Text Overlay application."""

import logging
import os
from typing import Optional, Callable

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk

from .config import config
from .processor import ImageProcessor
from .logging_config import get_logger

logger = get_logger(__name__)

# Check for drag and drop support
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False
    logger.warning("tkinterdnd2 not installed. Drag & drop disabled. Install with: pip install tkinterdnd2")


class TextOverlayUI:
    """Main UI class for the Image Text Overlay application."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the UI.

        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title(config.name)
        self.root.geometry(f"{config.window_width}x{config.window_height}")

        # State variables
        self.image_paths: list[str] = []
        self.current_index: int = 0
        self.original_image: Optional[Image.Image] = None
        self.preview_image: Optional[Image.Image] = None
        self.processed_images: list[Image.Image] = []
        self.rename_files = tk.BooleanVar(value=False)

        # Get application directory
        self.app_dir = self._get_app_dir()

        # Output directory
        self.output_dir_var = tk.StringVar(
            value=os.path.join(self.app_dir, config.default_output_dir)
        )

        # Image processor
        self.processor = ImageProcessor()

        # Create UI
        self._create_menu()
        self._create_widgets()

        # Setup drag and drop
        if HAS_DND:
            self._setup_drag_drop()
        else:
            self._show_dnd_warning()

        logger.info("UI initialized")

    def _get_app_dir(self) -> str:
        """Get application directory."""
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def _create_menu(self) -> None:
        """Create application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Images", command=self.load_images)
        file_menu.add_command(label="Clear List", command=self.clear_images)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_load_section(main_frame)
        self._create_navigation_section(main_frame)
        self._create_settings_section(main_frame)
        self._create_action_buttons(main_frame)
        self._create_preview_section(main_frame)

    def _create_load_section(self, parent: ttk.Frame) -> None:
        """Create image loading section."""
        load_frame = ttk.LabelFrame(parent, text="Image Loading", padding="10")
        load_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(load_frame, text="Select Images", command=self.load_images).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(load_frame, text="Clear List", command=self.clear_images).pack(
            side=tk.LEFT, padx=5
        )

        files_frame = ttk.Frame(load_frame)
        files_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        dnd_text = "Drag & drop files here or click button above" if HAS_DND else "Click 'Select Images' to load files"
        ttk.Label(files_frame, text=dnd_text).pack(side=tk.LEFT)

    def _create_navigation_section(self, parent: ttk.Frame) -> None:
        """Create navigation section."""
        nav_frame = ttk.LabelFrame(parent, text="Navigation", padding="10")
        nav_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(nav_frame, text="◄ Previous", command=self.prev_image).pack(
            side=tk.LEFT, padx=5
        )
        self.image_counter_label = ttk.Label(nav_frame, text="0 / 0")
        self.image_counter_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(nav_frame, text="Next ►", command=self.next_image).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(nav_frame, text="File name:").pack(side=tk.LEFT, padx=(20, 5))
        self.filename_label = ttk.Label(nav_frame, text="")
        self.filename_label.pack(side=tk.LEFT)

        ttk.Checkbutton(
            nav_frame,
            text="Overwrite original file",
            variable=self.rename_files,
        ).pack(side=tk.LEFT, padx=(20, 5))

    def _create_settings_section(self, parent: ttk.Frame) -> None:
        """Create text settings section."""
        settings_frame = ttk.LabelFrame(parent, text="Text Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Text input
        ttk.Label(settings_frame, text="Text:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(settings_frame, width=50)
        self.text_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=5)
        self.text_entry.insert(0, config.default_text)

        # Text color
        ttk.Label(settings_frame, text="Text color:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.color_preview = tk.Label(
            settings_frame, bg=config.default_color, width=5, height=1, relief=tk.RIDGE
        )
        self.color_preview.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(settings_frame, text="Choose color", command=self.choose_color).grid(
            row=1, column=2, sticky=tk.W, pady=5
        )

        # Text position
        ttk.Label(settings_frame, text="Position:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.position_var = tk.StringVar(value=config.default_position)
        position_menu = ttk.Combobox(
            settings_frame,
            textvariable=self.position_var,
            values=list(config.text_positions),
            width=20,
        )
        position_menu.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Offset up
        ttk.Label(settings_frame, text="Offset up (px):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.offset_up = ttk.Entry(settings_frame, width=10)
        self.offset_up.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        self.offset_up.insert(0, str(config.default_offset_up))

        # Offset left
        ttk.Label(settings_frame, text="Offset left (px):").grid(
            row=3, column=2, sticky=tk.W, pady=5, padx=(20, 0)
        )
        self.offset_left = ttk.Entry(settings_frame, width=10)
        self.offset_left.grid(row=3, column=3, sticky=tk.W, pady=5, padx=5)
        self.offset_left.insert(0, str(config.default_offset_left))

        # Font style
        ttk.Label(settings_frame, text="Font style:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.font_style_var = tk.StringVar(value=config.default_font_style)
        font_menu = ttk.Combobox(
            settings_frame,
            textvariable=self.font_style_var,
            values=list(config.font_styles),
            width=20,
        )
        font_menu.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # Font size
        ttk.Label(settings_frame, text="Font size:").grid(
            row=4, column=2, sticky=tk.W, pady=5, padx=(20, 0)
        )
        self.font_size_spin = ttk.Spinbox(
            settings_frame,
            from_=config.min_font_size,
            to=config.max_font_size,
            width=10,
        )
        self.font_size_spin.grid(row=4, column=3, sticky=tk.W, pady=5, padx=5)
        self.font_size_spin.set(str(config.default_font_size))

        # Font file
        ttk.Label(settings_frame, text="Font file:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.font_file_label = ttk.Label(settings_frame, text="System (default)")
        self.font_file_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        ttk.Button(settings_frame, text="Select font", command=self.choose_font).grid(
            row=5, column=3, sticky=tk.W, pady=5
        )

        # Output directory
        ttk.Label(settings_frame, text="Output Folder:").grid(
            row=6, column=0, sticky=tk.W, pady=5
        )
        self.output_dir_entry = ttk.Entry(
            settings_frame, textvariable=self.output_dir_var, width=30
        )
        self.output_dir_entry.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(settings_frame, text="Browse", command=self.browse_output_dir).grid(
            row=6, column=3, padx=5
        )

        # App location info
        ttk.Label(
            settings_frame, text=f"App location: {self.app_dir}", font=("Arial", 8)
        ).grid(row=7, column=0, columnspan=4, sticky=tk.W, pady=(2, 5))

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create action buttons."""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Apply to All", command=self.apply_to_all).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="Preview", command=self.preview_text).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="Save Current", command=self.save_current_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="Save All", command=self.save_all_images).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="Clear", command=self.clear_all).pack(
            side=tk.LEFT, padx=5
        )

    def _create_preview_section(self, parent: ttk.Frame) -> None:
        """Create preview section."""
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(preview_frame, bg="gray", width=600, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def _show_dnd_warning(self) -> None:
        """Show warning about missing drag and drop support."""
        messagebox.showwarning(
            "Drag & Drop Not Available",
            "Drag & drop support requires 'tkinterdnd2' library.\n\n"
            "Install it with: pip install tkinterdnd2\n\n"
            "You can still use 'Select Images' button to load files.",
        )

    def _setup_drag_drop(self) -> None:
        """Setup drag and drop handlers."""
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.drop_files)

            self.preview_canvas.drop_target_register(DND_FILES)
            self.preview_canvas.dnd_bind("<<Drop>>", self.drop_files)
        except Exception as e:
            logger.error(f"Error setting up drag & drop: {e}")

    def _get_current_settings(self) -> dict:
        """Get current settings from UI.

        Returns:
            Dictionary with current settings.
        """
        try:
            font_size = int(self.font_size_spin.get())
        except ValueError:
            font_size = config.default_font_size

        try:
            offset_up = int(self.offset_up.get())
        except ValueError:
            offset_up = config.default_offset_up

        try:
            offset_left = int(self.offset_left.get())
        except ValueError:
            offset_left = config.default_offset_left

        return {
            "text": self.text_entry.get(),
            "color": self.color_preview.cget("bg"),
            "font_path": getattr(self, "font_path", None),
            "font_size": font_size,
            "font_style": self.font_style_var.get(),
            "position": self.position_var.get(),
            "offset_up": offset_up,
            "offset_left": offset_left,
        }

    def _update_processor(self) -> None:
        """Update processor with current UI settings."""
        settings = self._get_current_settings()
        self.processor = ImageProcessor.from_dict(settings)

    # --- Public Methods ---

    def load_images(self) -> None:
        """Load images via file dialog."""
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif")],
        )

        if file_paths:
            self.add_files(list(file_paths))

    def add_files(self, file_paths: list[str]) -> None:
        """Add files to the image list.

        Args:
            file_paths: List of file paths to add.
        """
        added = 0

        for path in file_paths:
            if os.path.exists(path) and path.lower().endswith(config.valid_extensions):
                if path not in self.image_paths:
                    self.image_paths.append(path)
                    added += 1

        if added > 0:
            messagebox.showinfo("Success", f"Added {added} images")
            self.current_index = 0
            self.load_current_image()
            self.update_file_list()
        else:
            messagebox.showwarning("Warning", "No valid images found")

    def drop_files(self, event) -> None:
        """Handle dropped files event."""
        if HAS_DND:
            files = self.root.tk.splitlist(event.data)
            self.add_files(files)

    def load_current_image(self) -> None:
        """Load and display current image."""
        if self.image_paths and self.current_index < len(self.image_paths):
            try:
                image_path = self.image_paths[self.current_index]
                self.original_image = Image.open(image_path)
                self.filename_label.config(text=os.path.basename(image_path))
                self.show_preview()
                self.update_counter()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def update_counter(self) -> None:
        """Update image counter display."""
        total = len(self.image_paths)
        current = self.current_index + 1 if total > 0 else 0
        self.image_counter_label.config(text=f"{current} / {total}")

    def update_file_list(self) -> None:
        """Update file list info."""
        total = len(self.image_paths)
        if total > 0:
            self.image_counter_label.config(text=f"1 / {total}")
            self.filename_label.config(text=os.path.basename(self.image_paths[0]))
        else:
            self.image_counter_label.config(text="0 / 0")
            self.filename_label.config(text="")

    def next_image(self) -> None:
        """Go to next image."""
        if self.image_paths and self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_current_image()

    def prev_image(self) -> None:
        """Go to previous image."""
        if self.image_paths and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def clear_images(self) -> None:
        """Clear image list."""
        self.image_paths.clear()
        self.processed_images.clear()
        self.current_index = 0
        self.original_image = None
        self.preview_image = None
        self.filename_label.config(text="")
        self.image_counter_label.config(text="0 / 0")
        self.preview_canvas.delete("all")

    def choose_color(self) -> None:
        """Open color picker dialog."""
        color = colorchooser.askcolor(title="Select text color")
        if color[0]:
            self.color_preview.config(bg=color[1])

    def choose_font(self) -> None:
        """Open font file dialog."""
        file_path = filedialog.askopenfilename(
            title="Select font file",
            filetypes=[("Fonts", "*.ttf *.otf")],
        )
        if file_path:
            self.font_path = file_path
            self.font_file_label.config(text=os.path.basename(file_path))

    def browse_output_dir(self) -> None:
        """Browse for output directory."""
        folder = filedialog.askdirectory(
            title="Select Output Folder", initialdir=self.app_dir
        )
        if folder:
            self.output_dir_var.set(folder)

    def preview_text(self) -> None:
        """Preview text overlay on current image."""
        if self.original_image is None:
            messagebox.showwarning("Error", "Please load an image!")
            return

        self._update_processor()
        result = self.processor.apply_text(self.original_image)

        if result:
            self.preview_image = result
            self.show_preview(result)

    def apply_to_all(self) -> None:
        """Apply text to all loaded images."""
        if not self.image_paths:
            messagebox.showwarning("Error", "No images loaded!")
            return

        text = self.text_entry.get()
        if not text:
            messagebox.showwarning("Error", "Please enter text!")
            return

        self._update_processor()
        self.processed_images.clear()

        for path in self.image_paths:
            try:
                img = Image.open(path)
                result = self.processor.apply_text(img)
                if result:
                    self.processed_images.append(result)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to process {os.path.basename(path)}: {e}"
                )
                return

        if self.processed_images:
            self.preview_image = self.processed_images[0]
            self.show_preview(self.preview_image)
            messagebox.showinfo(
                "Success", f"Processed {len(self.processed_images)} images"
            )

    def show_preview(self, img: Optional[Image.Image] = None) -> None:
        """Show image preview on canvas.

        Args:
            img: PIL Image to display. Uses original if None.
        """
        if img is None and self.original_image is not None:
            img = self.original_image

        if img is None:
            return

        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 600
            canvas_height = 400

        img_copy = img.copy()
        img_copy.thumbnail(
            (canvas_width - 10, canvas_height - 10), Image.Resampling.LANCZOS
        )

        photo = ImageTk.PhotoImage(img_copy)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_width // 2, canvas_height // 2, image=photo, anchor=tk.CENTER
        )
        self.preview_canvas.image = photo

    def get_output_path(self, original_path: str) -> str:
        """Get output path for processed image."""
        output_dir = self.output_dir_var.get().strip()
        return self.processor.get_output_path(original_path, output_dir)

    def save_current_image(self) -> None:
        """Save current preview image."""
        if self.preview_image is None:
            messagebox.showwarning("Error", "Please preview first!")
            return

        original_path = self.image_paths[self.current_index]

        if self.rename_files.get():
            file_path = original_path

            if os.path.exists(file_path):
                if not messagebox.askyesno(
                    "Confirm Overwrite",
                    f"File '{os.path.basename(file_path)}' already exists. Do you want to overwrite it?",
                ):
                    return

            self.preview_image.save(file_path)
            messagebox.showinfo("Success", f"Image overwritten: {file_path}")
        else:
            # Save to output folder
            output_path = self.get_output_path(original_path)
            self.preview_image.save(output_path)
            messagebox.showinfo("Success", f"Image saved:\n{output_path}")

    def save_all_images(self) -> None:
        """Save all processed images."""
        if not self.processed_images:
            messagebox.showwarning("Error", "Please apply text to all images first!")
            return

        if self.rename_files.get():
            # Overwrite originals
            saved = 0
            for i, img in enumerate(self.processed_images):
                original_path = self.image_paths[i]

                if os.path.exists(original_path):
                    if not messagebox.askyesno(
                        "Confirm Overwrite",
                        f"File '{os.path.basename(original_path)}' exists. Overwrite all files?",
                    ):
                        return
                    break

            for i, img in enumerate(self.processed_images):
                original_path = self.image_paths[i]
                img.save(original_path)
                saved += 1

            messagebox.showinfo("Success", f"Overwritten {saved} original images")
        else:
            # Save to output folder
            saved = 0
            output_paths = []

            for i, img in enumerate(self.processed_images):
                original_path = self.image_paths[i]
                output_path = self.get_output_path(original_path)
                img.save(output_path)
                output_paths.append(output_path)
                saved += 1

            output_dir = os.path.dirname(output_paths[0]) if output_paths else ""
            messagebox.showinfo("Success", f"Saved {saved} images to:\n{output_dir}")

    def clear_all(self) -> None:
        """Clear all data and reset UI."""
        self.clear_images()

        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, config.default_text)
        self.offset_up.delete(0, tk.END)
        self.offset_up.insert(0, str(config.default_offset_up))
        self.offset_left.delete(0, tk.END)
        self.offset_left.insert(0, str(config.default_offset_left))
        self.color_preview.config(bg=config.default_color)
        self.font_path = None
        self.font_file_label.config(text="System (default)")
        self.position_var.set(config.default_position)
        self.font_style_var.set(config.default_font_style)
        self.font_size_spin.set(str(config.default_font_size))
        self.rename_files.set(False)
        self.output_dir_var.set(
            os.path.join(self.app_dir, config.default_output_dir)
        )

    def show_about(self) -> None:
        """Show about dialog."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("550x450")
        about_window.resizable(False, False)

        about_window.transient(self.root)
        about_window.grab_set()

        main_frame = ttk.Frame(about_window, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text=config.name, font=("Arial", 20, "bold")
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame, text=f"Version {config.version}", font=("Arial", 11)
        ).pack(pady=(0, 15))

        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        info_text = f"""Program for adding text overlay to images

Features:
• Batch processing support
• Drag & drop files
• Font and color customization
• Text position selection
• Preview functionality"""

        ttk.Label(main_frame, text=info_text, justify=tk.LEFT, font=("Arial", 10)).pack(
            anchor=tk.W, pady=10
        )

        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=15)

        copyright_text = f"""Copyright© 2026
License: Freeware
Author: {__import__('image_text').__author__}
Email: {__import__('image_text').__email__}"""

        ttk.Label(
            main_frame,
            text=copyright_text,
            justify=tk.LEFT,
            font=("Arial", 10),
            foreground="#333333",
        ).pack(anchor=tk.W, pady=5)


# Import sys for frozen check
import sys