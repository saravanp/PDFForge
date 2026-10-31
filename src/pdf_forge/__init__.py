"""PDFForge app."""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".pdf"}


def image_to_pdf(image_path: Path) -> PdfWriter:
    """Convert an image file to a single-page PDF, preserving original dimensions."""
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    writer = PdfWriter()
    import io
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=300.0)
    buf.seek(0)
    reader = PdfReader(buf)
    writer.append(reader)
    return writer


def resolve_inputs(inputs: list[Path]) -> list[Path]:
    """Resolve input paths: expand directories to sorted file lists.
    
    Supports '*' glob to load all files in a directory alphabetically.
    """
    resolved: list[Path] = []
    for path in inputs:
        if path.is_dir():
            # Read directory alphabetically, filter to supported files
            dir_files = sorted(
                [f for f in path.iterdir()
                 if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS],
                key=lambda p: p.name.lower(),
            )
            resolved.extend(dir_files)
        elif path.is_file():
            resolved.append(path)
        else:
            # Try glob expansion
            glob_matches = sorted(
                glob.glob(str(path)),
                key=lambda p: Path(p).name.lower(),
            )
            for match in glob_matches:
                p = Path(match)
                if p.is_file():
                    resolved.append(p)
                elif p.is_dir():
                    # Recurse into directory found via glob
                    dir_files = sorted(
                        [f for f in p.iterdir()
                         if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS],
                        key=lambda f: f.name.lower(),
                    )
                    resolved.extend(dir_files)
    return resolved


def merge_pdfs(input_paths: list[Path], output_path: Path) -> None:
    """Merge a list of images/PDFs into a single PDF.

    Images are converted to PDF at their native resolution (no resize/stretch).
    Existing PDFs are appended as-is.
    """
    writer = PdfWriter()

    for path in input_paths:
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}:
            writer.append(image_to_pdf(path))
        elif suffix == ".pdf":
            reader = PdfReader(path)
            writer.append(reader)
        else:
            print(f"Skipping unsupported file: {path}", file=sys.stderr)

    with open(output_path, "wb") as f:
        writer.write(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge images and PDFs into a single PDF.",
        epilog="Examples:\n"
               "  pdf-forge photo.jpg document.pdf -o merged.pdf\n"
               "  pdf-forge ./images/ -o photos.pdf\n"
               "  pdf-forge ./images/ ./documents/ -o combined.pdf\n"
               "  pdf-forge './images/*' -o all_photos.pdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", help="Input files/directories or '*' glob")
    parser.add_argument("-o", "--output", default="merged.pdf", help="Output PDF path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show processing details")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.inputs]
    resolved = resolve_inputs(input_paths)

    if not resolved:
        print("Error: no valid input files found.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Processing {len(resolved)} file(s):")
        for p in resolved:
            print(f"  • {p}")

    output_path = Path(args.output)
    merge_pdfs(resolved, output_path)
    print(f"Merged {len(resolved)} file(s) into {output_path}")


if __name__ == "__main__":
    main()
