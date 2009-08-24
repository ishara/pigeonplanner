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
import locale

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
    currentPath = os.path.abspath(os.path.dirname(__file__))
    if currentPath.startswith('/usr'):
        GLADEDIR = '/usr/share/pigeonplanner/glade/'
        IMAGEDIR = '/usr/share/pigeonplanner/images/'
    else:
        GLADEDIR = './glade/'
        IMAGEDIR = './images/'

GLADEMAIN = os.path.join(GLADEDIR, "MainWindow.glade")
GLADEOPTIONS = os.path.join(GLADEDIR, "OptionsDialog.glade")
GLADEPEDIGREE = os.path.join(GLADEDIR, "PedigreeWindow.glade")
GLADERESULT = os.path.join(GLADEDIR, "ResultWindow.glade")
GLADETOOLS = os.path.join(GLADEDIR, "ToolsWindow.glade")

DATABASE = os.path.join(PREFDIR, 'pigeonplanner.db')
UPDATEURL = 'http://pigeonplanner.sourceforge.net/CURRENT'
FORUMURL = 'https://sourceforge.net/apps/phpbb/pigeonplanner/'

if locale.getlocale()[0][:2]:
    DOWNLOADURL = 'http://pigeonplanner.sourceforge.net/nl/download.html'
else:
    DOWNLOADURL = 'http://pigeonplanner.sourceforge.net/en/download.html'

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
MSG_REMOVE_RESULT = (_("Removing the selected result"),
                     _("Are you sure?"),
                     _("Remove result"))

MSG_NAME_EMPTY = (_("Invalid input!"),
                  _("The name has to be entered."),
                  _("Error"))
MSG_NAME_EXISTS = (_("Invalid input!"),
                   _("The persoon you want to add already exists."),
                   _("Error"))
MSG_REMOVE_ADDRESS = (_("Removing '%s'"),
                      _("Are you sure you want to remove this person from your addresses?"),
                      _("Remove address"))

MSG_BACKUP_SUCCES = (_("The backup was successfully created."),
                     None,
                     _("Completed!"))
MSG_BACKUP_FAILED = (_("There was an error making the backup."),
                     None,
                     _("Failed!"))
MSG_RESTORE_SUCCES = (_("The backup was successfully restored.\nRestart the program."),
                      None,
                      _("Completed!"))
MSG_RESTORE_FAILED = (_("There was an error restoring the backup."),
                      None,
                      _("Failed!"))

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

MSG_UPDATE_NOW = (_("Update available!"),
                  _("There is an update available, do you want to download it now?"),
                  _("Update"))

MSG_UPDATE_ERROR = _("Error trying to get information. Are you connected to the internet?")
MSG_UPDATE_AVAILABLE = _("A new version is available. Please go to the Pigeon Planner website by clicking the link below and download the latest version")
MSG_NO_UPDATE = _("You already have the latest version installed.")
MSG_UPDATE_DEVELOPMENT = _("This isn't normal, or you must be running a development version")

