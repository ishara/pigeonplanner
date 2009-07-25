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
FORUMURL = 'https://sourceforge.net/apps/phpbb/pigeonplanner/'

MSG_INVALID_IMAGE = (_("Invalid image!"),
                     _("This image is either not supported or corrupt, please choose another one."),
                     _("Error"))
MSG_IMAGE_MISSING = (_("Loading image failed!"),
                     _("Maybe you have renamed the image or moved it on your disk."),
                     _("Error"))

MSG_SHOW_PIGEON = (_("This pigeon already exists, but isn't showing. Do you want to show it again?"),
                   None,
                   _("Warning"))
MSG_OVERWRITE_PIGEON = (_("This pigeon already exists. Overwrite it?"),
                        None,
                        _("Warning"))
MSG_ADD_PIGEON = (_("This pigeon doesn't exist. Do you want to add it?"),
                  None,
                  _("Adding pigeon"))

MSG_EMPTY_FIELDS = (_("Invalid input!"),
                    _("The ringnumber and year are necessary."),
                    _("Error"))
MSG_INVALID_NUMBER = (_("Invalid input!"),
                      _("Only numbers are accepted as year input."),
                      _("Error"))
MSG_INVALID_LENGTH = (_("Invalid input!"),
                      _("Check the length of the year."),
                      _("Error"))
MSG_INVALID_RANGE = (_("Invalid input!"),
                     _("Only numbers are allowed when adding multiple pigeons."),
                     _("Error"))

MSG_EMPTY_DATA = (_("Invalid input!"),
                  _("All fields have to be entered."),
                  _("Error"))
MSG_INVALID_FORMAT = (_("Invalid input!"),
                      _("The date you entered has the wrong format. It should be ISO-format (YYYY-MM-DD)."),
                      _("Error"))
MSG_RESULT_EXISTS = (_("Invalid input!"),
                     _("The result you want to add already exists."),
                     _("Error"))

MSG_BACKUP_SUCCES = (_("The backup was successfully created."),
                     None,
                     _("Completed!"))
MSG_RESTORE_SUCCES = (_("The backup was successfully restored.\nRestart the program."),
                      None,
                      _("Completed!"))

MSG_NO_INFO = (_("No personal information found."),
               _("This will be shown on top of the printed pedigree.\nDo you want to add it now?"),
               _("Personal"))

MSG_PRINT_ERROR = (_("Error printing the pedigree"),
                   None,
                   _("Error"))

MSG_DEFAULT_OPTIONS = (_("This will set back all the settings to the default values.\nAre you sure?"),
                       None,
                       _("Default settings"))

MSG_REMOVE_ITEM = (_("Removing item '%(item)s' from '%(dataset)s'.\n\nAre you sure?"),
                   None,
                   _("Remove data"))

MSG_UPDATE_ERROR = _("Error trying to get information. Are you connected to the internet?")
MSG_UPDATE_AVAILABLE = _("A new version is available. Please go to the Pigeon Planner website by clicking the link below and download the latest version")
MSG_NO_UPDATE = _("You already have the latest version installed.")
MSG_UPDATE_DEVELOPMENT = _("This isn't normal, or you must be running a development version")

