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
import shutil
import logging

from pigeonplanner.core import const
from pigeonplanner.database import models
from pigeonplanner.database import migrations

logger = logging.getLogger(__name__)

peewee_logger = logging.getLogger("peewee")
peewee_logger.disabled = True


class DatabaseVersionError(Exception): pass


class DatabaseMigrationError(Exception): pass


class DatabaseSession(object):
    def __init__(self):
        self.dbfile = None
        self.connection = None

    def open(self, dbfile=None):
        self.dbfile = dbfile or const.DATABASE
        self.is_new_db = (not os.path.exists(self.dbfile) or
                          os.path.getsize(self.dbfile) == 0)
        self.connection = models.set_database_path(self.dbfile)
        self.connection.connect()
        # Set this explicitly to work with ON DELETE/UPDATE
        self.connection.pragma("foreign_keys", 1)

        if self.is_new_db:
            logger.debug("Creating tables for the new database")
            self.connection.create_tables(models.all_tables())
            latest_version = migrations.get_latest_version()
            self.set_database_version(latest_version)

        if self.get_database_version() > migrations.get_latest_version():
            raise DatabaseVersionError

    def close(self):
        self.connection.close()
        self.connection = None

    def is_open(self):
        return self.connection is not None

    def get_database_version(self):
        return self.connection.pragma("user_version")

    def set_database_version(self, version):
        self.connection.pragma("user_version", version)

    def optimize_database(self):
        self.connection.execute_sql("VACUUM")

    def needs_update(self):
        db_version = self.get_database_version()
        return db_version < migrations.get_latest_version()

    def do_migrations(self):
        current_version = self.get_database_version()
        if current_version >= migrations.get_latest_version():
            return False

        # Make a backup of the database before migrating to restore it in
        # case an unexpected error happens during upgrade.
        backupdb = self.dbfile + "_bckp"
        shutil.copy(self.dbfile, backupdb)

        for migration in migrations.get_migrations():
            if migration["version"] <= current_version:
                continue
            try:
                logger.debug("Starting database migration %s", migration["version"])
                migration["module"].do_migration(self.connection)
            except Exception:
                # Catch any exception during migration!
                logger.error("Database migration failed!", exc_info=True)
                shutil.copy(backupdb, self.dbfile)
                os.remove(backupdb)
                raise DatabaseMigrationError

            current_version = migration["version"]
            # Make sure to update the actual database with the new version after
            # every migration, not only at the end. This will ensure the database
            # always has the correct version in case a migration fails.
            self.set_database_version(current_version)

        try:
            os.remove(backupdb)
        except Exception:
            pass

        return True
