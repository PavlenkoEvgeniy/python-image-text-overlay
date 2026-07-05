pyinstaller:
	pyinstaller --onefile --windowed --hidden-import=PIL._tkinter_finder --hidden-import=PIL._imagingtk --name ImageTextOverlay main.py