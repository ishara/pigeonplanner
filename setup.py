#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Pigeon Planner is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Pigeon Planner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Pigeon Planner.  If not, see <http://www.gnu.org/licenses/>


"""
This is the Pigeon Planner setup script
"""

import os
import sys
import glob
import shutil
from setuptools import setup, find_packages

from pigeonplanner.core import const


if sys.version_info.major != 3:
    print("Only Python 3 is supported, your version is: %s" % sys.version)
    sys.exit()

data_files = []
package_data = {}

if const.WINDOWS:
    import py2exe

    translation_files = []
    for mofile in glob.glob("pigeonplanner/data/languages/*/LC_MESSAGES/pigeonplanner.mo"):
        _, _, modir = os.path.dirname(mofile).split("/", 2)
        translation_files.append((modir, [mofile]))

    data_files = [
        ("glade", glob.glob("pigeonplanner/ui/glade/*.ui")),
        ("images", glob.glob("pigeonplanner/data/images/*.png")),
        ("resultparsers", glob.glob("pigeonplanner/resultparsers/*.py")),
        ("resultparsers", glob.glob("pigeonplanner/resultparsers/*.yapsy-plugin")),
        (".", ["AUTHORS", "CHANGES", "COPYING", "README", "README.dev"])
    ]
    data_files.extend(translation_files)

    platform_options = {
        "options": {
            "py2exe": {
                "dist_dir": "dist",
                "compressed": 2,
                "optimize": 2,
                "bundle_files": 3,
                "xref": False,
                "skip_archive": False,
                "ascii": False,
                "packages": ["encodings", "pigeonplanner"],
                "includes": ["atk", "cairo", "gio", "gobject", "pango", "pangocairo"],
                "excludes": [
                    "_gtkagg", "_tkagg", "bsddb", "curses", "email", "pywin.debugger",
                    "pywin.debugger.dbgcon", "pywin.dialogs", "tcl", "Tkconstants", "Tkinter"
                ],
                "dll_excludes": [
                    "tcl84.dll", "tk84.dll", "w9xpopen.exe", "MSVCP90.dll", "IPHLPAPI.dll",
                    "NSI.dll", "WINNSI.dll", "WTSAPI32.dll", "SHFOLDER.dll", "PSAPI.dll",
                    "MSVCR120.dll", "MSVCP120.dll", "CRYPT32.dll", "GDI32.dll", "ADVAPI32.dll",
                    "CFGMGR32.dll", "USER32.dll", "POWRPROF.dll", "MSIMG32.dll", "WINSTA.dll",
                    "MSVCR90.dll", "KERNEL32.dll", "MPR.dll", "Secur32.dll",
                ],
            }
        },
        "zipfile": r"lib/library.zip",
        "windows": [
            {"script": "pigeonplanner.py", "icon_resources": [(1, "win/pigeonplanner.ico")]}
        ]
    }
else:
    dependencies = [dep.strip("\n'") for dep in open("requirements.txt").readlines()]
    platform_options = {
        "install_requires": dependencies,
    }
    package_data = {
        "pigeonplanner": [
            "data/images/*.png",
            "data/languages/*/LC_MESSAGES/pigeonplanner.mo",
            "resultparsers/*.py",
            "resultparsers/*.yapsy-plugin",
        ],
        "pigeonplanner.ui": [
            "glade/*.ui"
        ]
    }

if const.UNIX:
    data_files = [
        ("share/applications", ["data/pigeonplanner.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["pigeonplanner/data/images/pigeonplanner.svg"]),
        ("share/pixmaps/", ["pigeonplanner/data/images/pigeonplanner.png"]),
    ]

entry_points = {
    "gui_scripts": [
        "pigeonplanner = pigeonplanner.main:run"
    ]
}

setup(
    name="pigeonplanner",
    version=const.VERSION,
    description=const.DESCRIPTION,
    long_description=(
        "Pigeon Planner is a pigeon organiser which lets the user " 
        "manage their pigeons with their details, pedigree, results and more."
    ),
    author="Timo Vanwynsberghe",
    author_email="timovwb@gmail.com",
    download_url="http://www.pigeonplanner.com/download",
    license="GPLv3",
    url=const.WEBSITE,
    packages=find_packages(exclude=["tests"]),
    package_data=package_data,
    data_files=data_files,
    entry_points=entry_points,
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    **platform_options
)

# Remove egg-info directory which is no longer needed
try:
    shutil.rmtree("pigeonplanner.egg-info")
except:
    pass
