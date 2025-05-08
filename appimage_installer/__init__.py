import os
import shutil
import subprocess
import tempfile
import argparse
import json
from configparser import ConfigParser
import importlib.metadata
import traceback
import hashlib
import stat
from pathlib import Path
import re
import sys

HOME = os.path.expanduser("~")
VERSION_FILE = os.path.join(HOME, ".local", "share", "appimage-versions.json")
ALLOWED_EXTENSIONS = {'.AppImage', '.appimage'}
ALLOWED_ICON_EXTENSIONS = {'.png', '.svg', '.xpm'}
MAX_PATH_LENGTH = 4096  # Linux'un maksimum dosya yolu uzunluğu

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
        # Get the base directory for the application
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = sys._MEIPASS
            print(f"Running in PyInstaller bundle, base_dir: {base_dir}")
        else:
            # Running in a normal Python environment
            base_dir = os.path.dirname(__file__)
            print(f"Running in normal Python environment, base_dir: {base_dir}")

        # Try to load the requested language file
        lang_file = os.path.join(base_dir, "locales", f"{lang}.json")
        print(f"Trying to load language file: {lang_file}")
        
        if not os.path.exists(lang_file):
            print(f"Language file {lang_file} not found, falling back to English")
            # Fall back to English if the requested language is not available
            lang_file = os.path.join(base_dir, "locales", "en.json")
            print(f"Trying to load English language file: {lang_file}")
        
        if not os.path.exists(lang_file):
            print(f"Language file {lang_file} not found")
            return None
            
        print(f"Loading language file: {lang_file}")
        with open(lang_file, 'r', encoding='utf-8') as f:
            _lang_data = json.load(f)
            print(f"Language data loaded: {_lang_data}")
        return _lang_data
    except Exception as e:
        print(f"Error loading language file: {e}")
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

def verify_appimage(path):
    """AppImage dosyasının güvenliğini ve geçerliliğini kontrol eder."""
    try:
        # Dosya uzantısını kontrol et
        if not any(path.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise ValueError(_("invalid_appimage"))

        # Dosya yolunun uzunluğunu kontrol et
        if len(path) > MAX_PATH_LENGTH:
            raise ValueError(_("path_too_long"))

        # Dosyanın varlığını ve okunabilirliğini kontrol et
        if not os.path.isfile(path):
            raise ValueError(_("file_not_found"))

        # Dosya izinlerini kontrol et
        st = os.stat(path)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError(_("not_a_regular_file"))

        # Dosya sahipliğini kontrol et
        if st.st_uid != os.getuid():
            raise ValueError(_("not_owned_by_user"))

        # Dosya boyutunu kontrol et (örn. 1GB'dan büyük olmamalı)
        if st.st_size > 1024 * 1024 * 1024:  # 1GB
            raise ValueError(_("file_too_large"))

        # Dosya hash'ini kontrol et (opsiyonel)
        # with open(path, 'rb') as f:
        #     file_hash = hashlib.sha256(f.read()).hexdigest()
        #     # Burada hash kontrolü yapılabilir

        return True
    except Exception as e:
        raise ValueError(str(e))

def sanitize_path(path):
    """Dosya yolunu güvenli hale getirir."""
    # Mutlak yol kontrolü
    if os.path.isabs(path):
        raise ValueError(_("absolute_path_not_allowed"))

    # Tehlikeli karakterleri temizle
    path = re.sub(r'[<>:"|?*]', '', path)
    
    # Çift nokta ve slash'ları temizle
    path = re.sub(r'\.{2,}|/{2,}', '', path)
    
    return path

def secure_mkdir(path):
    """Güvenli bir şekilde dizin oluşturur."""
    try:
        path = Path(path)
        if path.exists() and not path.is_dir():
            raise ValueError(_("path_exists_not_dir"))
        
        # Dizin izinlerini ayarla (700)
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o700)
        return str(path)
    except Exception as e:
        raise ValueError(str(e))

def secure_write(file_path, content):
    """Güvenli bir şekilde dosyaya yazar."""
    try:
        # Geçici dosya oluştur
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_path = temp_file.name
        
        # İçeriği geçici dosyaya yaz
        temp_file.write(content)
        temp_file.close()
        
        # Geçici dosyayı hedef konuma taşı
        shutil.move(temp_path, file_path)
        
        # Dosya izinlerini ayarla (600)
        os.chmod(file_path, 0o600)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise ValueError(str(e))

def secure_read(file_path):
    """Güvenli bir şekilde dosyadan okur."""
    try:
        if not os.path.exists(file_path):
            return None
            
        # Dosya izinlerini kontrol et
        st = os.stat(file_path)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError(_("not_a_regular_file"))
            
        # Dosya sahipliğini kontrol et
        if st.st_uid != os.getuid():
            raise ValueError(_("not_owned_by_user"))
            
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        raise ValueError(str(e))

def load_versions():
    """Güvenli bir şekilde versiyon bilgilerini yükler."""
    try:
        if os.path.exists(VERSION_FILE):
            content = secure_read(VERSION_FILE)
            if content:
                return json.loads(content)
        return {}
    except Exception as e:
        raise ValueError(str(e))

def save_versions(versions):
    """Güvenli bir şekilde versiyon bilgilerini kaydeder."""
    try:
        os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
        secure_write(VERSION_FILE, json.dumps(versions, indent=4))
    except Exception as e:
        raise ValueError(str(e))

