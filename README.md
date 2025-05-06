# AppImageInstaller

## Overview

`AppImageInstaller` is a Python-based utility for installing and uninstalling AppImage applications on Linux systems. It simplifies the process of integrating AppImages into your desktop environment by creating `.desktop` files, copying icons, and updating the desktop database.

## Features

- **Install AppImages**: Automatically extracts metadata, creates `.desktop` files, and integrates the application into your system.
- **Uninstall AppImages**: Removes the `.desktop` file, icon, and AppImage binary from your system.
- **Sandbox Support**: Optionally disable the sandbox feature for AppImages.

## Requirements

- Python 3.6 or higher
- Linux operating system
- `update-desktop-database` command available on your system

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/AppImageInstaller.git
cd AppImageInstaller
```

## Usage

Run the script using Python:

```bash
python3 appimage.py [OPTIONS]
```

### Options

- `-i, --install PATH`: Install an AppImage from the specified path.
- `-u, --uninstall NAME`: Uninstall an application by its name (e.g., `firefox`).
- `--no-sandbox`: Disable the sandbox feature for the AppImage.

### Examples

#### Installing an AppImage

To install an AppImage:

```bash
python3 appimage.py --install /path/to/application.AppImage
```

If you want to disable the sandbox feature:

```bash
python3 appimage.py --install /path/to/application.AppImage --no-sandbox
```

#### Uninstalling an AppImage

To uninstall an application:

```bash
python3 appimage.py --uninstall application_name
```

For example, to uninstall Firefox:

```bash
python3 appimage.py --uninstall firefox
```

## How It Works

1. **Installation**:
   - Extracts the AppImage to a temporary directory.
   - Finds the `.desktop` file and icon within the AppImage.
   - Copies the AppImage binary to `~/.local/bin`.
   - Copies the icon to `~/.local/share/icons`.
   - Creates a `.desktop` file in `~/.local/share/applications`.
   - Updates the desktop database.

2. **Uninstallation**:
   - Removes the `.desktop` file, icon, and AppImage binary.
   - Updates the desktop database.

## Notes

- Ensure the AppImage file is executable before running the script.
- The script uses the `slugify` function to create a consistent name for the application.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Author

Developed by [altaykirecci](https://github.com/altaykirecci)
`opriori (c)(p)2025 (https://www.opriori.com.tr)