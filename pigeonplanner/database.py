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
import sqlite3
import logging
logger = logging.getLogger(__name__)

import const


class DatabaseOperations:
    SCHEMA = {
    'Version': '(Versionkey INTEGER PRIMARY KEY,'
               ' db_version INTEGER)',
    'Pigeons': '(Pigeonskey INTEGER PRIMARY KEY,'
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
    'Results': '(Resultkey INTEGER PRIMARY KEY,'
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
    'Addresses': '(Addresskey INTEGER PRIMARY KEY,'
                 ' name TEXT,'
                 ' street TEXT,'
                 ' code TEXT,'
                 ' city TEXT,'
                 ' country TEXT,'
                 ' phone TEXT,'
                 ' email TEXT,'
                 ' comment TEXT,'
                 ' me INTEGER)',
    'Colours': '(Colourkey INTEGER PRIMARY KEY,'
               ' colour TEXT UNIQUE)',
    'Racepoints': '(Racepointkey INTEGER PRIMARY KEY,'
                  ' racepoint TEXT UNIQUE,'
                  ' xco TEXT,'
                  ' yco TEXT,'
                  ' distance TEXT)',
    'Sectors': '(Sectorkey INTEGER PRIMARY KEY,'
               ' sector TEXT UNIQUE)',
    'Types': '(Typekey INTEGER PRIMARY KEY,'
             ' type TEXT UNIQUE)',
    'Categories': '(Categorykey INTEGER PRIMARY KEY,'
                  ' category TEXT UNIQUE)',
    'Strains': '(Strainkey INTEGER PRIMARY KEY,'
               ' strain TEXT UNIQUE)',
    'Lofts': '(Loftkey INTEGER PRIMARY KEY,'
             ' loft TEXT UNIQUE)',
    'Weather': '(Weatherkey INTEGER PRIMARY KEY,'
               ' weather TEXT UNIQUE)',
    'Wind': '(Windkey INTEGER PRIMARY KEY,'
            ' wind TEXT UNIQUE)',
    'Sold': '(Soldkey INTEGER PRIMARY KEY,'
            ' pindex TEXT,'
            ' person TEXT,'
            ' date TEXT,'
            ' info TEXT)',
    'Lost': '(Lostkey INTEGER PRIMARY KEY,'
            ' pindex TEXT,'
            ' racepoint TEXT,'
            ' date TEXT,'
            ' info TEXT)',
    'Dead': '(Deadkey INTEGER PRIMARY KEY,'
            ' pindex TEXT,'
            ' date TEXT,'
            ' info TEXT)',
    }

    def __init__(self):
        create_tables = False

        if not os.path.exists(const.DATABASE):
            create_tables = True

        if create_tables:
            conn, cursor = self.db_connect()
            for table_name, sql in self.SCHEMA.items():
                cursor.execute('CREATE TABLE IF NOT EXISTS %s %s' % (table_name, sql))
                conn.commit()
            conn.close()

    def db_connect(self):
        try:
            conn = sqlite3.connect(const.DATABASE.decode(const.ENCODING).encode("utf-8"))
        except Exception, e:
            import logdialog

            logger.critical("Could not connect to database")
            logger.critical(e)
            logger.debug("Databasedir: %s" %const.PREFDIR)
            logger.debug("Database: %s" %const.DATABASE)
            logger.debug("Databasedir exists: %s" %os.path.exists(const.PREFDIR))
            logger.debug("Database exists: %s" %os.path.exists(const.DATABASE))
            logger.debug("Databasedir writable: %s" %os.access(const.PREFDIR, os.W_OK))
            logger.debug("Database writable: %s" %os.access(const.DATABASE, os.W_OK))
            logger.debug("Encoding: %s" %sys.getfilesystemencoding())

            logdialog.LogDialog()
            sys.exit()

        conn.text_factory = str
        cursor = conn.cursor()
        return (conn, cursor)

#### Version
    def get_db_version(self):
        conn, cursor = self.db_connect()
        try: 
            cursor.execute('SELECT db_version FROM Version')
            data = cursor.fetchone()[0]
        except TypeError:
            # Firstrun
            data = 2
        except sqlite3.OperationalError:
            # Old database
            data = 0
        conn.close()
        return data