def extract_appimage(appimage_path, extract_dir):
    """Güvenli bir şekilde AppImage dosyasını çıkarır."""
    try:
        # AppImage dosyasını doğrula
        verify_appimage(appimage_path)
        
        # Çıkarma dizinini güvenli hale getir
        extract_dir = secure_mkdir(extract_dir)
        
        # AppImage'ı çıkar
        subprocess.run([appimage_path, "--appimage-extract"], 
                      cwd=extract_dir, 
                      check=True,
                      capture_output=True,
                      text=True)
                      
        return os.path.join(extract_dir, "squashfs-root")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"AppImage extraction failed: {e.stderr}")
    except Exception as e:
        raise ValueError(str(e))

def find_file(root, extension):
    """Güvenli bir şekilde dosya arar."""
    try:
        if not os.path.exists(root):
            return None
            
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                if f.endswith(extension):
                    file_path = os.path.join(dirpath, f)
                    # Dosya yolunu güvenli hale getir
                    file_path = sanitize_path(file_path)
                    return file_path
        return None
    except Exception as e:
        raise ValueError(str(e))

def parse_desktop_file(path):
    """Güvenli bir şekilde desktop dosyasını ayrıştırır."""
    try:
        if not os.path.exists(path):
            raise ValueError(_("file_not_found"))
            
        parser = ConfigParser(strict=False, interpolation=None)
        parser.read(path)
        
        if "Desktop Entry" not in parser:
            raise ValueError(_("invalid_desktop_file"))
            
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
        raise ValueError(str(e))

def slugify(name):
    return name.lower().replace(" ", "_")

def install_appimage(appimage_path, sandbox=True):
    """Güvenli bir şekilde AppImage dosyasını kurar."""
    try:
        print(_("installing"))
        
        # AppImage dosyasını doğrula
        verify_appimage(appimage_path)
        
        # Çalıştırma izni ver
        os.chmod(appimage_path, os.stat(appimage_path).st_mode | 0o111)

        temp_dir = tempfile.mkdtemp()
        try:
            squashfs_root = extract_appimage(appimage_path, temp_dir)
            desktop_src = find_file(squashfs_root, ".desktop")
            if not desktop_src:
                raise ValueError(_("error_desktop"))

            data = parse_desktop_file(desktop_src)
            app_name = slugify(data["Name"])

            # Versiyon bilgilerini güncelle
            versions = load_versions()
            versions[app_name] = {
                "version": data["Version"],
                "path": appimage_path
            }
            save_versions(versions)

            # Bin dizinini oluştur
            bin_dir = secure_mkdir(os.path.join(HOME, ".local", "bin"))
            appimage_target = os.path.join(bin_dir, os.path.basename(appimage_path))
            shutil.copy(appimage_path, appimage_target)
            os.chmod(appimage_target, 0o755)

            # İkon dosyasını bul ve kopyala
            icon_filename = data["Icon"]
            icon_src = None
            for ext in ALLOWED_ICON_EXTENSIONS:
                icon_src = find_file(squashfs_root, ext)
                if icon_src and icon_filename in os.path.basename(icon_src):
                    break

            icon_target_dir = secure_mkdir(os.path.join(HOME, ".local", "share", "icons"))
            icon_target = os.path.join(icon_target_dir, f"{app_name}.png")
            if icon_src:
                shutil.copy(icon_src, icon_target)
                os.chmod(icon_target, 0o644)
            else:
                print(_("icon_not_found"))

            # Desktop dosyasını oluştur
            desktop_dir = secure_mkdir(os.path.join(HOME, ".local", "share", "applications"))
            desktop_target = os.path.join(desktop_dir, f"{app_name}.desktop")

            exec_command = appimage_target
            if not sandbox:
                exec_command = f"{appimage_target} --no-sandbox"

            desktop_content = f"""[Desktop Entry]
Type=Application
Name={data['Name']}
Comment={data['Comment']}
Exec={exec_command}
Icon={icon_target if icon_src else data['Icon']}
Terminal=false
Categories={data['Categories']};
"""
            secure_write(desktop_target, desktop_content)
            os.chmod(desktop_target, 0o644)

            subprocess.run(["update-desktop-database", desktop_dir], check=True)

            print(_("installation_complete", name=data["Name"]))
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        raise ValueError(str(e))

def uninstall_app(app_name):
    """Güvenli bir şekilde uygulamayı kaldırır."""
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
                raise ValueError(_("error_desktop"))

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

            subprocess.run(["update-desktop-database", os.path.join(HOME, ".local", "share", "applications")], check=True)
            print(_("uninstall_complete"))
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        raise ValueError(str(e))

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
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-L", "--lang", default="en")
    args, remaining = pre_parser.parse_known_args()

    # Load language
    load_language(args.lang)

    # Create main parser
    parser = argparse.ArgumentParser(description="AppImage Installer")
    parser.add_argument("-i", "--install", help=_("help_install"))
    parser.add_argument("-u", "--uninstall", help=_("help_uninstall"))
    parser.add_argument("-l", "--list", action="store_true", help=_("help_list"))
    parser.add_argument("-s", "--sandbox", action="store_true", help=_("help_sandbox"))
    parser.add_argument("-L", "--lang", help=_("help_lang"), default="en")
    parser.add_argument("-v", "--version", action="store_true", help=_("help_version"))
    parser.add_argument("-c", "--clean", action="store_true", help=_("help_clean"))
    parser.add_argument("--report-translations", action="store_true", help=_("help_report_translations"))

    args = parser.parse_args()

    try:
        if args.version:
            print(_("version_info", version=get_version()))
            return

        if args.install:
            install_appimage(args.install, not args.sandbox)
        elif args.uninstall:
            uninstall_app(args.uninstall)
        elif args.list:
            list_installed_apps()
        elif args.report_translations:
            report_missing_translations()
        else:
            parser.print_help()

    except Exception as e:
        print(_("error", message=str(e)))
        sys.exit(1)

if __name__ == "__main__":
    main()
