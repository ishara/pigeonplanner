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

import Const


class DatabaseOperations:
    SCHEMA = {
    'Pigeons': '(Pigeonskey INTEGER PRIMARY KEY,'
               ' band TEXT UNIQUE,'
               ' year TEXT,'
               ' sex TEXT,'
               ' show INTEGER,'
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
               ' pigeon TEXT,'
               ' date TEXT,'
               ' point TEXT,'
               ' place INTEGER,'
               ' out INTEGER,'
               ' sector TEXT)',
    'Colours': '(Colourkey INTEGER PRIMARY KEY,'
               ' colour TEXT UNIQUE, '
               ' distance TEXT)',
    'Racepoints': '(Racepointkey INTEGER PRIMARY KEY,'
                  ' racepoint TEXT UNIQUE)',
    'Sectors': '(Sectorkey INTEGER PRIMARY KEY,'
               ' sector TEXT UNIQUE)',
    'Strains': '(Strainkey INTEGER PRIMARY KEY,'
               ' strain TEXT UNIQUE)',
    'Lofts': '(Loftkey INTEGER PRIMARY KEY,'
             ' loft TEXT UNIQUE)',
    }

    def __init__(self):
        create_tables = False

        if not os.path.exists(Const.DATABASE):
            create_tables = True

        if create_tables:
            conn, cursor = self.db_connect()
            for table_name, sql in self.SCHEMA.iteritems():
                cursor.execute('CREATE TABLE IF NOT EXISTS %s %s' % (table_name, sql))
                conn.commit()
            conn.close()

    def db_connect(self):
        conn = sqlite3.connect(Const.DATABASE)
        cursor = conn.cursor()
        return (conn, cursor)

    def insert_pigeon(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Pigeons VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()

    def delete_pigeon(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Pigeons WHERE band=?', (band,))
        conn.commit()
        conn.close()

    def update_pigeon(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET band=?, year=?, sex=?, show=?, colour=?, name=?, strain=?, loft=?, image=?, sire=?, yearsire=?, dam=?, yeardam=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=? WHERE band=?', data)
        conn.commit()
        conn.close()

    def show_pigeon(self, band, value):
        conn, cursor = self.db_connect()
        cursor.execute('UPDATE Pigeons SET show=? WHERE band=?', (value, band))
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
        for row in cursor.execute('SELECT * FROM Pigeons WHERE band=?', (band,)):
            data = row

        conn.close()
        return data

    def has_pigeon(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT COUNT(*) FROM Pigeons WHERE band=?', (band,))
        data = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        if data:
            return data[0]
        else:
            return None

    def get_image(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT image FROM Pigeons WHERE band=?', (band,))
        data = cursor.fetchone()[0]
        return data


#### Results
    def insert_result(self, data):
        conn, cursor = self.db_connect()
        cursor.execute('INSERT INTO Results VALUES (null, ?, ?, ?, ?, ?, ?)', data)
        conn.commit()
        conn.close()

    def delete_result(self, ID):
        conn, cursor = self.db_connect()
        cursor.execute('DELETE FROM Results WHERE Resultkey=?', (ID,))
        conn.commit()
        conn.close()

#    def update_result(self, data):
#        conn, cursor = self.db_connect()
#        cursor.execute('UPDATE Results SET pigeon=?, date=?, point=?, place=?, out=?, sector=? WHERE Resultkey=?', data)
#        conn.commit()
#        conn.close()

    def get_all_results(self):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Results')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_pigeon_results(self, band):
        conn, cursor = self.db_connect()
        cursor.execute('SELECT * FROM Results WHERE pigeon=?', (band,))
        data = cursor.fetchall()
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

#### Racepoints
    def insert_racepoint(self, data):
        conn, cursor = self.db_connect()
        try:
            cursor.execute('INSERT INTO Racepoints VALUES (null, ?)', data)
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

