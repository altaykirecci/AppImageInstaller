import os
import shutil
import subprocess
import tempfile
import argparse
from configparser import ConfigParser

HOME = os.path.expanduser("~")

def extract_appimage(appimage_path, extract_dir):
    subprocess.run([appimage_path, "--appimage-extract"], cwd=extract_dir, check=True)
    return os.path.join(extract_dir, "squashfs-root")

def find_file(root, extension):
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(extension):
                return os.path.join(dirpath, f)
    return None

def parse_desktop_file(path):
    parser = ConfigParser(strict=False, interpolation=None)
    parser.read(path)
    entry = parser["Desktop Entry"]
    return {
        "Name": entry.get("Name", ""),
        "Comment": entry.get("Comment", ""),
        "Categories": entry.get("Categories", ""),
        "Exec": entry.get("Exec", ""),
        "Icon": entry.get("Icon", "")
    }

def slugify(name):
    return name.lower().replace(" ", "_")

def install_appimage(appimage_path, sandbox=True):
    print("AppImage kuruluyor...")
    os.chmod(appimage_path, os.stat(appimage_path).st_mode | 0o111)

    temp_dir = tempfile.mkdtemp()
    try:
        squashfs_root = extract_appimage(appimage_path, temp_dir)
        desktop_src = find_file(squashfs_root, ".desktop")
        if not desktop_src:
            print("HATA: .desktop dosyası bulunamadı.")
            return

        data = parse_desktop_file(desktop_src)
        app_name = slugify(data["Name"])

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
            print("İkon bulunamadı, masaüstü simgesi olmayabilir.")

        desktop_dir = os.path.join(HOME, ".local", "share", "applications")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_target = os.path.join(desktop_dir, f"{app_name}.desktop")

        # Eğer --sandbox bayrağı verilmişse, Exec satırına ekliyoruz.
        exec_command = appimage_target
        if  sandbox:
            exec_command = f"{appimage_target} --no-sandbox"

        # .desktop dosyasını burada oluşturuyoruz:
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

        # Veritabanını güncelle
        subprocess.run(["update-desktop-database", desktop_dir])

        print(f"Kurulum tamamlandı: {data['Name']}")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        shutil.rmtree(temp_dir)

def uninstall_app(app_name):
    app_name = slugify(app_name)
    print(f"{app_name} kaldırılıyor...")

    appimage_path = os.path.join(HOME, ".local", "bin", f"{app_name}.AppImage")
    if not os.path.exists(appimage_path):
        print(f"AppImage bulunamadı: {appimage_path}")
        return

    # Extract AppImage to get the actual application name
    temp_dir = tempfile.mkdtemp()
    try:
        squashfs_root = extract_appimage(appimage_path, temp_dir)
        desktop_src = find_file(squashfs_root, ".desktop")
        if not desktop_src:
            print("HATA: .desktop dosyası bulunamadı.")
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
                print(f"{key} silindi: {path}")
            else:
                print(f"{key} bulunamadı: {path}")

        subprocess.run(["update-desktop-database", os.path.join(HOME, ".local", "share", "applications")])
        print("Kaldırma işlemi tamamlandı.")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description="AppImage Kurulum/Kaldırma Aracı")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--install", metavar="PATH", help="AppImage dosyasının tam yolu")
    group.add_argument("-u", "--uninstall", metavar="NAME", help="Kaldırılacak uygulamanın adı (örnek: firefox)")
    parser.add_argument("--sandbox", action="store_true", help="AppImage için sandbox özelliğini devre dışı bırak")

    args = parser.parse_args()

    if args.install:
        if not os.path.isfile(args.install):
            print("Geçerli bir AppImage dosyası girilmedi.")
            return
        install_appimage(args.install, sandbox=args.sandbox)
    elif args.uninstall:
        uninstall_app(args.uninstall)

if __name__ == "__main__":
    main()
