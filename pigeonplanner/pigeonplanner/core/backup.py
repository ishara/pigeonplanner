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
Provides backup and restore functions
"""

import os
import zipfile
import logging
from datetime import date

from pigeonplanner.core import const
from pigeonplanner.database.manager import dbmanager

logger = logging.getLogger(__name__)


class BackupError(Exception):
    pass


class RestoreError(Exception):
    pass


def create_backup_filename():
    return "pigeonplanner_backup_%s.zip" % date.today().strftime("%Y-%m-%d")


def create_backup(destination, overwrite=True, include_config=True):
    """Create a backup file at the given destination.

    :param destination: full path with filename
    :param overwrite:
    :param include_config:
    :return:
    """

    logger.debug("Create backup %s (overwrite=%s, include_config=%s)", destination, overwrite, include_config)

    if os.path.exists(destination):
        if overwrite:
            os.unlink(destination)
        else:
            raise BackupError("The backup file already exists.")

    files = [
        const.DATABASEINFO,
    ]
    if include_config:
        files.append(const.CONFIGFILE)
    files.extend([dbinfo.path for dbinfo in get_valid_databases()])

    try:
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_STORED) as zfile:
            for filepath in files:
                filename = os.path.basename(filepath)
                zfile.write(filepath, filename)
    except Exception as exc:
        logger.error(exc)
        raise


def get_valid_databases():
    dbs = []
    for dbinfo in dbmanager.get_databases():
        if not os.path.exists(dbinfo.path):
            continue
        dbs.append(dbinfo)
    return dbs


class RestoreOperation:
    def __init__(self, path):
        self.path = path
        with zipfile.ZipFile(path, "r") as zfile:
            self.namelist = zfile.namelist()
            try:
                self.database_info = zfile.read(os.path.basename(const.DATABASEINFO))
                self.old_backup = False
            except KeyError:
                # Old style backups don't have a list of databases
                self.database_info = None
                self.old_backup = True

    def is_valid_archive(self):
        if not zipfile.is_zipfile(self.path):
            return False

        if self.old_backup and "pigeonplanner.db" not in self.namelist:
            return False

        if not os.path.basename(const.DATABASEINFO) in self.namelist and not self.old_backup:
            return False

        return True

    def has_config_file(self):
        return os.path.basename(const.CONFIGFILE) in self.namelist

    def restore_backup(self, dbobjs, configfile):
        if not self.is_valid_archive():
            raise RestoreError(_("The file '%s' is not a valid Pigeon Planner backup.") % self.path)

        existing_paths = [dbobj.path for dbobj in dbmanager.get_databases()]

        with zipfile.ZipFile(self.path, "r") as zfile:
            if self.has_config_file() and configfile:
                zfile.extract(os.path.basename(const.CONFIGFILE), const.PREFDIR)

            for dbobj in dbobjs:
                zfile.extract(dbobj.filename, dbobj.directory)
                if dbobj.path not in existing_paths:
                    dbmanager.add(dbobj.name, dbobj.description, dbobj.path)
