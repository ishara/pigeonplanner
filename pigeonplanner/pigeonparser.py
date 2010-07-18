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
Parser to get all pigeons
"""


import database


class PigeonParser:
    def __init__(self):
        self.database = database.DatabaseOperations()

    def get_pigeons(self):
        self.pigeons = {}
        for pigeon in self.database.get_pigeons():
            p = ParsedPigeon(pigeon[1],
                             pigeon[2],
                             pigeon[3],
                             pigeon[4],
                             pigeon[5],
                             pigeon[6],
                             pigeon[7],
                             pigeon[8],
                             pigeon[9],
                             pigeon[10],
                             pigeon[11],
                             pigeon[12],
                             pigeon[13],
                             pigeon[14],
                             pigeon[15],
                             pigeon[16],
                             pigeon[17],
                             pigeon[18],
                             pigeon[19],
                             pigeon[20],
                             pigeon[21])

            self.pigeons[p.pindex] = p


class ParsedPigeon:
    def __init__(self, pindex, ring, year, sex, show, active, colour='',
                 name='', strain='', loft='', image='', sire='', yearsire='',
                 dam='', yeardam='', extra1='', extra2='', extra3='',
                 extra4='', extra5='', extra6=''):
        self.pindex = pindex
        self.ring = ring
        self.year = year
        self.sex = sex
        self.show = show
        self.active = active
        self.colour = colour
        self.name = name
        self.strain = strain
        self.loft = loft
        self.image = image
        self.sire = sire
        self.yearsire = yearsire
        self.dam = dam
        self.yeardam = yeardam
        self.extra1 = extra1
        self.extra2 = extra2
        self.extra3 = extra3
        self.extra4 = extra4
        self.extra5 = extra5
        self.extra6 = extra6

