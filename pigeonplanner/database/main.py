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


import sys
import os.path
import logging
logger = logging.getLogger(__name__)
import sqlite3
sqlite3.register_adapter(str, lambda s: s.decode("utf-8"))

from pigeonplanner import const


__all__ = ["DatabaseSession", "InvalidValueError", "Tables", "SCHEMA_VERSION"]


class InvalidValueError(Exception): pass


class Tables:
    PIGEONS = "Pigeons"
    RESULTS = "Results"
    BREEDING = "Breeding"
    MEDIA = "Media"
    MED = "Medication"
    ADDR = "Addresses"
    COLOURS = "Colours"
    RACEPOINTS = "Racepoints"
    TYPES = "Types"
    CATEGORIES = "Categories"
    SECTORS = "Sectors"
    LOFTS = "Lofts"
    STRAINS = "Strains"
    WEATHER = "Weather"
    WIND = "Wind"
    SOLD = "Sold"
    LOST = "Lost"
    DEAD = "Dead"
    BREEDER = "Breeder"
    LOANED = "Onloan"


SCHEMA_VERSION = 1
# The schema has the following signature:
# Table name:    Column name    Data type    Constraints
SCHEMA = {
        Tables.PIGEONS: [("Pigeonskey", "INTEGER", "PRIMARY KEY"),
                         ("pindex", "TEXT", "UNIQUE NOT NULL"),
                         ("band", "TEXT", "NOT NULL"),
                         ("year", "TEXT", "NOT NULL"),
                         ("sex", "TEXT", "NOT NULL"),
                         ("show", "INTEGER", "DEFAULT 1"),
                         ("active", "INTEGER", "DEFAULT 1"),
                         ("colour", "TEXT", "DEFAULT ''"),
                         ("name", "TEXT", "DEFAULT ''"),
                         ("strain", "TEXT", "DEFAULT ''"),
                         ("loft", "TEXT", "DEFAULT ''"),
                         ("image", "TEXT", "DEFAULT ''"),
                         ("sire", "TEXT", "NOT NULL DEFAULT ''"),
                         ("yearsire", "TEXT", "NOT NULL DEFAULT ''"),
                         ("dam", "TEXT", "NOT NULL DEFAULT ''"),
                         ("yeardam", "TEXT", "NOT NULL DEFAULT ''"),
                         ("extra1", "TEXT", "DEFAULT ''"),
                         ("extra2", "TEXT", "DEFAULT ''"),
                         ("extra3", "TEXT", "DEFAULT ''"),
                         ("extra4", "TEXT", "DEFAULT ''"),
                         ("extra5", "TEXT", "DEFAULT ''"),
                         ("extra6", "TEXT", "DEFAULT ''")],
        Tables.RESULTS: [("Resultkey", "INTEGER", "PRIMARY KEY"),
                         ("pindex", "TEXT", "NOT NULL"),
                         ("date", "TEXT", "NOT NULL"),
                         ("point", "TEXT", "NOT NULL"),
                         ("place", "INTEGER", "NOT NULL"),
                         ("out", "INTEGER", "NOT NULL"),
                         ("sector", "TEXT", "DEFAULT ''"),
                         ("type", "TEXT", "DEFAULT ''"),
                         ("category", "TEXT", "DEFAULT ''"),
                         ("wind", "TEXT", "DEFAULT ''"),
                         ("weather", "TEXT", "DEFAULT ''"),
                         ("put", "TEXT", "DEFAULT ''"),
                         ("back", "TEXT", "DEFAULT ''"),
                         ("ownplace", "INTEGER", "DEFAULT 0"),
                         ("ownout", "INTEGER", "DEFAULT 0"),
                         ("comment", "TEXT", "DEFAULT ''")],
        Tables.BREEDING: [("Breedingkey", "INTEGER", "PRIMARY KEY"),
                          ("sire", "TEXT", "NOT NULL"),
                          ("dam", "TEXT", "NOT NULL"),
                          ("date", "TEXT", "NOT NULL"),
                          ("laid1", "TEXT", "DEFAULT ''"),
                          ("hatched1", "TEXT", "DEFAULT ''"),
                          ("pindex1", "TEXT", "DEFAULT ''"),
                          ("success1", "INTEGER", "DEFAULT 0"),
                          ("laid2", "TEXT", "DEFAULT ''"),
                          ("hatched2", "TEXT", "DEFAULT ''"),
                          ("pindex2", "TEXT", "DEFAULT ''"),
                          ("success2", "INTEGER", "DEFAULT 0"),
                          ("clutch", "TEXT", "DEFAULT ''"),
                          ("box", "TEXT", "DEFAULT ''"),
                          ("comment", "TEXT", "DEFAULT ''")],
        Tables.MEDIA: [("Mediakey", "INTEGER", "PRIMARY KEY"),
                       ("pindex", "TEXT", "NOT NULL"),
                       ("type", "TEXT", "NOT NULL"),
                       ("path", "TEXT", "NOT NULL"),
                       ("title", "TEXT", "DEFAULT ''"),
                       ("description", "TEXT", "DEFAULT ''")],
        Tables.MED: [("Medicationkey", "INTEGER", "PRIMARY KEY"),
                     ("medid", "TEXT", "NOT NULL"),
                     ("pindex", "TEXT", "NOT NULL"),
                     ("date", "TEXT", "NOT NULL"),
                     ("description", "TEXT", "DEFAULT ''"),
                     ("doneby", "TEXT", "DEFAULT ''"),
                     ("medication", "TEXT", "DEFAULT ''"),
                     ("dosage", "TEXT", "DEFAULT ''"),
                     ("comment", "TEXT", "DEFAULT ''"),
                     ("vaccination", "INTEGER", "DEFAULT 0")],

        Tables.SOLD: [("Soldkey", "INTEGER", "PRIMARY KEY"),
                      ("pindex", "TEXT", "NOT NULL"),
                      ("person", "TEXT", "DEFAULT ''"),
                      ("date", "TEXT", "DEFAULT ''"),
                      ("info", "TEXT", "DEFAULT ''")],
        Tables.LOST: [("Lostkey", "INTEGER", "PRIMARY KEY"),
                      ("pindex", "TEXT", "NOT NULL"),
                      ("racepoint", "TEXT", "DEFAULT ''"),
                      ("date", "TEXT", "DEFAULT ''"),
                      ("info", "TEXT", "DEFAULT ''")],
        Tables.DEAD: [("Deadkey", "INTEGER", "PRIMARY KEY"),
                      ("pindex", "TEXT", "NOT NULL"),
                      ("date", "TEXT", "DEFAULT ''"),
                      ("info", "TEXT", "DEFAULT ''")],
        Tables.BREEDER: [("Breederkey", "INTEGER", "PRIMARY KEY"),
                         ("pindex", "TEXT", "NOT NULL"),
                         ("start", "TEXT", "DEFAULT ''"),
                         ("end", "TEXT", "DEFAULT ''"),
                         ("info", "TEXT", "DEFAULT ''")],
        Tables.LOANED: [("Onloankey", "INTEGER", "PRIMARY KEY"),
                        ("pindex", "TEXT", "NOT NULL"),
                        ("loaned", "TEXT", "DEFAULT ''"),
                        ("back", "TEXT", "DEFAULT ''"),
                        ("person", "TEXT", "DEFAULT ''"),
                        ("info", "TEXT", "DEFAULT ''")],

        Tables.ADDR: [("Addresskey", "INTEGER", "PRIMARY KEY"),
                      ("name", "TEXT", "NOT NULL"),
                      ("street", "TEXT", "DEFAULT ''"),
                      ("code", "TEXT", "DEFAULT ''"),
                      ("city", "TEXT", "DEFAULT ''"),
                      ("country", "TEXT", "DEFAULT ''"),
                      ("phone", "TEXT", "DEFAULT ''"),
                      ("email", "TEXT", "DEFAULT ''"),
                      ("comment", "TEXT", "DEFAULT ''"),
                      ("me", "INTEGER", "DEFAULT 0"),
                      ("latitude", "TEXT", "DEFAULT ''"),
                      ("longitude", "TEXT", "DEFAULT ''")],
        Tables.COLOURS: [("Colourkey", "INTEGER", "PRIMARY KEY"),
                         ("colour", "TEXT", "UNIQUE NOT NULL")],
        Tables.LOFTS: [("Loftkey", "INTEGER", "PRIMARY KEY"),
                       ("loft", "TEXT", "UNIQUE NOT NULL")],
        Tables.STRAINS: [("Strainkey", "INTEGER", "PRIMARY KEY"),
                         ("strain", "TEXT", "UNIQUE NOT NULL")],
        Tables.RACEPOINTS: [("Racepointkey", "INTEGER", "PRIMARY KEY"),
                            ("racepoint", "TEXT", "UNIQUE NOT NULL"),
                            ("xco", "TEXT", "DEFAULT ''"),
                            ("yco", "TEXT", "DEFAULT ''"),
                            ("distance", "TEXT", "DEFAULT ''"),
                            ("unit", "INTEGER", "DEFAULT 0")],
        Tables.TYPES: [("Typekey", "INTEGER", "PRIMARY KEY"),
                       ("type", "TEXT", "UNIQUE NOT NULL")],
        Tables.CATEGORIES: [("Categorykey", "INTEGER", "PRIMARY KEY"),
                            ("category", "TEXT", "UNIQUE NOT NULL")],
        Tables.SECTORS: [("Sectorkey", "INTEGER", "PRIMARY KEY"),
                         ("sector", "TEXT", "UNIQUE NOT NULL")],
        Tables.WEATHER: [("Weatherkey", "INTEGER", "PRIMARY KEY"),
                         ("weather", "TEXT", "UNIQUE NOT NULL")],
        Tables.WIND: [("Windkey", "INTEGER", "PRIMARY KEY"),
                      ("wind", "TEXT", "UNIQUE NOT NULL")],
    }

