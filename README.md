# PDF Merger

A PDF merger app in Python with both Command Line Interface (CLI) and Desktop Graphical User Interface (GUI). Merge images (JPEG, PNG, etc.) and PDFs into a single PDF.

## Features

- Convert images (JPEG, PNG, GIF, BMP, TIFF, WebP) to PDF pages
- Merge PDFs and images in any order
- Configurable page size for image inputs (A4 or Letter)
- Drag-and-drop file reordering in GUI
- Built with [uv](https://github.com/astral-sh/uv) and [pypdf](https://pypdf.readthedocs.io/)

## Installation

```bash
uv sync
```

## Usage

### Command Line Interface (CLI)

```bash
# Merge images and PDFs
uv run python -m pdf_merger file1.jpg file2.png file3.pdf -o merged.pdf

# Use the installed entry point
uv run pdf-merger file1.jpg file2.png file3.pdf -o merged.pdf

# Specify page size for image inputs
uv run python -m pdf_merger *.jpg -o photos.pdf --page-size Letter

# For help
uv run pdf-merger --help
```

### Desktop Graphical User Interface (GUI)

```bash
# Launch the GUI
uv run pdf-merger-gui
```

**Note:** The GUI requires tkinter to be available on your system. On most Linux distributions, you may need to install `python3-tk` or equivalent package.

#### GUI Features:
- Drag and drop files to reorder them
- Add individual files or entire folders
- Move selected files up/down in the merge queue
- Real-time status and progress indicators
- File type identification (PDF/Image)
- Output file location selection

### Options (CLI only)

| Option | Description |
|--------|-------------|
| `inputs` | Input files/directories or '*' glob patterns |
| `-o, --output` | Output PDF path (default: `merged.pdf`) |
| `--page-size` | Page size for image inputs: `A4` or `Letter` (default: `A4`) |
| `-v, --verbose` | Show processing details |

## Development

```bash
# Run tests
uv run pytest

# Update dependencies
uv lock

# Run linting/formatting (if configured)
# uv run ruff check .  # example
```

## Project Structure

```
pdf-merger/
├── src/
│   └── pdf_merger/
│       ├── __init__.py        # Core PDF merger logic
│       ├── __main__.py        # CLI entry point
│       └── gui.py             # Desktop GUI implementation
├── tests/                     # Unit tests
├── test_data/                 # Sample test files
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## How It Works

The PDF merger works by:
1. Accepting input files (images or PDFs) via CLI arguments or GUI
2. Converting images to PDF pages while preserving original dimensions
3. Appending existing PDFs as-is
4. Merging all pages into a single output PDF

Images are converted at their native resolution without resizing or stretching, maintaining their original aspect ratio and quality.
