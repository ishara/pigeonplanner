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
PIGEONFILE = os.path.join(PREFDIR, 'pigeon.list')
RESULTFILE = os.path.join(PREFDIR, 'results.db')
DATAFILE = os.path.join(PREFDIR, 'data.db')

MSGIMG = _("This image is either not supported or corrupt, please choose another one.")

MSGSHOW = _("This pigeon already exists, but isn't showing. Do you want to show it again?")
MSGEXIST = _("This pigeon already exists. Overwrite it?")
MSGADD = _("This pigeon doesn't exist. Do you want to add it?")

MSGINPUT = _("The ringnumber and year of the %s are necessary.\n\nCheck if these are entered.")
MSGNUMBER = _("Incorrect input of the ringnumber or year of the %s.\n\nOnly numbers are accepted.")
MSGLENGTH = _("Incorrect input of the ringnumber or year of the %s.\n\nCheck the length.")

MSGEMPTY = _("All fields have to be entered.")
MSGFORMAT = _("The date you entered has the wrong format. It should be ISO-format (YYYY-MM-DD).")

MSGBCKPOK = _("The backup was successfully created.")
MSGRESTOK = _("The backup was successfully restored.\nRestart the program.")

MSGDEFAULT = _("This will set back all the settings to the default values.\nAre you sure?")
MSGNOINFO = _("You have not entered your personal information.\nThis will be shown on top of the printed pedigree.\nDo you want to add it now?")

MSGPRINTERROR = _("Error printing the pedigree")

