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

import PigeonPlanner


NAME = PigeonPlanner.name
VERSION = PigeonPlanner.version
AUTHORS = PigeonPlanner.authors
WEBSITE = PigeonPlanner.website
COPYRIGHT = PigeonPlanner.copyright
DESCRIPTION = _(PigeonPlanner.description)
LICENSE = PigeonPlanner.license


if sys.platform == 'win32':
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
    currentPath = os.path.abspath(os.path.dirname(__file__))
    if currentPath.startswith('/usr'):
        GLADEDIR = '/usr/share/pigeonplanner/glade/'
        IMAGEDIR = '/usr/share/pigeonplanner/images/'
    else:
        GLADEDIR = './glade/'
        IMAGEDIR = './images/'

DATABASE = os.path.join(PREFDIR, 'pigeonplanner.db')
UPDATEURL = 'http://pigeonplanner.sourceforge.net/CURRENT'
DOWNLOADURL = 'http://pigeonplanner.sourceforge.net/download.html'

MSG_INVALID_IMAGE = _("This image is either not supported or corrupt, please choose another one.")
MSG_IMAGE_MISSING = _("Error loading this image. Probably you have moved it on your disk.")

MSG_SHOW_PIGEON = _("This pigeon already exists, but isn't showing. Do you want to show it again?")
MSG_OVERWRITE_PIGEON = _("This pigeon already exists. Overwrite it?")
MSG_ADD_PIGEON = _("This pigeon doesn't exist. Do you want to add it?")

MSG_EMPTY_FIELDS = _("The ringnumber and year of the %s are necessary.\n\nCheck if these are entered.")
MSG_INVALID_NUMBER = _("Incorrect input of the year of the %s.\n\nOnly numbers are accepted.")
MSG_INVALID_LENGTH = _("Incorrect input of the year of the %s.\n\nCheck the length.")

MSG_EMPTY_DATA = _("All fields have to be entered.")
MSG_INVALID_FORMAT = _("The date you entered has the wrong format. It should be ISO-format (YYYY-MM-DD).")
MSG_RESULT_EXISTS = _("The result you want to add already exists.")

MSG_BACKUP_SUCCES = _("The backup was successfully created.")
MSG_RESTORE_SUCCES = _("The backup was successfully restored.\nRestart the program.")

MSG_DEFAULT_OPTIONS = _("This will set back all the settings to the default values.\nAre you sure?")

MSG_NO_INFO = _("You have not entered your personal information.\nThis will be shown on top of the printed pedigree.\nDo you want to add it now?")

MSG_PRINT_ERROR = _("Error printing the pedigree")

MSG_UPDATE_ERROR = _("Error trying to get information. Are you connected to the internet?")
MSG_UPDATE_AVAILABLE = _("A new version is available. Please go to the Pigeon Planner website by clicking the link below and download the latest version")
MSG_NO_UPDATE = _("You already have the latest version installed.")
MSG_UPDATE_DEVELOPMENT = _("This isn't normal, or you must be running a development version")

MSG_REMOVE_ITEM = _("Removing item '%(item)s' from '%(dataset)s'.\n\nAre you sure?")