#### 
    def insert_db_version(self, version):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Version VALUES (null, ?)', (version, ))
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def add_table_from_schema(self, table):
        conn, cursor = self.db_connect()
        cursor.execute("CREATE TABLE IF NOT EXISTS %s %s" %(table, self.SCHEMA[table]))
        conn.commit()
        conn.close()

    def rename_table(self, old, new):
        conn, cursor = self.db_connect()
        cursor.execute("ALTER TABLE %s RENAME TO %s" %(old, new))
        conn.commit()
        conn.close()

    def copy_table(self, frm, to):
        conn, cursor = self.db_connect()
        cursor.execute("INSERT INTO %s SELECT * FROM %s" %(to, frm))
        conn.commit()
        conn.close()

    def copy_table2(self, frm, to):
        conn, cursor = self.db_connect()
        cursor.execute("INSERT INTO %s(Resultkey, pindex, date, point, place, out, sector) SELECT * FROM %s" %(to, frm))
        conn.commit()
        conn.close()

    def drop_table(self, table):
        conn, cursor = self.db_connect()
        cursor.execute("DROP TABLE %s" %table)
        conn.commit()
        conn.close()

#### Optimize
    def optimize_db(self):
        conn, cursor = self.db_connect()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()

#### Pigeons
    def insert_pigeon(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Pigeons VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def delete_pigeon(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Pigeons WHERE pindex=?', (pindex,))
        conn.commit()
        conn.close()

    def update_pigeon(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET pindex=?, band=?, year=?, sex=?, show=?, active=?, colour=?, name=?, strain=?, loft=?, image=?, sire=?, yearsire=?, dam=?, yeardam=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def update_pedigree_pigeon(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('UPDATE Pigeons SET pindex=?, band=?, year=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=? WHERE pindex=?', data)
        except sqlite3.IntegrityError:
            pass

        conn.commit()
        conn.close()

    def update_pigeon_sire(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET sire=?, yearsire=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def update_pigeon_dam(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET dam=?, yeardam=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def show_pigeon(self, band, value):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET show=? WHERE pindex=?', (value, band))
        conn.commit()
        conn.close()

    def get_pigeons(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Pigeons')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_pigeon(self, band):
        conn, cursor = self.db_connect()
        data = None
        for row in cursor.execute('SELECT * FROM Pigeons WHERE pindex=?', (band,)):
            data = row

        conn.close()
        return data

    def has_pigeon(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT COUNT(*) FROM Pigeons WHERE pindex=?', (band,))
        data = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        if data:
            return data[0]
        else:
            return None

    def get_image(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT image FROM Pigeons WHERE pindex=?', (pindex,))
        data = cursor.fetchone()[0]
        conn.close()
        return data

    def get_all_images(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT pindex, band, year, image FROM Pigeons')
        data = [image for image in cursor.fetchall()]
        conn.close()
        return data


#### Results
    def insert_result(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('INSERT INTO Results VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
        conn.commit()
        rowid = cursor.lastrowid
        conn.close()

        return rowid

    def delete_result_from_id(self, ID):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Results WHERE Resultkey=?', (ID,))
        conn.commit()
        conn.close()

    def delete_result_from_band(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Results WHERE pindex=?', (band,))
        conn.commit()
        conn.close()

    def update_result(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Results SET date=?, point=?, place=?, out=?, sector=?, type=?, category=?, wind=?, weather=?, put=?, back=?, ownplace=?, ownout=?, comment=? WHERE Resultkey=?', data)
        conn.commit()
        conn.close()

    def update_result_pindex(self, pindex, pindex_old):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Results SET pindex=? WHERE pindex=?', (pindex, pindex_old))
        conn.commit()
        conn.close()

    def get_all_results(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Results')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_pigeon_results(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Results WHERE pindex=?', (pindex,))
        data = cursor.fetchall()
        conn.close()
        return data

    def get_pigeon_results_at_date(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Results WHERE pindex=? AND date=?', data)
        data = cursor.fetchall()
        conn.close()
        return data

    def has_results(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT COUNT(*) FROM Results WHERE pindex=?', (pindex,))
        data = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        if data:
            return data[0]
        else:
            return None

#### Addresses
    def insert_address(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('INSERT INTO Addresses VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
        conn.commit()
        conn.close()

    def delete_address(self, name):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Addresses WHERE name=?', (name,))
        conn.commit()
        conn.close()

    def update_address(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Addresses SET name=?, street=?, code=?, city=?, country=?, phone=?, email=?, comment=?, me=? WHERE name=?', data)
        conn.commit()
        conn.close()

    def get_all_addresses(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Addresses')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_address(self, name):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Addresses WHERE name=?', (name,))
        data = cursor.fetchone()
        conn.close()
        return data

#### Colours
    def insert_colour(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Colours VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_colours(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Colours')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_colour(self, colour):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Colours WHERE colour=?', (colour,))
        conn.commit()
        conn.close()

#### Sectors
    def insert_sector(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Sectors VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_sectors(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Sectors')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_sector(self, sector):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Sectors WHERE sector=?', (sector,))
        conn.commit()
        conn.close()

#### Types
    def insert_type(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Types VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_types(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Types')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_type(self, ftype):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Types WHERE type=?', (ftype,))
        conn.commit()
        conn.close()

#### Categories
    def insert_category(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Categories VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_categories(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Categories')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_category(self, category):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Categories WHERE category=?', (category,))
        conn.commit()
        conn.close()

#### Racepoints
    def insert_racepoint(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Racepoints (Racepointkey, racepoint) VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_racepoints(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Racepoints')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_racepoint(self, racepoint):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Racepoints WHERE racepoint=?', (racepoint,))
        conn.commit()
        conn.close()

#### Weather
    def insert_weather(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Weather (Weatherkey, weather) VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_weather(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Weather')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_weather(self, weather):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Weather WHERE weather=?', (weather,))
        conn.commit()
        conn.close()

#### Wind
    def insert_wind(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Wind (Windkey, wind) VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_wind(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Wind')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_wind(self, wind):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Wind WHERE wind=?', (wind,))
        conn.commit()
        conn.close()

#### Strains
    def insert_strain(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Strains VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_strains(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Strains')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_strain(self, strain):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Strains WHERE strain=?', (strain,))
        conn.commit()
        conn.close()

#### Lofts
    def insert_loft(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Lofts VALUES (null, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def get_all_lofts(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Lofts')
        data = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return data

    def delete_loft(self, loft):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Lofts WHERE loft=?', (loft,))
        conn.commit()
        conn.close()

#### Status
    def delete_status(self, table, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM %s WHERE pindex=?' %table, (pindex,))
        conn.commit()
        conn.close()

#### Sold
    def insert_sold(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Sold VALUES (null, ?, ?, ?, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def update_sold(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Sold SET person=?, date=?, info=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def get_sold_data(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT person, date, info FROM Sold WHERE pindex=?', (pindex,))
        data = cursor.fetchone()
        conn.close()
        return data

    def delete_sold(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Sold WHERE pindex=?', (pindex,))
        conn.commit()
        conn.close()

#### Lost
    def insert_lost(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Lost VALUES (null, ?, ?, ?, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def update_lost(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Lost SET racepoint=?, date=?, info=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def get_lost_data(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT racepoint, date, info FROM Lost WHERE pindex=?', (pindex,))
        data = cursor.fetchone()
        conn.close()
        return data

    def delete_lost(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Lost WHERE pindex=?', (pindex,))
        conn.commit()
        conn.close()

#### Dead
    def insert_dead(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Dead VALUES (null, ?, ?, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def update_dead(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Dead SET date=?, info=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def get_dead_data(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT date, info FROM Dead WHERE pindex=?', (pindex,))
        data = cursor.fetchone()
        conn.close()
        return data

    def delete_dead(self, pindex):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Dead WHERE pindex=?', (pindex,))
        conn.commit()
        conn.close()

