# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import glob
import shutil
sys.path.insert(0, os.path.abspath(".."))

from pigeonplanner.core import const

print("Updating version_file.py")
with open("version_file.py.in") as version_file_in:
    version_file_template = version_file_in.read().format(
        name=const.NAME,
        version=const.VERSION,
        version_tuple=const.VERSION_TUPLE+(0,),  # Requires a 4-tuple
        description=const.DESCRIPTION,
        copyright=const.COPYRIGHT
    )
with open("version_file.py", "w") as version_file_out:
    version_file_out.write(version_file_template)


block_cipher = None

# noinspection PyUnresolvedReferences
a = Analysis(
    ["../pigeonplanner/main.py"],
    pathex=["../"],
    binaries=[],
    datas=[
        ("../pigeonplanner/ui/data/style.css", "share/pigeonplanner"),
        ("../pigeonplanner/ui/glade/*.ui", "share/pigeonplanner/glade"),
        ("../pigeonplanner/data/images/*.png", "share/pigeonplanner/images"),
        ("../pigeonplanner/data/images/pigeonplanner.svg", "share/pigeonplanner/images"),
        ("../pigeonplanner/data/languages/", "share/pigeonplanner/languages"),
        ("../pigeonplanner/resultparsers/*.py", "share/pigeonplanner/resultparsers"),
        ("../pigeonplanner/resultparsers/*.yapsy-plugin", "share/pigeonplanner/resultparsers"),
        ("../pigeonplanner/database/migrations/*.py", "share/pigeonplanner/migrations"),
        ("../AUTHORS", "."),
        ("../CHANGES", "."),
        ("../COPYING", "."),
        ("../README", ".")
    ],
    hiddenimports=[
        "playhouse",
        "playhouse.migrate",
        "packaging",
        "packaging.version",
        "packaging.specifiers",
        "packaging.requirements"
    ],
    hookspath=["."],
    runtime_hooks=["pyinstaller_add_lib_dir.py"],
    excludes=["lib2to3", "tcl", "tk", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# noinspection PyUnresolvedReferences
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# noinspection PyUnresolvedReferences
exe = EXE(
    pyz,
    a.scripts,
    options=[],
    exclude_binaries=True,
    name="pigeonplanner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    version="version_file.py",
    icon="pigeonplanner.ico",
    console=False
)

# noinspection PyUnresolvedReferences
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="pigeonplanner"
)

print("Cleaning up dist directory...")

orig_working_dir = os.getcwd()
os.chdir("dist/pigeonplanner/")

# With the added runtime hook above, we can move a bunch of stuff inside the
# lib directory. There are however a few DLLs that need to stay in the root.
dlls_to_keep = [
    "_struct-cpython-38.dll",
    "libpython3.8.dll",
    "libwinpthread-1.dll",
    "zlib1.dll",
    "zlib-cpython-38.dll",
]
dlls = glob.glob("*.dll")
for dll in dlls:
    if dll not in dlls_to_keep:
        shutil.move(dll, "lib/")

shutil.move("gi/", "lib/")

# These directories and files inside are not required.
shutil.rmtree("lib/python3.8/")
shutil.rmtree("share/themes/")
shutil.rmtree("include/")

# Remove all GTK/GLib translations we don't support ourselves.
supported_languages = os.listdir("share/pigeonplanner/languages/")
installed_languages = os.listdir("share/locale/")
for lang in installed_languages:
    if lang not in supported_languages:
        shutil.rmtree("share/locale/" + lang)

# TODO: clean up some icons/cursors we don't use

# This file is executed by PyInstaller. Change the working directory back to
# where we started just to be sure PyInstaller continues correctly.
os.chdir(orig_working_dir)
