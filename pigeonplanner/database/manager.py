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
import json
import errno
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.database import session


logger = logging.getLogger(__name__)


class DatabaseInfoError(Exception):
    def __init__(self, message):
        self.message = message


class DatabaseOperationError(Exception):
    def __init__(self, message):
        self.message = message


class DatabaseInfo:
    def __init__(self, name: str, path: str, description: str, default: bool):
        self.name = name
        self.path = path
        self.description = description
        self.default = default

    def __repr__(self):
        return u"<DatabaseInfo name=%s>" % self.name

    @property
    def directory(self) -> str:
        return os.path.dirname(self.path)

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)

    @property
    def writable(self) -> bool:
        return os.access(self.path, os.W_OK)

    @property
    def last_access(self) -> str:
        try:
            t = os.path.getmtime(self.path)
        except OSError:
            return "0000-00-00 00:00:00"
        return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def filesize(self) -> int:
        try:
            s = os.path.getsize(self.path)
        except OSError:
            return 0
        return s

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "default": self.default,
        }


class DBManager:
    default_name = _("My pigeons")
    default_description = _("My default database")

    def __init__(self):
        try:
            self._dbs = self._load_dbs()
        except IOError:
            # Database config file doesn't exist
            if os.path.exists(const.DATABASE):
                # The default database exist, which means an older version of Pigeon Planner
                # was already used before. Just add this database to the list.
                self._dbs = [DatabaseInfo(self.default_name, const.DATABASE, self.default_description, False)]
            else:
                # First run, let the user create their own database.
                self._dbs = []
            self._save_dbs()

    def get_databases(self) -> List[DatabaseInfo]:
        """Return a list of available database objects"""
        return self._dbs

    def save(self):
        """Save all database objects to the configuration file"""
        self._save_dbs()

    def reorder(self, new_order: List[DatabaseInfo]):
        """Reorder the current database list to match the given list.

        @param new_order: List of DatabaseInfo objects
        """
        self._dbs.sort(key=lambda x: new_order.index(x))
        self.save()

    def set_default(self, dbobj: DatabaseInfo, value: bool):
        """Set the default value to the given database object.

        @param dbobj: The DatabaseInfo to change
        @param value: Bool to set the default value
        """
        if value:
            for db in self._dbs:
                db.default = False
        dbobj.default = value
        self.save()

    def get_default(self) -> Optional[DatabaseInfo]:
        """Get the default database object."""
        for db in self._dbs:
            if db.default:
                return db
        return None

    # noinspection PyMethodMayBeStatic
    def prompt_do_upgrade(self) -> bool:
        """Called when a database upgrade is needed. Return True to continue or False
        to abort. Override this method in the GUI to provide a dialog for example.
        """
        return True

    def upgrade_finished(self):
        pass

    def open(self, dbobj: DatabaseInfo):
        """Open the given database object.

        @param dbobj: The DatabaseInfo to open
        """

        self.close_database()
        session.open(dbobj.path)
        if session.needs_update():
            if not self.prompt_do_upgrade():
                self.close_database()
                raise DatabaseInfoError("")
            session.do_migrations()
            self.upgrade_finished()

    def add(self, name: str, description: str, path: str) -> DatabaseInfo:
        name = name.strip()
        description = description.strip()

        self._check_input_name(name)

        for dbobj in self._dbs:
            if dbobj.path == path:
                raise DatabaseInfoError(_("This database is already added."))

        # TODO: check for writable path?

        info = DatabaseInfo(name, path, description, False)
        self._dbs.append(info)
        self.save()
        return info

    def create(self, name: str, description: str, path: str) -> DatabaseInfo:
        name = name.strip()
        description = description.strip()

        self._check_input_name(name)

        dbfilepath = self._get_new_db_path(path)
        try:
            open(dbfilepath, "w").close()
        except IOError:
            raise DatabaseInfoError(_("Database path '%s' is not writeable.") % path)

        info = DatabaseInfo(name, dbfilepath, description, False)
        self._dbs.append(info)
        self.save()
        return info

    def edit(self, dbobj: DatabaseInfo, name: str, description: str, path: str) -> DatabaseInfo:
        name = name.strip()
        description = description.strip()

        if dbobj.name != name:
            self._check_input_name(name)

        if dbobj.path != path:
            try:
                shutil.move(dbobj.path, path)
            except (shutil.Error, IOError) as exc:
                # Don't raise errno.ENOENT (No such file or directory)
                # This means the user changes the location of a database that doesn't exist.
                if exc.errno != errno.ENOENT:
                    raise DatabaseOperationError(_("Moving the database failed with message:\n%s") % exc)

        dbobj.name = name
        dbobj.description = description
        dbobj.path = path
        self.save()
        return dbobj

    def delete(self, dbobj: DatabaseInfo):
        self.close_database()

        try:
            os.remove(dbobj.path)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                # The database doesn't exist, no need to report this
                pass
            elif exc.errno == errno.EACCES:
                # Permission denied, the path is not writable. Report back that
                # the database isn't removed.
                raise DatabaseOperationError(_("Unable to remove the database: permission denied"))
            else:
                # None of our special cases, raise the original exception
                raise

        # Always update the config file
        self._dbs.remove(dbobj)
        self.save()

    def remove_from_config(self, dbobj: DatabaseInfo):
        """Remove a database from the configuration file without removing the actual database"""
        self._dbs.remove(dbobj)
        self.save()

    def copy(self, dbobj: DatabaseInfo) -> DatabaseInfo:
        n_copy = 1
        while True:
            name = "%s (%s %s)" % (dbobj.name, _("copy"), n_copy)
            description = "%s (%s %s)" % (dbobj.description, _("copy"), n_copy)
            try:
                self._check_input_name(name)
            except DatabaseInfoError:
                n_copy += 1
            else:
                break

        new_db_path = self._get_new_db_path(os.path.dirname(dbobj.path))
        shutil.copy(dbobj.path, new_db_path)

        info = DatabaseInfo(name, new_db_path, description, False)
        self._dbs.append(info)
        self.save()
        return info

    def move(self, dbobj: DatabaseInfo, new_path: str) -> DatabaseInfo:
        filename = os.path.basename(dbobj.path)
        destination = os.path.join(new_path, filename)
        try:
            shutil.move(dbobj.path, destination)
        except (shutil.Error, IOError) as exc:
            raise DatabaseOperationError(_("Moving the database failed with message:\n%s") % exc)
        dbobj.path = destination
        self.save()
        return dbobj

    # noinspection PyMethodMayBeStatic
    def close_database(self):
        try:
            session.close()
        except Exception as exc:
            logger.error("Failed to close database: %s", exc)

    # noinspection PyMethodMayBeStatic
    def _load_dbs(self) -> List[DatabaseInfo]:
        with open(const.DATABASEINFO) as infile:
            data = json.load(infile)
        return [DatabaseInfo(**info) for info in data]

    def _save_dbs(self):
        data = []
        for dbobj in self._dbs:
            data.append(dbobj.as_dict())

        with open(const.DATABASEINFO, "w") as outfile:
            json.dump(data, outfile, indent=4)

    # noinspection PyMethodMayBeStatic
    def _get_new_db_path(self, path: str) -> str:
        # Keep checking for a unique filename
        db = None
        exists = True
        while exists:
            db = os.path.join(path, "pigeonplanner_%s.db" % common.get_random_string(8))
            exists = os.path.exists(db)
        return db

    def _check_input_name(self, name: str):
        if name == "":
            raise DatabaseInfoError(_("Database name is required."))
        for dbobj in self._dbs:
            if dbobj.name == name:
                raise DatabaseInfoError(_("Database name '%s' already exists.") % name)


dbmanager = None


def init_manager():
    global dbmanager
    dbmanager = DBManager()
