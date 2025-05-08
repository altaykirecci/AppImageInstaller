# AppImage Installer

A command-line tool for installing and managing AppImage applications on Linux systems.

## Features

- Install AppImage applications with proper desktop integration
- Uninstall applications
- List installed applications
- Multi-language support (English and Turkish)
- Secure installation process
- Sandbox support

## Installation

```bash
pip install appimage-installer
```

## Usage

```bash
# Install an AppImage
appimage-installer install /path/to/application.AppImage

# List installed applications
appimage-installer list

# Uninstall an application
appimage-installer uninstall application-name

# Set language (en/tr/de/fr)
appimage-installer --lang tr install /path/to/application.AppImage

# Show available languages
appimage-installer --available-languages

# Show version
appimage-installer --version
```

## Requirements

- Python 3.6 or higher
- Linux operating system

## License

MIT License

## Author

Developed by [altaykirecci](https://github.com/altaykirecci)
`opriori (c)(p)2025 (https://www.opriori.com.tr)`