# PDFForge

PDFForge is a Python app with both Command Line Interface (CLI) and Desktop Graphical User Interface (GUI). Merge images (JPEG, PNG, etc.) and PDFs into a single PDF.

**Distribution:** PDFForge is released as two separate packages: a desktop GUI app and a CLI executable. Both bundle Python, so users do not need Python installed. Packaged macOS builds target Apple Silicon (arm64).

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
uv run python -m pdf_forge file1.jpg file2.png file3.pdf -o merged.pdf

# Use the installed entry point
uv run pdf-forge file1.jpg file2.png file3.pdf -o merged.pdf

# Specify page size for image inputs
uv run python -m pdf_forge *.jpg -o photos.pdf --page-size Letter

# For help
uv run pdf-forge --help
```

### Desktop Graphical User Interface (GUI)

```bash
# Launch the GUI
uv run pdf-forge-gui
```

**Note:** The GUI requires tkinter to be available on your system. On most Linux distributions, you may need to install `python3-tk` or equivalent package.

![PDFForge desktop GUI](docs/screenshots/gui.png)

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

## Building

The GUI and CLI are built as separate standalone applications with PyInstaller. Both bundle Python, so users do not need Python installed.

See [BUILDING.md](BUILDING.md) for macOS, Linux, and Windows build instructions, testing steps, and release packaging.

Build both apps in one command:

```bash
uv sync && uv run python scripts/build_apps.py
```

The `target` defaults to `all`. To build just one app, use `uv run python scripts/build_apps.py gui` or `uv run python scripts/build_apps.py cli`.

### Run the built apps

Artifacts are run from the repository root:

| Platform | GUI | CLI |
|----------|-----|-----|
| macOS | `open dist/PDFForge.app` | `./dist/pdf-forge --help` |
| Linux | `./dist/PDFForge/PDFForge` | `./dist/pdf-forge --help` |
| Windows (PowerShell) | `.\dist\PDFForge\PDFForge.exe` | `.\dist\pdf-forge.exe --help` |

On Linux, `dist/PDFForge/` is a directory containing the GUI executable and its `_internal/` support files; the executable is `dist/PDFForge/PDFForge`. The CLI is `dist/pdf-forge` and requires at least one `inputs` argument. Use `--help` for usage, or pass files, directories, or glob patterns:

```bash
./dist/pdf-forge file1.jpg file2.pdf -o merged.pdf
```

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
PDFForge/
├── src/
│   └── pdf_forge/
│       ├── __init__.py        # Core merging logic
│       ├── __main__.py        # CLI entry point
│       └── gui.py             # Desktop GUI implementation
├── scripts/                   # Standalone packaging build scripts
├── tests/                     # Unit tests
├── test_data/                 # Sample test files
├── BUILDING.md                # Build, test, and release instructions
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## How It Works

PDFForge works by:
1. Accepting input files (images or PDFs) via CLI arguments or GUI
2. Converting images to PDF pages while preserving original dimensions
3. Appending existing PDFs as-is
4. Merging all pages into a single output PDF

Images are converted at their native resolution without resizing or stretching, maintaining their original aspect ratio and quality.
