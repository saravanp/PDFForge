# Building PDFForge

PDFForge is distributed as two separate standalone applications:

- **GUI:** a desktop application built with PyInstaller
- **CLI:** a command-line executable built with PyInstaller

Both packages bundle Python and project dependencies, so users do not need Python installed. PyInstaller does not cross-compile; build on the target operating system and CPU architecture.

## Requirements

- [uv](https://github.com/astral-sh/uv)
- Python 3.14, installed automatically by `uv`
- The target OS and architecture:
  - macOS: Apple Silicon (arm64)
  - Linux: the architecture you plan to distribute
  - Windows: the architecture you plan to distribute

## Build the applications

Install dependencies and build both artifacts in one command:

```bash
uv sync && uv run python scripts/build_apps.py
```

Build them independently:

```bash
uv run python scripts/build_apps.py gui
uv run python scripts/build_apps.py cli
```

Artifacts are written to `dist/`:

| Platform | GUI | CLI |
|----------|-----|-----|
| macOS | `PDFForge.app` | `pdf-forge` |
| Linux | `PDFForge/PDFForge` | `pdf-forge` |
| Windows | `PDFForge/PDFForge.exe` | `pdf-forge.exe` |

A Linux build produces:

```text
dist/
├── PDFForge/
│   ├── PDFForge
│   └── _internal/
└── pdf-forge
```

`dist/PDFForge/` is a PyInstaller one-dir bundle. The executable and its `_internal/` support files must be kept together. `dist/pdf-forge` is a single-file executable.

### Run the built apps

Artifacts are run from the repository root:

```bash
# macOS
open dist/PDFForge.app
./dist/pdf-forge --help

# Linux
./dist/PDFForge/PDFForge
./dist/pdf-forge --help

# Windows (PowerShell)
.\dist\PDFForge\PDFForge.exe
.\dist\pdf-forge.exe --help
```

The CLI requires at least one `inputs` argument; `--help` prints usage.

On macOS, PyInstaller also leaves a `dist/PDFForge/` directory. This is the intermediate one-folder build; distribute `PDFForge.app`, not that directory. On Linux and Windows, `dist/PDFForge/` is the GUI application directory.

## macOS (Apple Silicon)

```bash
uv sync && uv run python scripts/build_apps.py

open dist/PDFForge.app
./dist/pdf-forge --help
```

Create release ZIPs:

```bash
ditto -c -k --sequesterRsrc --keepParent \
  dist/PDFForge.app PDFForge-0.1.0-arm64.zip

(cd dist && zip ../pdf-forge-0.1.0-arm64.zip pdf-forge)
shasum -a 256 *.zip > SHA256SUMS.txt
```

Unsigned apps are blocked by Gatekeeper on current macOS. Without an Apple Developer account, document that users must open **System Settings → Privacy & Security**, click **Open Anyway**, and launch again. Signing and notarization are required for a warning-free experience.

## Linux

Build separately for each target architecture. For Intel/AMD use `linux/amd64`; for ARM use `linux/arm64`.

### Debian

```bash
docker run --rm -it --platform linux/amd64 \
  -v "$PWD":/src -w /src debian:latest bash
```

Inside the container:

```bash
apt-get update
apt-get install -y curl ca-certificates binutils xvfb \
  libx11-6 libxext6 libxrender1 libxft2 libfontconfig1 libxss1

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

uv sync && uv run python scripts/build_apps.py

./dist/pdf-forge --help
xvfb-run -a timeout 10 ./dist/PDFForge/PDFForge
```

### Ubuntu 26.04

```bash
docker run --rm -it --platform linux/amd64 \
  -v "$PWD":/src -w /src ubuntu:26.04 bash
```

Use the same commands inside the container.

### Fedora

```bash
docker run --rm -it --platform linux/amd64 \
  -v "$PWD":/src -w /src fedora:latest bash
```

Inside the container:

```bash
dnf install -y curl ca-certificates binutils \
  xorg-x11-server-Xvfb libX11 libXext libXrender libXft \
  fontconfig libXScrnSaver

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

uv sync && uv run python scripts/build_apps.py

./dist/pdf-forge --help
xvfb-run -a timeout 10 ./dist/PDFForge/PDFForge
```

Xvfb only confirms that the GUI starts. Test drag-and-drop and merging on a real Debian or Fedora desktop.

PyInstaller bundles Python and project dependencies, but not glibc or system X11 libraries. Artifacts built on Ubuntu 26.04 or the latest Debian require a similarly recent glibc and may not run on older distributions. Build on an older distribution if you need to support older systems.

### Verify without system Python

Run the CLI in a clean container:

```bash
docker run --rm -v "$PWD/dist:/dist" debian:latest /dist/pdf-forge --help
docker run --rm -v "$PWD/dist:/dist" ubuntu:26.04 /dist/pdf-forge --help
docker run --rm -v "$PWD/dist:/dist" fedora:latest /dist/pdf-forge --help
```

The GUI also needs X11/Tk libraries and a display, so test it on a desktop VM for the most realistic result.

## Windows

Run on Windows:

```powershell
uv sync && uv run python scripts/build_apps.py
```

This produces `dist\PDFForge\PDFForge.exe` and `dist\pdf-forge.exe`. Use Inno Setup or WiX to create an installer for the GUI if needed, and sign the executables to avoid SmartScreen warnings.

## Testing checklist

- Launch the GUI and merge a mix of images and PDFs.
- Reorder files with drag-and-drop.
- Run the CLI with individual files, a directory, and a glob pattern.
- Confirm the generated PDF opens correctly.
- Test the artifacts on a clean machine or VM without Python or uv installed.
- Verify the downloaded GUI on a clean macOS machine to check Gatekeeper behavior.

## Troubleshooting

- **PyInstaller reports missing `objdump` on Linux:** install `binutils`.
- **GUI build fails with missing Tkinter:** install the platform Tk/X11 packages or use a Python build that includes Tkinter.
- **Drag-and-drop is missing:** the build script uses `--collect-all tkinterdnd2`; verify the package data is present in the built artifact.
- **Application fails on another Linux distribution:** rebuild on an older glibc distribution or distribute an AppImage/container-based package.
