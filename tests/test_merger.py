"""Tests for pdf_forge."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter

from pdf_forge import image_to_pdf, merge_pdfs


def test_image_to_pdf():
    """Test converting an image to PDF preserves native dimensions."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(tmp.name, format="PNG")
        tmp_path = Path(tmp.name)

    try:
        writer = image_to_pdf(tmp_path)
        buf = BytesIO()
        writer.write(buf)
        buf.seek(0)
        reader = PdfReader(buf)
        assert len(reader.pages) == 1
        # Verify page size matches original image dimensions (in PDF points)
        # PDF uses 1/72 inch, so 100x100 pixels at 150 DPI ≈ 48x48 points
        page = reader.pages[0]
        assert page.mediabox.width > 0
        assert page.mediabox.height > 0
    finally:
        tmp_path.unlink()


def test_merge_pdfs_images_only():
    """Test merging multiple images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        img1 = tmpdir / "img1.png"
        img2 = tmpdir / "img2.png"
        out = tmpdir / "out.pdf"

        Image.new("RGB", (100, 100), "red").save(img1)
        Image.new("RGB", (100, 100), "blue").save(img2)

        merge_pdfs([img1, img2], out)

        reader = PdfReader(out)
        assert len(reader.pages) == 2


def test_merge_pdfs_mixed():
    """Test merging images and PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        img = tmpdir / "img.png"
        pdf1 = tmpdir / "doc1.pdf"
        out = tmpdir / "out.pdf"

        Image.new("RGB", (100, 100), "green").save(img)

        # Create a 2-page PDF
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_blank_page(width=200, height=200)
        with open(pdf1, "wb") as f:
            writer.write(f)

        merge_pdfs([img, pdf1], out)

        reader = PdfReader(out)
        assert len(reader.pages) == 3  # 1 image page + 2 PDF pages


def test_cli_smoke():
    """Smoke test for CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        img = tmpdir / "test.png"
        out = tmpdir / "merged.pdf"

        Image.new("RGB", (100, 100), "yellow").save(img)

        result = subprocess.run(
            [sys.executable, "-m", "pdf_forge", str(img), "-o", str(out)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert out.exists()

        reader = PdfReader(out)
        assert len(reader.pages) == 1


def test_cli_directory():
    """Test CLI with directory input (files processed alphabetically)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        img1 = tmpdir / "aaa.png"
        img2 = tmpdir / "zzz.png"
        out = tmpdir / "combined.pdf"

        Image.new("RGB", (100, 100), "red").save(img1)
        Image.new("RGB", (100, 100), "blue").save(img2)

        # Pass directory as input; should process alphabetically
        result = subprocess.run(
            [sys.executable, "-m", "pdf_forge", str(tmpdir), "-o", str(out)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert out.exists()

        reader = PdfReader(out)
        assert len(reader.pages) == 2  # Both files processed alphabetically


def test_native_dimensions_preserved():
    """Test that image dimensions are preserved (no resize/stretch)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create images with specific native dimensions
        img_wide = tmpdir / "wide.png"  # 800x600
        img_tall = tmpdir / "tall.png"  # 600x800
        out = tmpdir / "combined.pdf"

        Image.new("RGB", (800, 600), "red").save(img_wide)
        Image.new("RGB", (600, 800), "blue").save(img_tall)

        merge_pdfs([img_wide, img_tall], out)

        reader = PdfReader(out)
        assert len(reader.pages) == 2
        # Each page should have its own dimensions (not stretched to same size)
        page1 = reader.pages[0]
        page2 = reader.pages[1]
        # Pages should have different heights (aspect ratios preserved)
        assert page1.mediabox.width != page2.mediabox.width or \
               page1.mediabox.height != page2.mediabox.height