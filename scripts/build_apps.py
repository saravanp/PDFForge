#!/usr/bin/env python3
"""Build the PDFForge GUI and CLI as separate standalone applications."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
GUI_ENTRY = ROOT / "scripts" / "gui_entry.py"
CLI_ENTRY = ROOT / "scripts" / "cli_entry.py"

APP_NAME = "PDFForge"
CLI_NAME = "pdf-forge"
BUNDLE_ID = "com.saravanp.pdfforge"


def pyinstaller(*args: str) -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        *args,
    ]
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def build_gui() -> Path:
    args = [
        "--name",
        APP_NAME,
        "--windowed",
        "--onedir",
        "--collect-all",
        "tkinterdnd2",
    ]
    if sys.platform == "darwin":
        args.extend(["--osx-bundle-identifier", BUNDLE_ID])
    args.append(str(GUI_ENTRY))
    pyinstaller(*args)

    artifact = DIST / f"{APP_NAME}.app" if sys.platform == "darwin" else DIST / APP_NAME
    print(f"GUI artifact: {artifact}")
    return artifact


def build_cli() -> Path:
    pyinstaller(
        "--name",
        CLI_NAME,
        "--console",
        "--onefile",
        str(CLI_ENTRY),
    )

    artifact = DIST / f"{CLI_NAME}.exe" if sys.platform == "win32" else DIST / CLI_NAME
    print(f"CLI artifact: {artifact}")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        choices=("all", "gui", "cli"),
        default="all",
        help="Artifact to build (default: all)",
    )
    args = parser.parse_args()

    if args.target in ("all", "gui"):
        build_gui()
    if args.target in ("all", "cli"):
        build_cli()


if __name__ == "__main__":
    main()
