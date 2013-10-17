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


import sqlite3

import nose.tools as nt
from . import utils

from pigeonplanner import database
from pigeonplanner.core import const


def test_connection():
    nt.assert_equal(database.session.dbfile, const.DATABASE)
    nt.assert_false(database.session.is_new_db)
    nt.assert_is_instance(database.session.connection, sqlite3.Connection)
    nt.assert_is_instance(database.session.cursor, sqlite3.Cursor)
test_connection.setup = database.session.open
test_connection.teardown = database.session.close

def test_new_database():
    nt.assert_equal(database.session.dbfile, utils.DBFILE)
    nt.assert_true(database.session.is_new_db)
test_new_database.setup = utils.open_test_db
test_new_database.teardown = utils.close_test_db

