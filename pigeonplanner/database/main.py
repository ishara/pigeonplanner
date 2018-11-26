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

    def open(self, dbfile=None):
        self.dbfile = dbfile or const.DATABASE
        self.is_new_db = (not os.path.exists(self.dbfile) or
                          os.path.getsize(self.dbfile) == 0)
        logger.debug("Opening database %s (new db=%s)", self.dbfile, self.is_new_db)
        models.database.init(self.dbfile)
        models.database.connect()
        # Set this explicitly to work with ON DELETE/UPDATE
        models.database.pragma("foreign_keys", 1)

        if self.is_new_db:
            logger.debug("Creating tables for the new database")
            models.database.create_tables(models.all_tables())
            latest_version = migrations.get_latest_version()
            self.set_database_version(latest_version)

        if self.get_database_version() > migrations.get_latest_version():
            raise DatabaseVersionError

        # TODO: This is a HACK, not a fix!
        #       There's a bug since version 3.0.0 where there's a possibility that the
        #       Pigeon and Status database tables become out of sync. They have a
        #       one-to-one relationship with the Status having a UNIQUE backref to
        #       the Pigeon. Some user reports show that a Status row is left behind
        #       after removing a Pigeon row. Thus adding a Pigeon row with the same
        #       ID will trigger an IntegrityError. Especially messing up get or create
        #       functionality. The current workaround is to remove the extra Status row(s)
        #       where the Pigeon ID references to a non-existing Pigeon row. This
        #       workaround is put here because it affects different parts in the code
        #       and to keep this in one place only. The user has to re-open the database
        #       though for having effect.
        #       The reason why this problem happens was not found during some testing.
        #       The Status row is deleted on database level (ON DELETE CASCADE).
        #       Fix it as soon as possible.
        if models.Pigeon.select().count() < models.Status.select().count():
            logger.warning("The Pigeon and Status tables are out of sync, applying fix.")
            pigeon_ids = models.Pigeon.select(models.Pigeon.id)
            models.Status.delete().where(models.Status.pigeon.not_in(pigeon_ids)).execute()

    def close(self):
        models.database.close()

    def is_open(self):
        return not models.database.is_closed()

    def get_database_version(self):
        return models.database.pragma("user_version")

    def set_database_version(self, version):
        models.database.pragma("user_version", version)

    def optimize_database(self):
        models.database.execute_sql("VACUUM")

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
                migration["module"].do_migration(models.database)
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
