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
Provides access to the database
"""


import sys
import os.path
import logging
logger = logging.getLogger(__name__)
import sqlite3
sqlite3.register_adapter(str, lambda s: s.decode('utf-8'))

import const
import common


(RET_FIRSTCOL,
 RET_SECCOL,
 RET_ALLCOL,
 RET_ONEROW) = range(4)


class DatabaseOperations(object):
    PIGEONS = "Pigeons"
    RESULTS = "Results"
    MEDIA = "Media"
    MED = "Medication"
    ADDR = "Addresses"
    EVENTS = "Events"
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

    SCHEMA = {
    'Version': '(Versionkey INTEGER PRIMARY KEY,'
               ' db_version INTEGER)',
    PIGEONS: '(Pigeonskey INTEGER PRIMARY KEY,'
             ' pindex TEXT UNIQUE,'
             ' band TEXT,'
             ' year TEXT,'
             ' sex TEXT,'
             ' show INTEGER,'
             ' active INTEGER,'
             ' colour TEXT,'
             ' name TEXT,'
             ' strain TEXT,'
             ' loft TEXT,'
             ' image TEXT,'
             ' sire TEXT,'
             ' yearsire TEXT,'
             ' dam TEXT,'
             ' yeardam TEXT,'
             ' extra1 TEXT,'
             ' extra2 TEXT,'
             ' extra3 TEXT,'
             ' extra4 TEXT,'
             ' extra5 TEXT,'
             ' extra6 TEXT)',
    RESULTS: '(Resultkey INTEGER PRIMARY KEY,'
             ' pindex TEXT,'
             ' date TEXT,'
             ' point TEXT,'
             ' place INTEGER,'
             ' out INTEGER,'
             ' sector TEXT,'
             ' type TEXT,'
             ' category TEXT,'
             ' wind TEXT,'
             ' weather TEXT,'
             ' put TEXT,'
             ' back TEXT,'
             ' ownplace INTEGER,'
             ' ownout INTEGER,'
             ' comment TEXT)',
    MEDIA: '(Mediakey INTEGER PRIMARY KEY,'
           ' pindex TEXT,'
           ' type TEXT,'
           ' path TEXT,'
           ' title TEXT,'
           ' description TEXT)',
    MED: '(Medicationkey INTEGER PRIMARY KEY,'
         ' medid TEXT,'
         ' pindex TEXT,'
         ' date TEXT,'
         ' description TEXT,'
         ' doneby TEXT,'
         ' medication TEXT,'
         ' dosage TEXT,'
         ' comment TEXT,'
         ' vaccination INTEGER)',
    ADDR: '(Addresskey INTEGER PRIMARY KEY,'
          ' name TEXT,'
          ' street TEXT,'
          ' code TEXT,'
          ' city TEXT,'
          ' country TEXT,'
          ' phone TEXT,'
          ' email TEXT,'
          ' comment TEXT,'
          ' me INTEGER)',
    EVENTS: '(Eventskey INTEGER PRIMARY KEY,'
            ' date TEXT,'
            ' type TEXT,'
            ' description TEXT,'
            ' comment TEXT,'
            ' notify INTEGER,'
            ' interval INTEGER,'
            ' notifyday INTEGER)',
    COLOURS: '(Colourkey INTEGER PRIMARY KEY,'
             ' colour TEXT UNIQUE)',
    RACEPOINTS: '(Racepointkey INTEGER PRIMARY KEY,'
                ' racepoint TEXT UNIQUE,'
                ' xco TEXT,'
                ' yco TEXT,'
                ' distance TEXT)',
    SECTORS: '(Sectorkey INTEGER PRIMARY KEY,'
             ' sector TEXT UNIQUE)',
    TYPES: '(Typekey INTEGER PRIMARY KEY,'
           ' type TEXT UNIQUE)',
    CATEGORIES: '(Categorykey INTEGER PRIMARY KEY,'
                ' category TEXT UNIQUE)',
    STRAINS: '(Strainkey INTEGER PRIMARY KEY,'
             ' strain TEXT UNIQUE)',
    LOFTS: '(Loftkey INTEGER PRIMARY KEY,'
           ' loft TEXT UNIQUE)',
    WEATHER: '(Weatherkey INTEGER PRIMARY KEY,'
             ' weather TEXT UNIQUE)',
    WIND: '(Windkey INTEGER PRIMARY KEY,'
          ' wind TEXT UNIQUE)',
    SOLD: '(Soldkey INTEGER PRIMARY KEY,'
          ' pindex TEXT,'
          ' person TEXT,'
          ' date TEXT,'
          ' info TEXT)',
    LOST: '(Lostkey INTEGER PRIMARY KEY,'
          ' pindex TEXT,'
          ' racepoint TEXT,'
          ' date TEXT,'
          ' info TEXT)',
    DEAD: '(Deadkey INTEGER PRIMARY KEY,'
          ' pindex TEXT,'
          ' date TEXT,'
          ' info TEXT)',
    }

    def __init__(self):
        self.conn, self.cursor = self.__db_connect()

        if not os.path.exists(const.DATABASE):
            for table_name, sql in self.SCHEMA.items():
                self.cursor.execute('CREATE TABLE IF NOT EXISTS %s %s' 
                                                    %(table_name, sql))
                self.conn.commit()

    def get_n_column_name(self, table, start=1, end=None):
        if end is None:
            end = start + 1
        return [sql.split(' ')[0].lstrip(' (')
                    for sql in self.SCHEMA[table].split(', ')[start:end]]

    def create_sql_from_names(self, colnames):
        sql = ""
        for name in colnames:
            sql += " %s=?," % name
        return sql.lstrip(' (').rstrip(',')

    def close(self):
        self.conn.close()

    def __db_connect(self):
        try:
            conn = sqlite3.connect(const.DATABASE)
        except Exception, e:
            from ui import logdialog

            logger.critical("Could not connect to database")
            logger.critical(e)
            logger.debug("Databasedir: %s" %const.PREFDIR)
            logger.debug("Database: %s" %const.DATABASE)
            logger.debug("Databasedir exists: %s"
                                        %os.path.exists(const.PREFDIR))
            logger.debug("Database exists: %s" %os.path.exists(const.DATABASE))
            logger.debug("Databasedir writable: %s"
                                        %os.access(const.PREFDIR, os.W_OK))
            logger.debug("Database writable: %s"
                                        %os.access(const.DATABASE, os.W_OK))
            logger.debug("Encoding: %s" %sys.getfilesystemencoding())

            logdialog.LogDialog()
            sys.exit()

        cursor = conn.cursor()
        return (conn, cursor)

    def __db_execute(self, sql, args=None):
        try:
            if args is None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, args)
        except sqlite3.IntegrityError:
            pass
        self.conn.commit()
        return self.cursor.lastrowid

    def __db_execute_select(self, sql, args=None, retval=None):
        data = None
        if args is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, args)

        if retval == RET_FIRSTCOL:
            data = [row[0] for row in self.cursor.fetchall() if row[0]]
        elif retval == RET_SECCOL:
            data = [row[1] for row in self.cursor.fetchall() if row[1]]
        elif retval == RET_ALLCOL or retval is None:
            data = self.cursor.fetchall()
        elif retval == RET_ONEROW:
            data = self.cursor.fetchone()
        return data

#### General methods to be called outside this module
    def execute(self, sql, select=False):
        if select:
            return self.__db_execute_select(sql, None, RET_ALLCOL)
        else:
            return self.__db_execute(sql)

#### General methods for SQL queries
    def insert_into_table(self, table, data):
        sql = 'INSERT INTO %s VALUES (null%s)' % (table, ", ?"*len(data))
        return self.__db_execute(sql, data)

    def select_from_table(self, table):
        sql = 'SELECT * FROM %s' % table
        return self.__db_execute_select(sql, None, RET_SECCOL)

    def update_table(self, table, data, startcol, idcol=1):
        collist = self.get_n_column_name(table, startcol, startcol+(len(data)-1))
        colsql = self.create_sql_from_names(collist)
        idcolname = self.get_n_column_name(table, idcol)[0]
        sql = 'UPDATE %s SET %s WHERE %s=?' % (table, colsql, idcolname)
        self.__db_execute(sql, data)

    def delete_from_table(self, table, item, col=1):
        sql = 'DELETE FROM %s WHERE %s=?' % (table,
                                            self.get_n_column_name(table, col)[0])
        self.__db_execute(sql, (item,))

#### Methods used at startup to check and update the database
    def get_tablenames(self):
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        return self.__db_execute_select(sql, None, RET_FIRSTCOL)

    def get_columnnames(self, table):
        sql = "PRAGMA table_info(%s)" % table
        return self.__db_execute_select(sql, None, RET_SECCOL)

    def add_column(self, table, column):
        sql = "ALTER TABLE %s ADD COLUMN %s" % (table, column)
        self.__db_execute(sql)

    def add_table_from_schema(self, table):
        sql = "CREATE TABLE IF NOT EXISTS %s %s" % (table, self.SCHEMA[table])
        self.__db_execute(sql)

    def change_column_name(self, table):
        self.cursor.execute("CREATE TEMP TABLE tmp_%s AS SELECT * FROM %s"
                                        % (table, table))
        self.cursor.execute("DROP TABLE %s" %table)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s %s"
                                        % (table, self.SCHEMA[table]))
        self.cursor.execute("INSERT INTO %s SELECT * FROM tmp_%s" % (table, table))
        # No need to drop the temporary table. From the SQLite docs:
        # If the "TEMP" or "TEMPORARY" keyword occurs (...) the table is only
        # visible within that same database connection and is automatically
        # deleted when the database connection is closed.
        self.conn.commit()

#### Maintenance
    def optimize_db(self):
        self.__db_execute("VACUUM")

    def check_db(self):
        return self.__db_execute_select("PRAGMA integrity_check")

    def check_empty_column(self, table, column):
        sql = "SELECT * FROM %s WHERE %s=''" % (table, column)
        return self.__db_execute_select(sql, None, RET_ALLCOL)

    def check_schema(self):
        # Check if all tables are present
        for s_table, s_columns in self.SCHEMA.items():
            if not s_table in self.get_tablenames():
                logger.debug("Adding table '%s'" %s_table)
                self.add_table_from_schema(s_table)

        # Check if all columns are present
        for table in self.get_tablenames(): # Get all tables again
            columns = self.get_columnnames(table)
            if table == 'Pigeons' and 'alive' in columns:
                # This column has been renamed somewhere
                # between version 0.4.0 and 0.6.0
                logger.debug("Renaming 'alive' column")
                self.change_column_name(table)
                # Get all columns again in this table
                columns = self.get_columnnames(table)
            for column_def in self.SCHEMA[table][1:-1].split(', '):
                column = column_def.split(' ')[0]
                if not column in columns:
                    # Note: no need to show a progressbar. According to the
                    # SQLite website:
                    # The execution time of the ALTER TABLE command is
                    # independent of the amount of data in the table.
                    # The ALTER TABLE command runs as quickly on a table
                    # with 10 million rows as it does on a table with 1 row.
                    logger.debug("Adding column '%s' to table '%s'"
                                 %(column, table))
                    self.add_column(table, column_def)

#### Pigeons
    def update_pedigree_pigeon(self, data):
        sql = 'UPDATE Pigeons SET pindex=?, band=?, year=?, \
               extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, \
               extra6=? WHERE pindex=?'
        self.__db_execute(sql, data)

    def get_pigeons(self):
        sql = 'SELECT * FROM Pigeons'
        return self.__db_execute_select(sql, None, RET_ALLCOL)

    def get_pigeon_data(self, pindex):
        sql = 'SELECT * FROM Pigeons WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ONEROW)

    def has_pigeon(self, band):
        sql = 'SELECT COUNT(*) FROM Pigeons WHERE pindex=?'
        return self.__db_execute_select(sql, (band,), RET_FIRSTCOL)

    def has_parent(self, sex, band, year):
        cols = ('sire', 'yearsire') if sex == const.SIRE else ('dam', 'yeardam')
        sql = 'SELECT COUNT(*) FROM Pigeons WHERE %s=? AND %s=?' % cols
        return self.__db_execute_select(sql, (band, year), RET_ONEROW)[0]

    def get_all_images(self):
        sql = 'SELECT pindex, band, year, image FROM Pigeons'
        return self.__db_execute_select(sql, None, RET_ALLCOL)

#### Results
    def get_all_results(self):
        sql = 'SELECT * FROM Results'
        return self.__db_execute_select(sql, None, RET_ALLCOL)

    def get_pigeon_results(self, pindex):
        sql = 'SELECT * FROM Results WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ALLCOL)

    def get_pigeon_results_at_date(self, data):
        sql = 'SELECT * FROM Results WHERE pindex=? AND date=?'
        return self.__db_execute_select(sql, data, RET_ALLCOL)

    def has_result(self, data):
        sql = 'SELECT COUNT(*) FROM Results WHERE pindex=? and date=? \
               and point=? and place=? and out=? and sector=? \
               and type=? and category=? and wind=? and weather=? \
               and put=? and back=? and ownplace=? and ownout=? \
               and comment=?'
        return self.__db_execute_select(sql, data, RET_FIRSTCOL)

    def has_results(self, pindex):
        sql = 'SELECT COUNT(*) FROM Results WHERE pindex=?'
        if len(self.__db_execute_select(sql, (pindex,), RET_FIRSTCOL)) == 0:
            return False
        else:
            return True

#### Media
    def get_pigeon_media(self, pindex):
        sql = 'SELECT * FROM Media WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ALLCOL)

#### Medication
    def delete_medication_from_id_pindex(self, ID, pindex):
        sql = 'DELETE FROM Medication WHERE medid=? AND pindex=?'
        self.__db_execute(sql, (ID, pindex))

    def get_pigeon_medication(self, pindex):
        sql = 'SELECT * FROM Medication WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ALLCOL)

    def get_medication_from_id(self, ID):
        sql = 'SELECT * FROM Medication WHERE medid=?'
        return self.__db_execute_select(sql, (ID,), RET_ONEROW)

    def get_pigeons_from_medid(self, medid):
        sql = 'SELECT pindex FROM Medication WHERE medid=?'
        return self.__db_execute_select(sql, (medid,), RET_FIRSTCOL)

    def has_medication(self, pindex):
        sql = 'SELECT COUNT(*) FROM Medication WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_FIRSTCOL)

    def count_medication_entries(self, medid):
        sql = 'SELECT COUNT(*) FROM Medication WHERE medid=?'
        return self.__db_execute_select(sql, (medid,), RET_FIRSTCOL)[0]

#### Events
    def get_all_events(self):
        sql = 'SELECT * FROM Events'
        return self.__db_execute_select(sql)

    def get_event(self, ID):
        sql = 'SELECT * FROM Events WHERE Eventskey=?'
        return self.__db_execute_select(sql, (ID,), RET_ONEROW)

    def get_notification(self, now):
        sql = 'SELECT Eventskey, date, description FROM Events \
               WHERE notifyday<=? AND notifyday!=0 ORDER BY date ASC'
        return self.__db_execute_select(sql, (now,), RET_ALLCOL)

#### Addresses
    def get_all_addresses(self):
        sql = 'SELECT * FROM Addresses'
        return self.__db_execute_select(sql, None, RET_ALLCOL)

    def get_address(self, key):
        sql = 'SELECT * FROM Addresses WHERE Addresskey=?'
        return self.__db_execute_select(sql, (key,), RET_ONEROW)

    def get_own_address(self):
        sql = 'SELECT * FROM Addresses WHERE me=1'
        return self.__db_execute_select(sql, None, RET_ONEROW)

#### Racepoints
    def get_racepoint_data(self, racepoint):
        sql = 'SELECT xco, yco, distance FROM Racepoints WHERE racepoint=?'
        return self.__db_execute_select(sql, (racepoint,), RET_ONEROW)

#### Sold
    def get_sold_data(self, pindex):
        sql = 'SELECT person, date, info FROM Sold WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ONEROW)

#### Lost
    def get_lost_data(self, pindex):
        sql = 'SELECT racepoint, date, info FROM Lost WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ONEROW)

#### Dead
    def get_dead_data(self, pindex):
        sql = 'SELECT date, info FROM Dead WHERE pindex=?'
        return self.__db_execute_select(sql, (pindex,), RET_ONEROW)

