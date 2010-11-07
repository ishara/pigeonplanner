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
Definies all constants
"""


import os
import sys
import tempfile

import gtk.gdk

import pigeonplanner


NAME = pigeonplanner.name
VERSION = pigeonplanner.version
AUTHORS = pigeonplanner.authors
ARTISTS = pigeonplanner.artists
WEBSITE = pigeonplanner.website
COPYRIGHT = pigeonplanner.copyright
DESCRIPTION = pigeonplanner.description
LICENSE = pigeonplanner.license


DATABASE_VERSION = 3


SMALL_SCREEN = False
if gtk.gdk.screen_height() <= 768:
    SMALL_SCREEN = True


ENCODING = sys.getfilesystemencoding() or 'utf-8'


UNIX = False
WINDOWS = False
OSX = False
if sys.platform.startswith("win"):
	WINDOWS = True
elif "darwin" in sys.platform:
	OSX = True
else:
	UNIX = True


if WINDOWS:
    HOMEDIR = os.environ['USERPROFILE'] 
    if os.environ.has_key('APPDATA'):
        PREFDIR = os.path.join(os.environ['APPDATA'], 'pigeonplanner')
    else:
        PREFDIR = os.path.join(HOMEDIR, 'pigeonplanner')
    GLADEDIR = './glade/'
    IMAGEDIR = './images/'
    LANGDIR = './languages/'
else:
    HOMEDIR = os.environ['HOME']
    PREFDIR = os.path.join(HOMEDIR, '.pigeonplanner')
    topPath = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    if topPath.startswith('/usr'):
        GLADEDIR = '/usr/share/pigeonplanner/glade/'
        IMAGEDIR = '/usr/share/pigeonplanner/images/'
        LANGDIR = '/usr/share/locale/'
    else:
        GLADEDIR = os.path.join(topPath, 'glade')
        IMAGEDIR = os.path.join(topPath, 'images')
        LANGDIR = os.path.join(topPath, 'languages')

TEMPDIR = tempfile.gettempdir()

GLADEMAIN = os.path.join(GLADEDIR, "MainWindow.ui")
GLADEOPTIONS = os.path.join(GLADEDIR, "OptionsDialog.ui")
GLADEPEDIGREE = os.path.join(GLADEDIR, "PedigreeWindow.ui")
GLADERESULT = os.path.join(GLADEDIR, "ResultWindow.ui")
GLADETOOLS = os.path.join(GLADEDIR, "ToolsWindow.ui")
GLADEPREVIEW = os.path.join(GLADEDIR, "PreviewWindow.ui")
GLADEPHOTOALBUM = os.path.join(GLADEDIR, "PhotoAlbum.ui")
GLADEDIALOGS = os.path.join(GLADEDIR, "Dialogs.ui")

DATABASE = os.path.join(PREFDIR, 'pigeonplanner.db')
LOGFILE = os.path.join(PREFDIR, 'pigeonplanner.log')
THUMBDIR = os.path.join(PREFDIR, 'thumbs')

UPDATEURL = 'http://www.pigeonplanner.com/CURRENT'
DOWNLOADURL = 'http://www.pigeonplanner.com/download'
FORUMURL = 'http://forum.pigeonplanner.com'
MAILURL = "http://www.pigeonplanner.com/cgi-bin/pigeonplanner_mailing.py"
REPORTMAIL = "timovwb@gmail.com"

DOMAIN = 'pigeonplanner'

USER_AGENT = {"User-Agent": "Pigeon Planner/%s" %VERSION}

LOG_FORMAT = '[%(asctime)s] %(name)s %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d'

(SIRE,
 DAM,
 YOUNG) = range(3)

(ADD,
 EDIT) = range(2)

(DEAD,
 ACTIVE,
 SOLD,
 LOST) = range(4)

(ERROR,
 WARNING,
 QUESTION,
 INFO) = range(4)
