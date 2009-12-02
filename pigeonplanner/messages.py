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


MSG_ALREADY_RUNNING = (_("Pigeon Planner is already running."),
                       None,
                       _("Error"))

MSG_MAKE_DONATION = (_("Go to the website?"),
                     _("Pigeon Planner is free software. You don’t need to pay for using it. But if you like it, please consider donating to help improving it."),
                     _("Make a donation"))

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

MSG_REMOVE_ITEM = (_("Removing '%s' from '%s'."),
                   _("Are you sure you want to remove this item?"),
                   _("Remove item"))

MSG_REMOVE_DATABASE = (_("Removing database"),
                       _("Are you sure you want to remove the database? All data will be lost."),
                       _("Remove database"))

MSG_RMDB_FINISH = (_("Click \"OK\" to close the program. A new database will be created the next time you start the program again."),
                   None,
                   _("Restart required"))

MSG_OPTIMIZE_FINISH = (_("Optimization has been completed."),
                       None,
                       _("Completed!"))

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

MSG_RESTART_APP = (_("Pigeon Planner needs to be restarted for the changes to take effect."),
                   None,
                   _("Restart required"))

MSG_UPDATE_NOW = (_("Update available!"),
                  _("There is an update available, do you want to download it now?"),
                  _("Update"))

MSG_UPDATE_ERROR = _("Error trying to get information. Are you connected to the internet?")
MSG_UPDATE_AVAILABLE = _("A new version is available. Please go to the Pigeon Planner website by clicking the link below and download the latest version")
MSG_NO_UPDATE = _("You already have the latest version installed.")
MSG_UPDATE_DEVELOPMENT = _("This isn't normal, or you must be running a development version")