def get_table_names():
    return SCHEMA.keys()

def get_column_names(table):
    return [col[0] for col in SCHEMA[table]]

def get_column_sql(table, name):
    for col in SCHEMA[table]:
        if name == col[0]:
            coldefs = col
            break
    return ", ".join(coldefs)

def get_columns_sql(table):
    data = []
    for column_data in SCHEMA[table]:
        data.append(" ".join(column_data))
    return ", ".join(data)


class DatabaseSession(object):
    def __init__(self, dbfile=None):
        self.dbfile = dbfile or const.DATABASE
        self.is_new_db = not os.path.exists(self.dbfile)
        self.connection, self.cursor = self.__db_connect()

    def __db_connect(self):
        try:
            conn = sqlite3.connect(self.dbfile,
                            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        except Exception as e:
            from pigeonplanner.ui import logdialog

            logger.critical("Could not connect to database")
            logger.critical(e)
            logger.debug("Databasedir: %s" % const.PREFDIR)
            logger.debug("Database: %s" % self.dbfile)
            logger.debug("Databasedir exists: %s"  % os.path.exists(const.PREFDIR))
            logger.debug("Database exists: %s" % os.path.exists(self.dbfile))
            logger.debug("Databasedir writable: %s" % os.access(const.PREFDIR, os.W_OK))
            logger.debug("Database writable: %s" % os.access(self.dbfile, os.W_OK))
            logger.debug("Encoding: %s" % sys.getfilesystemencoding())

            logdialog.LogDialog()
            sys.exit()

        conn.row_factory = sqlite3.Row
        return (conn, conn.cursor())

    ##############
    ##  Helper methods
    ##############
    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in self.cursor.fetchall() if row[0]]

    def get_column_names(self, table):
        self.cursor.execute("PRAGMA table_info(%s)" % table)
        return [row[1] for row in self.cursor.fetchall() if row[1]]

    def add_column(self, table, column):
        self.cursor.execute("ALTER TABLE %s ADD COLUMN %s" % (table, column))
        self.connection.commit()

    def remove_table(self, table):
        self.cursor.execute("DROP TABLE IF EXISTS %s" % table)
        self.connection.commit()

    def add_table(self, table):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (table, get_columns_sql(table)))
        self.connection.commit()

    def recreate_table(self, table):
        self.cursor.execute("CREATE TEMP TABLE tmp_%s AS SELECT * FROM %s" % (table, table))
        self.cursor.execute("DROP TABLE %s" % table)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (table, get_columns_sql(table)))
        self.cursor.execute("INSERT INTO %s SELECT * FROM tmp_%s" % (table, table))
        self.cursor.execute("DROP TABLE tmp_%s" % table)
        self.connection.commit()

    ##############
    ##  Maintenance
    ##############
    def close(self):
        self.connection.close()

    def get_database_version(self):
        self.cursor.execute("PRAGMA user_version")
        return self.cursor.fetchone()[0]

    def set_database_version(self, version):
        self.cursor.execute("PRAGMA user_version=%s" % version)
        self.connection.commit()

    def optimize_database(self):
        self.cursor.execute("VACUUM")

    def check_database_integrity(self):
        """
        PRAGMA integrity_check;
        PRAGMA integrity_check(integer)

        This pragma does an integrity check of the entire database. It looks for
        out-of-order records, missing pages, malformed records, and corrupt indices.
        If any problems are found, then strings are returned (as multiple rows with
        a single column per row) which describe the problems. At most integer errors
        will be reported before the analysis quits. The default value for integer
        is 100. If no errors are found, a single row with the value "ok" is returned.
        """

        self.cursor.execute("PRAGMA integrity_check")
        return self.cursor.fetchall()

    def check_schema(self):
        changed = False
        db_version = self.get_database_version()
        while db_version < SCHEMA_VERSION:
            getattr(self, "migrate_from_%s_to_%s" % (db_version, db_version+1))()
            db_version += 1
            changed = True
        self.set_database_version(db_version)
        return changed

    ##############
    ##  Migrations
    ##############
    def migrate_from_0_to_1(self):
        logger.debug("Migrating from 0 to 1")

        # These are some migrations normally done by the old check method.
        # They are from old Pigeon Planner versions, but we better make sure these
        # changes were done so they won't cause any problems.
        if 'alive' in self.get_column_names(Tables.PIGEONS):
            # This column has been renamed somewhere between version 0.4.0 and 0.6.0
            logger.debug("Renaming 'alive' column")
            self.recreate_table(Tables.PIGEONS)

        if not "latitude" in self.get_column_names(Tables.ADDR):
            # latitude and longiitude columns were added later on
            logger.debug("Adding latitude and longitude columns to Adresses table")
            self.add_column(Tables.ADDR, "latitude TEXT DEFAULT ''")
            self.add_column(Tables.ADDR, "longitude TEXT DEFAULT ''")

        if not "unit" in self.get_column_names(Tables.RACEPOINTS):
            # unit column was added later on
            logger.debug("Adding unit column to Racepoints table")
            self.add_column(Tables.RACEPOINTS, "unit INTEGER DEFAULT 0")

        # The Version table was dropped. It was never used anyway.
        logger.debug("Removing Version table")
        self.remove_table("Version")

        # The Events table was dropped. The calendar functionality is removed.
        logger.debug("Removing Events table")
        self.remove_table("Events")

        # Make sure all tables from the current schema exist
        for table_name in SCHEMA.keys():
            column_sql = get_columns_sql(table_name)
            self.cursor.execute('CREATE TABLE IF NOT EXISTS %s (%s)' % (table_name, column_sql))
        self.connection.commit()

        # Column constraints were added for all tables
        for table in get_table_names():
            logger.debug("Recreating %s table" % table)
            self.recreate_table(table)

