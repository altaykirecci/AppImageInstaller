import os
import shutil
import subprocess
import tempfile
import argparse
import json
from configparser import ConfigParser
import importlib.metadata
import traceback

HOME = os.path.expanduser("~")
VERSION_FILE = os.path.join(HOME, ".local", "share", "appimage-versions.json")

# Global language data
_lang_data = None

def get_version():
    try:
        return importlib.metadata.version("appimage-installer")
    except importlib.metadata.PackageNotFoundError:
        return "1.0.0"  # Fallback version if package is not installed

def load_language(lang):
    global _lang_data
    try:
        lang_file = os.path.join(os.path.dirname(__file__), "locales", f"{lang}.json")
        if not os.path.exists(lang_file):
            lang_file = os.path.join(os.path.dirname(__file__), "locales", "en.json")
        
        with open(lang_file, 'r', encoding='utf-8') as f:
            _lang_data = json.load(f)
        return _lang_data
    except Exception as e:
        traceback.print_exc()
        return None

def _(key, **kwargs):
    global _lang_data
    try:
        if not _lang_data:
            return key
            
        if not isinstance(key, str):
            key = str(key)
            
        text = _lang_data.get(key, key)
        
        if not kwargs:
            return text
            
        try:
            # Remove 'key' from kwargs if it exists to avoid duplicate
            if 'key' in kwargs:
                del kwargs['key']
            formatted_kwargs = {k: str(v) for k, v in kwargs.items()}
            return text.format(**formatted_kwargs)
        except KeyError as e:
            traceback.print_exc()
            return text
        except Exception as e:
            traceback.print_exc()
            return text
    except Exception as e:
        traceback.print_exc()
        return key

def load_versions():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_versions(versions):
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
    with open(VERSION_FILE, 'w') as f:
        json.dump(versions, f, indent=4)

def extract_appimage(appimage_path, extract_dir):
    try:
        subprocess.run([appimage_path, "--appimage-extract"], cwd=extract_dir, check=True)
        return os.path.join(extract_dir, "squashfs-root")
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        raise
    except Exception as e:
        traceback.print_exc()
        raise

def find_file(root, extension):
    try:
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                if f.endswith(extension):
                    return os.path.join(dirpath, f)
        return None
    except Exception as e:
        traceback.print_exc()
        return None

def parse_desktop_file(path):
    try:
        parser = ConfigParser(strict=False, interpolation=None)
        parser.read(path)
        entry = parser["Desktop Entry"]
        return {
            "Name": entry.get("Name", ""),
            "Comment": entry.get("Comment", ""),
            "Categories": entry.get("Categories", ""),
            "Exec": entry.get("Exec", ""),
            "Icon": entry.get("Icon", ""),
            "Version": entry.get("Version", "1.0")
        }
    except Exception as e:
        traceback.print_exc()
        raise

def slugify(name):
    return name.lower().replace(" ", "_")

def install_appimage(appimage_path, sandbox=True):
    print(_("installing"))
    os.chmod(appimage_path, os.stat(appimage_path).st_mode | 0o111)

    temp_dir = tempfile.mkdtemp()
    try:
        squashfs_root = extract_appimage(appimage_path, temp_dir)
        desktop_src = find_file(squashfs_root, ".desktop")
        if not desktop_src:
            print(_("error_desktop"))
            return

        data = parse_desktop_file(desktop_src)
        app_name = slugify(data["Name"])

        versions = load_versions()
        versions[app_name] = {
            "version": data["Version"],
            "path": appimage_path
        }
        save_versions(versions)

        bin_dir = os.path.join(HOME, ".local", "bin")
        os.makedirs(bin_dir, exist_ok=True)
        appimage_target = os.path.join(bin_dir, os.path.basename(appimage_path))
        shutil.copy(appimage_path, appimage_target)

        icon_filename = data["Icon"]
        icon_exts = [".png", ".svg", ".xpm"]
        icon_src = None
        for ext in icon_exts:
            icon_src = find_file(squashfs_root, ext)
            if icon_src and icon_filename in os.path.basename(icon_src):
                break

        icon_target_dir = os.path.join(HOME, ".local", "share", "icons")
        os.makedirs(icon_target_dir, exist_ok=True)
        icon_target = os.path.join(icon_target_dir, f"{app_name}.png")
        if icon_src:
            shutil.copy(icon_src, icon_target)
        else:
            print(_("icon_not_found"))

        desktop_dir = os.path.join(HOME, ".local", "share", "applications")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_target = os.path.join(desktop_dir, f"{app_name}.desktop")

        exec_command = appimage_target
        if not sandbox:
            exec_command = f"{appimage_target} --no-sandbox"

        with open(desktop_target, "w") as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name={data['Name']}
