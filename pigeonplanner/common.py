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


import gobject


def count_active_pigeons(database):
    cocks = 0
    hens = 0
    ybirds = 0
    total = 0
    for pigeon in database.get_pigeons():
        if not pigeon[5]: continue

        total += 1

        if pigeon[4] == '0':
            cocks += 1
        elif pigeon[4] == '1':
            hens += 1
        elif pigeon[4] == '2':
            ybirds += 1

    return total, cocks, hens, ybirds

def add_statusbar_message(statusbar, message):
    statusbar.pop(0)
    statusbar.push(0, message)
    gobject.timeout_add_seconds(4, pop_statusbar_message, statusbar)

def pop_statusbar_message(statusbar):
    statusbar.pop(0)
    return False
