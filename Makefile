.PHONY: help test install-dev pyinstaller clean

help:
	@echo "Available targets:"
	@echo "  make test         - Run tests"
	@echo "  make install-dev - Install in development mode with test dependencies"
	@echo "  make pyinstaller - Build standalone executable"
	@echo "  make clean       - Clean build artifacts"

test:
	python -m pytest -v

install-dev:
	pip install -e ".[dev]"

pyinstaller:
	PYTHONPATH=src pyinstaller --onefile --windowed --hidden-import=PIL._tkinter_finder --hidden-import=PIL._imagingtk --hidden-import=tkinterdnd2 --name ImageTextOverlay main.py

clean:
	rm -rf build dist *.spec