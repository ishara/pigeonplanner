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

import nose.tools as nt
from peewee import SqliteDatabase

from . import utils
from pigeonplanner.database import session
from pigeonplanner.database import migrations
from pigeonplanner.database.manager import DBManager, DatabaseInfo, DatabaseInfoError
from pigeonplanner.core import const


def test_connection():
    nt.assert_equal(session.dbfile, const.DATABASE)
    nt.assert_false(session.is_new_db)
    nt.assert_is_instance(session.connection, SqliteDatabase)
test_connection.setup = session.open
test_connection.teardown = session.close

def test_new_database():
    nt.assert_equal(session.dbfile, utils.DBFILE)
    nt.assert_true(session.is_new_db)
test_new_database.setup = utils.open_test_db
test_new_database.teardown = utils.close_test_db

def test_database_version():
    nt.assert_false(session.needs_update())
    value = session.get_database_version()
    nt.assert_equal(value, migrations.get_latest_version())
    session.set_database_version(999)
    value = session.get_database_version()
    nt.assert_equal(value, 999)
test_database_version.setup = utils.open_test_db
test_database_version.teardown = utils.close_test_db


class TestDatabaseManager:
    def setUp(self):
        self._testfolder = os.path.realpath(".")
        self._old_const_path = const.DATABASEINFO
        const.DATABASEINFO = os.path.join(self._testfolder, "test_database.json")
        self.dbmanager = DBManager()

    def tearDown(self):
        os.remove(const.DATABASEINFO)
        const.DATABASEINFO = self._old_const_path

    def test_add(self):
        # Test simple add
        path = os.path.join(self._testfolder, "my_pigeonplanner_db.db")
        name = "TestDB"
        description = "My description"
        result = self.dbmanager.add(name, description, path)
        nt.assert_is_instance(result, DatabaseInfo)
        nt.assert_equal(result.path, path)
        nt.assert_equal(result.name, name)
        nt.assert_equal(result.description, description)
        nt.assert_in(result, self.dbmanager.get_databases())

        # Test empty name
        nt.assert_raises(DatabaseInfoError, self.dbmanager.add, "", "", "")

        # Test existing name
        nt.assert_raises(DatabaseInfoError, self.dbmanager.add, "TestDB", "", "")

    def test_create(self):
        # Test simple create
        path = self._testfolder
        name = "TestDB"
        description = "My description"
        result = self.dbmanager.create(name, description, path)
        nt.assert_is_instance(result, DatabaseInfo)
        nt.assert_true(result.path.startswith(path))
        nt.assert_true(result.path.endswith(".db"))
        nt.assert_equal(result.name, name)
        nt.assert_equal(result.description, description)
        nt.assert_in(result, self.dbmanager.get_databases())

        # Test empty name
        nt.assert_raises(DatabaseInfoError, self.dbmanager.create, "", "", path)

        # Test existing name
        nt.assert_raises(DatabaseInfoError, self.dbmanager.create, "TestDB", "", path)

        # Test empty path
        nt.assert_raises(DatabaseInfoError, self.dbmanager.create, "TestDB", "", "")

        # Clean up
        os.remove(result.path)

    def test_edit(self):
        # Test simple edit
        path = self._testfolder
        name = "TestDB"
        description = "My description"
        dbobj = self.dbmanager.create(name, description, path)

        path_new = os.path.join(self._testfolder, "my_pigeonplanner_db.db")
        name_new = "TestDB new"
        description_new = "My description new"
        result = self.dbmanager.edit(dbobj, name_new, description_new, path_new)
        nt.assert_is_instance(result, DatabaseInfo)
        nt.assert_equal(result.path, path_new)
        nt.assert_equal(result.name, name_new)
        nt.assert_equal(result.description, description_new)
        nt.assert_in(result, self.dbmanager.get_databases())

        # Test empty name
        nt.assert_raises(DatabaseInfoError, self.dbmanager.edit, result, "", "", path_new)

        # Test existing name
        name = self.dbmanager.get_databases()[0].name # grab name from the default database
        nt.assert_raises(DatabaseInfoError, self.dbmanager.edit, result, name, "", path_new)

        # Clean up
        os.remove(result.path)

    def test_delete(self):
        # Add a database to test
        path = self._testfolder
        name = "TestDB"
        description = "My description"
        dbobj = self.dbmanager.create(name, description, path)
        nt.assert_true(os.path.exists(dbobj.path))
        nt.assert_in(dbobj, self.dbmanager.get_databases())

        # Remove it
        self.dbmanager.delete(dbobj)
        nt.assert_false(os.path.exists(dbobj.path))
        nt.assert_not_in(dbobj, self.dbmanager.get_databases())

