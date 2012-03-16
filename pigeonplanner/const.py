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
from datetime import datetime


NAME = "Pigeon Planner"
VERSION = "1.6.1"
COPYRIGHT = "(C)opyright 2009-%s Timo Vanwynsberghe" % datetime.now().year
AUTHORS = ["Timo Vanwynsberghe <timovwb@gmail.com>"]
ARTISTS = ["Timo Vanwynsberghe <timovwb@gmail.com>",
           "http://www.openclipart.org"]
WEBSITE = "http://www.pigeonplanner.com"
DESCRIPTION = "Organise and manage your pigeons"
LICENSE = """
Pigeon Planner is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pigeon Planner is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pigeon Planner.  If not, see <http://www.gnu.org/licenses/>"""


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
    PREFDIR = os.path.join(os.environ.get('APPDATA', HOMEDIR), 'pigeonplanner')
    PREFDIR = unicode(PREFDIR, sys.getfilesystemencoding())
    HOMEDIR = unicode(HOMEDIR, sys.getfilesystemencoding())
else:
    HOMEDIR = os.environ['HOME']
    PREFDIR = os.path.join(HOMEDIR, '.pigeonplanner')

#XXX: For some reason, GtkBuilder translations on Windows don't work when
#     building the languages folder path from the ROOTDIR.
#     Looks like a unicode problem:
#           * os.path.join(ROOTDIR, 'languages') => unicode, doesn't work
#           * os.path.abspath(u'languages') => unicode, doesn't work
#           * os.path.abspath('languages') => str, does work
if hasattr(sys, "frozen"):
    ROOTDIR = os.path.abspath(os.path.dirname(
                unicode(sys.executable, sys.getfilesystemencoding())))
    LANGDIR = os.path.abspath('languages')
else:
    ROOTDIR = os.path.abspath(os.path.dirname(
                unicode(__file__, sys.getfilesystemencoding())))
    if not ROOTDIR.startswith('/usr'):
        # When running from the source folder, the root is one dir up
        ROOTDIR = os.path.normpath(os.path.join(ROOTDIR, '..'))
        LANGDIR = os.path.join(ROOTDIR, 'languages')
        if WINDOWS:
            LANGDIR = os.path.abspath('../languages')
    else:
        # Running the installed program, use the system's locale dir
        LANGDIR = '/usr/share/locale/'

IMAGEDIR = os.path.join(ROOTDIR, 'images')
GLADEDIR = os.path.join(ROOTDIR, 'glade')
THUMBDIR = os.path.join(PREFDIR, u'thumbs')
DATABASE = os.path.join(PREFDIR, u'pigeonplanner.db')
LOGFILE = os.path.join(PREFDIR, u'pigeonplanner.log')

TEMPDIR = tempfile.gettempdir()

UPDATEURL = 'http://www.pigeonplanner.com/CURRENT'
DOWNLOADURL = 'http://www.pigeonplanner.com/download'
FORUMURL = 'http://forum.pigeonplanner.com'
MAILURL = "http://www.pigeonplanner.com/cgi-bin/pigeonplanner_mailing.py"
REPORTMAIL = "timovwb@gmail.com"
DOCURL = WEBSITE + "/index.php?option=com_content&view=article&catid=9&id=%s"
DOCURLMAIN = WEBSITE + "/support/documentation"

DOMAIN = 'pigeonplanner'

USER_AGENT = {"User-Agent": "Pigeon Planner/%s" % VERSION}

LOG_FORMAT = '[%(asctime)s] %(name)s %(levelname)s: %(message)s'
LOG_FORMAT_CLI = '%(name)s %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d'

LOGO_IMG = os.path.join(IMAGEDIR, 'icon_logo.png')
SEX_IMGS = {'0': os.path.join(IMAGEDIR, "symbol_male.png"),
            '1': os.path.join(IMAGEDIR, "symbol_female.png"),
            '2': os.path.join(IMAGEDIR, "symbol_young.png")}

(SIRE,
 DAM,
 YOUNG) = range(3)

(ADD,
 EDIT) = range(2)

(CREATE,
 RESTORE) = range(2)

(DEAD,
 ACTIVE,
 SOLD,
 LOST,
 BREEDER,
 LOANED) = range(6)

(ERROR,
 WARNING,
 QUESTION,
 INFO) = range(4)

(PRINT,
 PREVIEW,
 MAIL,
 SAVE) = range(4)

