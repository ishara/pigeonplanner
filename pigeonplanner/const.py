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


import os
import sys
import tempfile

import pigeonplanner


NAME = pigeonplanner.name
VERSION = pigeonplanner.version
AUTHORS = pigeonplanner.authors
WEBSITE = pigeonplanner.website
COPYRIGHT = pigeonplanner.copyright
DESCRIPTION = pigeonplanner.description
LICENSE = pigeonplanner.license


if sys.platform.startswith("win"):
    HOMEDIR = os.environ['USERPROFILE'] 
    if os.environ.has_key('APPDATA'):
        PREFDIR = os.path.join(os.environ['APPDATA'], 'pigeonplanner')
    else:
        PREFDIR = os.path.join(HOMEDIR, 'pigeonplanner')
    GLADEDIR = './glade/'
    IMAGEDIR = './images/'
else:
    HOMEDIR = os.environ['HOME']
    PREFDIR = os.path.join(HOMEDIR, '.pigeonplanner')
    topPath = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    if topPath.startswith('/usr'):
        GLADEDIR = '/usr/share/pigeonplanner/glade/'
        IMAGEDIR = '/usr/share/pigeonplanner/images/'
    else:
        GLADEDIR = os.path.join(topPath, 'glade')
        IMAGEDIR = os.path.join(topPath, 'images')

TEMPDIR = tempfile.gettempdir()

GLADEMAIN = os.path.join(GLADEDIR, "MainWindow.glade")
GLADELOG = os.path.join(GLADEDIR, "LogDialog.glade")
GLADEOPTIONS = os.path.join(GLADEDIR, "OptionsDialog.glade")
GLADEPEDIGREE = os.path.join(GLADEDIR, "PedigreeWindow.glade")
GLADERESULT = os.path.join(GLADEDIR, "ResultWindow.glade")
GLADETOOLS = os.path.join(GLADEDIR, "ToolsWindow.glade")
GLADEASSIST = os.path.join(GLADEDIR, "DBAssistant.glade")

DATABASE = os.path.join(PREFDIR, 'pigeonplanner.db')
LOGFILE = os.path.join(PREFDIR, 'pigeonplanner.log')

UPDATEURL = 'http://www.pigeonplanner.com/CURRENT'
DOWNLOADURL = 'http://www.pigeonplanner.com/download'
FORUMURL = 'https://sourceforge.net/apps/phpbb/pigeonplanner/'
