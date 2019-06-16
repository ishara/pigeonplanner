
import os
import sys
import glob
import shutil
import zipfile
import subprocess

sys.path.insert(0, os.path.abspath("."))
from pigeonplanner.core.const import VERSION


package_root = "dist"
if not os.path.exists(package_root):
    print("Dist directory not found. Did you py2exe'd?")
    sys.exit()

python_root = os.path.dirname(sys.executable)
gtk_root = os.path.join(python_root, "Lib", "site-packages", "gtk-2.0", "runtime")


def copy_files():
    # Copy the required theme files
    theme_files = [
        ("etc\\gtk-2.0", "gtkrc"),
        ("lib\\gtk-2.0\\2.10.0\\engines", "libclearlooks.dll"),
    ]
    for theme_path, theme_file in theme_files:
        dist_theme_path = os.path.join(package_root, theme_path)
        if not os.path.exists(dist_theme_path):
            os.makedirs(dist_theme_path)
        shutil.copyfile(
            os.path.join(gtk_root, theme_path, theme_file),
            os.path.join(dist_theme_path, theme_file)
        )

    # Only copy GTK+ translations for the languages used inside Pigeon Planner
    # TODO: only copy gtk20.mo?
    langs = os.listdir(os.path.join(package_root, "languages"))
    for lang in langs:
        try:
            shutil.copytree(
                os.path.join(gtk_root, "share", "locale", lang),
                os.path.join(package_root, "share", "locale", lang)
            )
        except WindowsError:
            pass

    # Copy intl.dll from GTK+ to avoid problems
    shutil.copy(
        os.path.join(gtk_root, "bin", "intl.dll"),
        os.path.join(package_root, "lib")
    )

    # Find the mvcr90.dll and approriate manifest
    # TODO: This only works on Windows XP probably
    dll_version = "9.0.21022.8"
    dlls_dir = "C:\\WINDOWS\\WinSxS"
    manifests_dir = os.path.join(dlls_dir, "Manifests")

    for manifest in glob.glob(manifests_dir + "*.manifest"):
        if "Microsoft.VC90.CRT" in manifest and dll_version in manifest:
            shutil.copy(manifest, os.path.join(package_root, "Microsoft.VC90.CRT.manifest"))
            break
    for dll_dir in os.listdir(dlls_dir):
        if "Microsoft.VC90.CRT" in dll_dir and dll_version in dll_dir:
            dll = os.path.join(dlls_dir, dll_dir, "msvcr90.dll")
            shutil.copy(dll, package_root)
            break


def build_installer():
    iss_compiler = "C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"
    subprocess.call([iss_compiler, "win\\setup.iss"])


def build_zip():
    ziproot = "Pigeon Planner %s" % VERSION
    zfile = zipfile.ZipFile("win\\pigeonplanner-%s-win32.zip" % VERSION, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(package_root):
        for file in files:
            filepath = os.path.join(root, file)
            zfile.write(filepath, filepath.replace("dist", ziproot))
    zfile.close()


if __name__ == "__main__":
    if "-c" in sys.argv or "--copy" in sys.argv:
        copy_files()
    elif "-z" in sys.argv or "--zip" in sys.argv:
        copy_files()
        build_zip()
    else:
        copy_files()
        build_zip()
        build_installer()
    print "Done!"
