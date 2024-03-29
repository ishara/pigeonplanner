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
import sys
import glob
from importlib import import_module

from pigeonplanner.core import const

_migrations = None


def get_filenames():
    """Get a sorted list of migration filenames"""
    if const.IS_FROZEN:
        folder = const.MIGRATIONSDIR
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(folder, "[0-9][0-9][0-9]_*.py"))
    filenames = [os.path.splitext(os.path.basename(f))[0] for f in files]
    return sorted(filenames, key=lambda fname: int(fname.split("_", 1)[0]))


def get_migrations():
    """Get a sorted list of dicts of migrations.
    The dicts contain a version and module key.
    """
    global _migrations
    if _migrations is None:
        _migrations = []
        for module_name in get_filenames():
            if const.IS_FROZEN:
                module_path = module_name
            else:
                module_path = "pigeonplanner.database.migrations.%s" % module_name
            module = import_module(module_path)
            _migrations.append({"version": module.database_version, "module": module})
    return _migrations


def get_latest_version():
    return get_migrations()[-1]["version"]
