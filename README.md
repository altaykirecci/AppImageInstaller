# AppImage Installer

A command-line tool for installing and managing AppImage applications on Linux.

## Features

- Install AppImage applications
- Uninstall installed applications
- List installed applications
- Multi-language support (English, Turkish, German, French)
- Sandbox support
- Clean installation option

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/appimage-installer.git
cd appimage-installer

# Install the package
pip install .
```

### Using PyInstaller (Standalone Binary)

```bash
# Build the standalone binary
pyinstaller --onefile --name appimage-installer appimage_installer/__init__.py

# The binary will be created in the dist directory
```

## Usage

```bash
# Install an AppImage
appimage-installer -i /path/to/app.AppImage

# Install with sandbox disabled
appimage-installer -i /path/to/app.AppImage -s

# Install and delete original file
appimage-installer -i /path/to/app.AppImage -c

# Uninstall an application
appimage-installer -u appname

# List installed applications
appimage-installer -l

# Show version
appimage-installer -v

# Change language
appimage-installer -L tr  # Turkish
appimage-installer -L de  # German
appimage-installer -L fr  # French
```

## License

MIT License

## Author

Developed by [altaykirecci](https://github.com/altaykirecci)
`opriori (c)(p)2025 (https://www.opriori.com.tr)