Comment={data['Comment']}
Exec={exec_command}
Icon={icon_target if icon_src else data['Icon']}
Terminal=false
Categories={data['Categories']};
""")
        os.chmod(desktop_target, 0o755)

        subprocess.run(["update-desktop-database", desktop_dir])

        print(_("installation_complete", name=data["Name"]))
    except Exception as e:
        print(_("error_occurred", error=str(e)))
    finally:
        shutil.rmtree(temp_dir)

def uninstall_app(app_name):
    try:
        app_name = slugify(app_name)
        print(_("uninstalling", name=app_name))

        appimage_path = os.path.join(HOME, ".local", "bin", f"{app_name}.AppImage")
        if not os.path.exists(appimage_path):
            print(_("appimage_not_found", path=appimage_path))
            return

        temp_dir = tempfile.mkdtemp()
        try:
            squashfs_root = extract_appimage(appimage_path, temp_dir)
            desktop_src = find_file(squashfs_root, ".desktop")
            if not desktop_src:
                print(_("error_desktop"))
                return

            data = parse_desktop_file(desktop_src)
            actual_app_name = slugify(data["Name"])

            paths = {
                "AppImage": appimage_path,
                "Desktop": os.path.join(HOME, ".local", "share", "applications", f"{actual_app_name}.desktop"),
                "Icon": os.path.join(HOME, ".local", "share", "icons", f"{actual_app_name}.png"),
            }

            for key, path in paths.items():
                if os.path.exists(path):
                    os.remove(path)
                    print(_("deleted", type=key, path=path))
                else:
                    print(_("not_found", type=key, path=path))

            versions = load_versions()
            if actual_app_name in versions:
                del versions[actual_app_name]
                save_versions(versions)

            subprocess.run(["update-desktop-database", os.path.join(HOME, ".local", "share", "applications")])
            print(_("uninstall_complete"))
        except Exception as e:
            traceback.print_exc()
            error_msg = str(e)
            print(_("error_occurred", error=error_msg))
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)
        print(_("error_occurred", error=error_msg))

def list_installed_apps():
    versions = load_versions()
    if not versions:
        print(_("no_installed_apps"))
        return

    print(f"\n{_('installed_apps')}")
    print("-" * 50)
    for app_name, info in versions.items():
        print(f"{_('app')}: {app_name}")
        print(f"{_('version')}: {info['version']}")
        print(f"{_('location')}: {info['path']}")
        print("-" * 50)

def main():
    # First parse language argument
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--lang', '-L', default='en')
    args, remaining = parser.parse_known_args()
    
    # Load language
    load_language(args.lang)
    
    # Now create the main parser with translated help texts
    parser = argparse.ArgumentParser(description='AppImage Installer')
    parser.add_argument('--install', '-i', help=_('help_install'))
    parser.add_argument('--uninstall', '-u', help=_('help_uninstall'))
    parser.add_argument('--list', '-l', action='store_true', help=_('help_list'))
    parser.add_argument('--sandbox', '-s', action='store_true', help=_('help_sandbox'))
    parser.add_argument('--lang', '-L', default='en', help=_('help_lang'))
    parser.add_argument('--version', '-v', action='store_true', help=_('help_version'))
    parser.add_argument('--report-translations', '-r', action='store_true', help=_('help_report_translations'))
    parser.add_argument('--clean', '-c', action='store_true', help=_('help_clean'))
    args = parser.parse_args()

    # Show version
    if args.version:
        print(f"AppImage Installer v{get_version()}")
        return

    # Report translations
    if args.report_translations:
        report_missing_translations()
        return

    # List installed apps
    if args.list:
        list_installed_apps()
        return

    # Install AppImage
    if args.install:
        try:
            install_appimage(args.install, args.sandbox)
            if args.clean:
                try:
                    os.remove(args.install)
                    print(_('original_deleted', path=args.install))
                except Exception as e:
                    error_msg = str(e)
                    print(_('error_occurred', error=error_msg))
        except Exception as e:
            error_msg = str(e)
            print(_('error_occurred', error=error_msg))
        return

    # Uninstall app
    if args.uninstall:
        try:
            uninstall_app(args.uninstall)
        except Exception as e:
            error_msg = str(e)
            print(_('error_occurred', error=error_msg))
        return

    parser.print_help()

if __name__ == "__main__":
    main()
