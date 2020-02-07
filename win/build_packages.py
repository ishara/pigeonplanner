
import os
import sys
import zipfile
import argparse
import subprocess

sys.path.insert(0, os.path.abspath(".."))
from pigeonplanner.core.const import VERSION


def build_executable():
    if os.path.exists("dist\\pigeonplanner"):
        print("dist directory already exists, skip building executable.")
        return
    print("Building executable...")
    subprocess.call(["pyinstaller", "pigeonplanner.spec"])


def build_installer():
    print("Building installer...")
    iss_compiler = "C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"
    subprocess.call([iss_compiler, "setup.iss"])


def build_zip():
    print("Building zip file...")
    package_root = "dist\\pigeonplanner"
    ziproot = "Pigeon Planner %s" % VERSION
    zfile = zipfile.ZipFile("pigeonplanner-%s-win32.zip" % VERSION, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(package_root):
        for file in files:
            filepath = os.path.join(root, file)
            zfile.write(filepath, filepath.replace("dist\\pigeonplanner", ziproot))
    zfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--executable", help="Build the executable", action="store_true")
    parser.add_argument("-z", "--zip", help="Create a zipfile", action="store_true")
    parser.add_argument("-i", "--installer", help="Create an installer", action="store_true")
    parser.add_argument("-a", "--all", help="Create a zipfile and an installer", action="store_true")
    args = parser.parse_args()
    if args.executable:
        build_executable()
    if args.zip:
        build_executable()
        build_zip()
    if args.installer:
        build_executable()
        build_installer()
    if args.all:
        build_executable()
        build_zip()
        build_installer()
