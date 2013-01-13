#!/usr/bin/env python
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
import glob
from distutils.core import setup

import i18n
from pigeonplanner import const


# Common data files
glade_files = glob.glob('glade/*.ui')
glade_files.extend(['glade/pigeonplannerwidgets.py', 'glade/pigeonplannerwidgets.xml'])
data_files = [
            ('share/applications', ['data/pigeonplanner.desktop']),
            ('share/icons/hicolor/scalable/apps', ['images/pigeonplanner.svg']),
            ('share/pixmaps/', ['images/pigeonplanner.png']),
            ('share/pigeonplanner/glade', glade_files),
            ('share/pigeonplanner/images', glob.glob('images/*.png')),
        ]

# Find all packages
packages = []
for folder, subfolders, files in os.walk('pigeonplanner'):
    if '__init__.py' in files:
        # It's only a package when it contains a __init__.py file
        packages.append(folder)

# Compile translation files
i18n.create_mo()
# Search for the translation files
translation_files = []
for mofile in glob.glob('languages/*/LC_MESSAGES/pigeonplanner.mo'):
    _, lang, _ = mofile.split('/', 2)

    modir = os.path.dirname(mofile).replace('languages', 'share/locale')
    translation_files.append((modir, [mofile]))

def run_setup():
    setup(name = 'pigeonplanner',
          version = const.VERSION,
          description = const.DESCRIPTION,
          long_description = """
                Pigeon Planner is a pigeon organiser which lets the user 
                manage their pigeons with their details, pedigree, 
                results and more.""",
          author = "Timo Vanwynsberghe",
          author_email = "timovwb@gmail.com",
          download_url = "http://www.pigeonplanner.com/download",
          license = "GPLv3",
          url = const.WEBSITE,
          packages = packages,
          scripts = ["bin/pigeonplanner", "bin/pigeonplanner-db"],
          data_files = data_files + translation_files,
        )

if __name__ == '__main__':
    run_setup()

