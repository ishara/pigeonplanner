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


import os.path
import sqlite3

import const


class DatabaseOperations:
    SCHEMA = {
    'Pigeons': '(Pigeonskey INTEGER PRIMARY KEY,'
               ' pindex TEXT UNIQUE,'
               ' band TEXT,'
               ' year TEXT,'
               ' sex TEXT,'
               ' show INTEGER,'
               ' alive INTEGER,'
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
               ' sector TEXT)',
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
                  ' xco INTEGER,'
                  ' yco INTEGER,'
                  ' distance INTEGER)',
    'Sectors': '(Sectorkey INTEGER PRIMARY KEY,'
               ' sector TEXT UNIQUE)',
    'Strains': '(Strainkey INTEGER PRIMARY KEY,'
               ' strain TEXT UNIQUE)',
    'Lofts': '(Loftkey INTEGER PRIMARY KEY,'
             ' loft TEXT UNIQUE)',
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
        conn = sqlite3.connect(const.DATABASE)
        conn.text_factory = str
        cursor = conn.cursor()
        return (conn, cursor)

#### Search
    def search_band(self, band):
        conn, cursor = self.db_connect()
        for row in cursor.execute('SELECT pindex, show FROM Pigeons WHERE band=?', (band,)).fetchall():
            yield row

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
        cursor.execute('UPDATE Pigeons SET pindex=?, band=?, year=?, sex=?, show=?, alive=?, colour=?, name=?, strain=?, loft=?, image=?, sire=?, yearsire=?, dam=?, yeardam=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=? WHERE pindex=?', data)
        conn.commit()
        conn.close()

    def update_pedigree_pigeon(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET pindex=?, band=?, year=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=? WHERE pindex=?', data)
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

    def get_image(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT image FROM Pigeons WHERE pindex=?', (band,))
        data = cursor.fetchone()[0]
        return data


#### Results
    def insert_result(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('INSERT INTO Results VALUES (null, ?, ?, ?, ?, ?, ?)', data)
        conn.commit()
        conn.close()

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
        cursor.execute('UPDATE Results SET date=?, point=?, place=?, out=?, sector=? WHERE Resultkey=?', data)
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

