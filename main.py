import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import sys

# Попытка импорта tkinterdnd2
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("WARNING: tkinterdnd2 not installed. Drag & drop disabled.")
    print("Install with: pip install tkinterdnd2")


# Fix для замороженных приложений
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_app_dir():
    """Get the application directory, works for both script and frozen executable"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a frozen executable (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # If the application is run as a script
        return os.path.dirname(os.path.abspath(__file__))


class TextOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Text Overlay")
        self.root.geometry("950x750")

        # Variables
        self.image_paths = []
        self.current_index = 0
        self.original_image = None
        self.preview_image = None
        self.font_path = None
        self.text_color = "#FFFFFF"
        self.font_size = 40
        self.processed_images = []
        self.rename_files = tk.BooleanVar(value=False)  # Variable for rename checkbox

        # Get the application directory
        self.app_dir = get_app_dir()

        # Output directory variable - default to processed_images in app directory
        self.output_dir_var = tk.StringVar(value=os.path.join(self.app_dir, "processed_images"))

        # Create menu
        self.create_menu()

        # Create interface
        self.create_widgets()

        # Setup drag & drop if available
        if HAS_DND:
            self.setup_drag_drop()
        else:
            # Show info about missing DND
            self.show_dnd_warning()

    def show_dnd_warning(self):
        """Show warning about missing DND support"""
        messagebox.showwarning(
            "Drag & Drop Not Available",
            "Drag & drop support requires 'tkinterdnd2' library.\n\n"
            "Install it with: pip install tkinterdnd2\n\n"
            "You can still use 'Select Images' button to load files."
        )

    def create_menu(self):
        """Create program menu"""
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

    def show_about(self):
        """Show about information"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("550x450")
        about_window.resizable(False, False)

        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()

        # Main frame with padding
        main_frame = ttk.Frame(about_window, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Image Text Overlay",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(0, 5))

        # Version
        version_label = ttk.Label(
            main_frame,
            text="Version 1.0.0",
            font=("Arial", 11)
        )
        version_label.pack(pady=(0, 15))

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Information
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)

        info_text = """Program for adding text overlay to images

Features:
• Batch processing support
• Drag & drop files
• Font and color customization
• Text position selection
• Preview functionality"""

        info_label = ttk.Label(
            info_frame,
            text=info_text,
            justify=tk.LEFT,
            font=("Arial", 10)
        )
        info_label.pack(anchor=tk.W)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)

        # Copyright frame with visible text
        copyright_frame = ttk.Frame(main_frame)
        copyright_frame.pack(fill=tk.X, pady=5)

        # Copyright text with clear formatting
        copyright_text = """Copyright© 2026 
License: Freeware
Author: Pavlenko Evgeniy
Email: pavlenkoevgeniy85@gmail.com"""

        copyright_label = ttk.Label(
            copyright_frame,
            text=copyright_text,
            justify=tk.LEFT,
            font=("Arial", 10),
            foreground="#333333"
        )
        copyright_label.pack(anchor=tk.W, pady=5)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top panel - image loading
        load_frame = ttk.LabelFrame(main_frame, text="Image Loading", padding="10")
        load_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(load_frame, text="Select Images", command=self.load_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(load_frame, text="Clear List", command=self.clear_images).pack(side=tk.LEFT, padx=5)

        # Files list
        files_frame = ttk.Frame(load_frame)
        files_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        if HAS_DND:
            dnd_text = "Drag & drop files here or click button above"
        else:
            dnd_text = "Click 'Select Images' to load files"
        ttk.Label(files_frame, text=dnd_text).pack(side=tk.LEFT)

        # Navigation
        nav_frame = ttk.LabelFrame(main_frame, text="Navigation", padding="10")
        nav_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(nav_frame, text="◄ Previous", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        self.image_counter_label = ttk.Label(nav_frame, text="0 / 0")
        self.image_counter_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(nav_frame, text="Next ►", command=self.next_image).pack(side=tk.LEFT, padx=5)

        ttk.Label(nav_frame, text="File name:").pack(side=tk.LEFT, padx=(20, 5))
        self.filename_label = ttk.Label(nav_frame, text="")
        self.filename_label.pack(side=tk.LEFT)

        # Add rename checkbox to navigation frame
        ttk.Checkbutton(
            nav_frame,
            text="Overwrite original file",
            variable=self.rename_files
        ).pack(side=tk.LEFT, padx=(20, 5))

        # Text settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Text Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Text
        ttk.Label(settings_frame, text="Text:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(settings_frame, width=50)
        self.text_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=5)
        self.text_entry.insert(0, "Your text")

        # Text color
        ttk.Label(settings_frame, text="Text color:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.color_preview = tk.Label(settings_frame, bg=self.text_color, width=5, height=1, relief=tk.RIDGE)
        self.color_preview.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(settings_frame, text="Choose color", command=self.choose_color).grid(row=1, column=2, sticky=tk.W,
                                                                                        pady=5)

        # Text position
        ttk.Label(settings_frame, text="Position:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.position_var = tk.StringVar(value="bottom right")
        positions = ["top left", "top right", "bottom left", "bottom right", "center"]
        position_menu = ttk.Combobox(settings_frame, textvariable=self.position_var, values=positions, width=20)
        position_menu.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Offset
        ttk.Label(settings_frame, text="Offset up (px):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.offset_up = ttk.Entry(settings_frame, width=10)
        self.offset_up.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        self.offset_up.insert(0, "20")

        ttk.Label(settings_frame, text="Offset left (px):").grid(row=3, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.offset_left = ttk.Entry(settings_frame, width=10)
        self.offset_left.grid(row=3, column=3, sticky=tk.W, pady=5, padx=5)
        self.offset_left.insert(0, "20")

        # Font style
        ttk.Label(settings_frame, text="Font style:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.font_style_var = tk.StringVar(value="Normal")
        font_styles = ["Normal", "Bold", "Italic", "Bold Italic"]
        font_menu = ttk.Combobox(settings_frame, textvariable=self.font_style_var, values=font_styles, width=20)
        font_menu.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # Font size
        ttk.Label(settings_frame, text="Font size:").grid(row=4, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.font_size_spin = ttk.Spinbox(settings_frame, from_=10, to=200, width=10)
        self.font_size_spin.grid(row=4, column=3, sticky=tk.W, pady=5, padx=5)
        self.font_size_spin.set("40")

        # Font file selection
        ttk.Label(settings_frame, text="Font file:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.font_file_label = ttk.Label(settings_frame, text="System (default)")
        self.font_file_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        ttk.Button(settings_frame, text="Select font", command=self.choose_font).grid(row=5, column=3, sticky=tk.W,
                                                                                      pady=5)

        # Output directory settings
        ttk.Label(settings_frame, text="Output Folder:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.output_dir_entry = ttk.Entry(settings_frame, textvariable=self.output_dir_var, width=30)
        self.output_dir_entry.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(settings_frame, text="Browse", command=self.browse_output_dir).grid(row=6, column=3, padx=5)

        # Show current app directory info
        ttk.Label(settings_frame, text=f"App location: {self.app_dir}", font=("Arial", 8)).grid(
            row=7, column=0, columnspan=4, sticky=tk.W, pady=(2, 5)
        )

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Apply to All", command=self.apply_to_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Preview", command=self.preview_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Save Current", command=self.save_current_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Save All", command=self.save_all_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Preview area
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(preview_frame, bg='gray', width=600, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def browse_output_dir(self):
        """Browse for output directory"""
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=self.app_dir)
        if folder:
            self.output_dir_var.set(folder)

    def setup_drag_drop(self):
        """Setup drag and drop using tkinterdnd2"""
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.drop_files)

            self.preview_canvas.drop_target_register(DND_FILES)
            self.preview_canvas.dnd_bind('<<Drop>>', self.drop_files)
        except Exception as e:
            print(f"Error setting up drag & drop: {e}")

    def drop_files(self, event):
        """Handle dropped files"""
        if HAS_DND:
            files = self.root.tk.splitlist(event.data)
            self.add_files(files)

    def add_files(self, file_paths):
        """Add files to list"""
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif')
        added = 0

        for path in file_paths:
            if os.path.exists(path) and path.lower().endswith(valid_extensions):
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

    def load_images(self):
        """Load images via dialog"""
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif")]
        )

        if file_paths:
            self.add_files(list(file_paths))

    def load_current_image(self):
        """Load current image"""
        if self.image_paths and self.current_index < len(self.image_paths):
            try:
                # Fix для замороженных приложений
                image_path = self.image_paths[self.current_index]
                self.original_image = Image.open(image_path)
                self.filename_label.config(text=os.path.basename(image_path))
                self.show_preview()
                self.update_counter()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def update_counter(self):
        """Update image counter"""
        total = len(self.image_paths)
        current = self.current_index + 1 if total > 0 else 0
        self.image_counter_label.config(text=f"{current} / {total}")

    def update_file_list(self):
        """Update file list info"""
        total = len(self.image_paths)
        if total > 0:
            self.image_counter_label.config(text=f"1 / {total}")
            self.filename_label.config(text=os.path.basename(self.image_paths[0]))
        else:
            self.image_counter_label.config(text="0 / 0")
            self.filename_label.config(text="")

    def next_image(self):
        """Go to next image"""
        if self.image_paths and self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_current_image()

    def prev_image(self):
        """Go to previous image"""
        if self.image_paths and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def clear_images(self):
        """Clear image list"""
        self.image_paths.clear()
        self.processed_images.clear()
        self.current_index = 0
        self.original_image = None
        self.preview_image = None
        self.filename_label.config(text="")
        self.image_counter_label.config(text="0 / 0")
        self.preview_canvas.delete("all")

    def choose_color(self):
        color = colorchooser.askcolor(title="Select text color")
        if color[0]:
            self.text_color = color[1]
            self.color_preview.config(bg=self.text_color)

    def choose_font(self):
        file_path = filedialog.askopenfilename(
            title="Select font file",
            filetypes=[("Fonts", "*.ttf *.otf")]
        )
        if file_path:
            self.font_path = file_path
            self.font_file_label.config(text=os.path.basename(file_path))

    def get_font(self, size):
        """Get font with style"""
        style = self.font_style_var.get()

        if style == "Bold":
            pil_style = "bold"
        elif style == "Italic":
            pil_style = "italic"
        elif style == "Bold Italic":
            pil_style = "bold italic"
        else:
            pil_style = "normal"

        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except:
                messagebox.showwarning("Error", "Failed to load font. Using system font.")
                return ImageFont.load_default()
        else:
            try:
                # Пробуем разные системные шрифты
                font_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]
                for font_name in font_names:
                    try:
                        return ImageFont.truetype(font_name, size)
                    except:
                        continue
                return ImageFont.load_default()
            except:
                return ImageFont.load_default()

    def get_text_position(self, img_width, img_height, text_width, text_height):
        """Calculate text position"""
        position = self.position_var.get()

        try:
            offset_up = int(self.offset_up.get())
            offset_left = int(self.offset_left.get())
        except ValueError:
            offset_up = 20
            offset_left = 20

        x = 0
        y = 0

        if position == "top left":
            x = offset_left
            y = offset_up
        elif position == "top right":
            x = img_width - text_width - offset_left
            y = offset_up
        elif position == "bottom left":
            x = offset_left
            y = img_height - text_height - offset_up
        elif position == "bottom right":
            x = img_width - text_width - offset_left
            y = img_height - text_height - offset_up
        elif position == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2

        return x, y

    def apply_text_to_image(self, image):
        """Apply text to image and return result"""
        text = self.text_entry.get()
        if not text:
            messagebox.showwarning("Error", "Please enter text!")
            return None

        try:
            font_size = int(self.font_size_spin.get())
        except ValueError:
            font_size = 40

        img = image.copy()
        draw = ImageDraw.Draw(img)
        font = self.get_font(font_size)

        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width, text_height = draw.textsize(text, font=font)

        x, y = self.get_text_position(img.width, img.height, text_width, text_height)

        draw.text((x, y), text, fill=self.text_color, font=font)

        return img

    def preview_text(self):
        if self.original_image is None:
            messagebox.showwarning("Error", "Please load an image!")
            return

        result = self.apply_text_to_image(self.original_image)
        if result:
            self.preview_image = result
            self.show_preview(result)

    def apply_to_all(self):
        """Apply text to all images"""
        if not self.image_paths:
            messagebox.showwarning("Error", "No images loaded!")
            return

        text = self.text_entry.get()
        if not text:
            messagebox.showwarning("Error", "Please enter text!")
            return

        self.processed_images.clear()

        for path in self.image_paths:
            try:
                img = Image.open(path)
                result = self.apply_text_to_image(img)
                if result:
                    self.processed_images.append(result)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {os.path.basename(path)}: {e}")
                return

        if self.processed_images:
            self.preview_image = self.processed_images[0]
            self.show_preview(self.preview_image)
            messagebox.showinfo("Success", f"Processed {len(self.processed_images)} images")

    def show_preview(self, img=None):
        """Show image preview on canvas"""
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
        img_copy.thumbnail((canvas_width - 10, canvas_height - 10), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img_copy)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=photo,
            anchor=tk.CENTER
        )
        self.preview_canvas.image = photo

    def get_output_path(self, original_path):
        """Get the output path for a processed image"""
        # Get the output directory (should be absolute path from app_dir)
        output_dir = self.output_dir_var.get().strip()

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Get the original filename without extension
        base_name = os.path.basename(original_path)
        name, ext = os.path.splitext(base_name)

        # Create the output filename with _text suffix
        output_filename = f"{name}_text{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # Add number suffix if file already exists
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{name}_text_{counter}{ext}")
            counter += 1

        return output_path

    def save_current_image(self):
        """Save current image with optional rename"""
        if self.preview_image is None:
            messagebox.showwarning("Error", "Please preview first!")
            return

        # Get the original file path
        original_path = self.image_paths[self.current_index]

        # Determine default name based on checkbox
        if self.rename_files.get():
            # Overwrite original file
            file_path = original_path

            # Check if we should overwrite
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite",
                                           f"File '{os.path.basename(file_path)}' already exists. Do you want to overwrite it?"):
                    return

            self.preview_image.save(file_path)
            messagebox.showinfo("Success", f"Image overwritten: {file_path}")
        else:
            # Save to output folder
            output_path = self.get_output_path(original_path)
            self.preview_image.save(output_path)
            messagebox.showinfo("Success", f"Image saved:\n{output_path}")

    def save_all_images(self):
        """Save all processed images with optional rename"""
        if not self.processed_images:
            messagebox.showwarning("Error", "Please apply text to all images first!")
            return

        # Check if rename checkbox is checked
        if self.rename_files.get():
            # Overwrite original files
            saved = 0
            for i, img in enumerate(self.processed_images):
                original_path = self.image_paths[i]

                # Check if file exists
                if os.path.exists(original_path):
                    if not messagebox.askyesno("Confirm Overwrite",
                                               f"File '{os.path.basename(original_path)}' exists. Overwrite all files?"):
                        return
                    break

            # Save all files overwriting originals
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

    def clear_all(self):
        """Clear everything"""
        self.image_paths.clear()
        self.processed_images.clear()
        self.current_index = 0
        self.original_image = None
        self.preview_image = None
        self.filename_label.config(text="")
        self.image_counter_label.config(text="0 / 0")
        self.preview_canvas.delete("all")

        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, "Your text")
        self.offset_up.delete(0, tk.END)
        self.offset_up.insert(0, "20")
        self.offset_left.delete(0, tk.END)
        self.offset_left.insert(0, "20")
        self.text_color = "#FFFFFF"
        self.color_preview.config(bg=self.text_color)
        self.font_path = None
        self.font_file_label.config(text="System (default)")
        self.position_var.set("bottom right")
        self.font_style_var.set("Normal")
        self.font_size_spin.set("40")
        self.rename_files.set(False)
        # Reset output directory to app directory
        self.output_dir_var.set(os.path.join(self.app_dir, "processed_images"))


if __name__ == "__main__":
    # Use TkinterDnD if available, otherwise use regular Tk
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = TextOverlayApp(root)
    root.mainloop()