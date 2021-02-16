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


import sys
import shutil
from setuptools import setup, find_packages

from pigeonplanner.core import const


if sys.version_info.major != 3:
    print("Only Python 3 is supported, your version is: %s" % sys.version)
    sys.exit()

dependencies = [dep.strip("\n'") for dep in open("requirements.txt").readlines()]

package_data = {
    "pigeonplanner": [
        "data/images/*.png",
        "data/images/pigeonplanner.svg",
        "data/languages/*/LC_MESSAGES/pigeonplanner.mo",
        "resultparsers/*.py",
        "resultparsers/*.yapsy-plugin",
    ],
    "pigeonplanner.ui": [
        "glade/*.ui",
        "data/*.css"
    ]
}

data_files = []
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
    download_url="https://www.pigeonplanner.com/download",
    license="GPLv3",
    url=const.WEBSITE,
    packages=find_packages(exclude=["tests"]),
    package_data=package_data,
    data_files=data_files,
    install_requires=dependencies,
    entry_points=entry_points,
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)

# Remove egg-info directory which is no longer needed
try:
    shutil.rmtree("pigeonplanner.egg-info")
except:
    pass
