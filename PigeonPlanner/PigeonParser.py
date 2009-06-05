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


import ConfigParser

import Const


class PigeonParser:
    def __init__(self):
        self.pigeon = ConfigParser.SafeConfigParser()
        self.read_pigeonfile()

    def read_pigeonfile(self):
        self.pigeon.read(Const.PIGEONFILE)

    def get_pigeons(self):
        self.pigeons = {}
        sections = self.pigeon.sections()

        for pigeon in sections:
            try:
                p = ParsedPigeon(self.pigeon.get(pigeon,'ring'),
                                 self.pigeon.get(pigeon,'year'),
                                 self.pigeon.get(pigeon,'sex'),
                                 self.pigeon.getboolean(pigeon,'show'),
                                 self.pigeon.get(pigeon,'extra1'),
                                 self.pigeon.get(pigeon,'extra2'),
                                 self.pigeon.get(pigeon,'extra3'),
                                 self.pigeon.get(pigeon,'extra4'),
                                 self.pigeon.get(pigeon,'extra5'),
                                 self.pigeon.get(pigeon,'extra6'),
                                 self.pigeon.get(pigeon,'name'),
                                 self.pigeon.get(pigeon,'colour'),
                                 self.pigeon.get(pigeon,'strain'),
                                 self.pigeon.get(pigeon,'loft'),
                                 self.pigeon.get(pigeon,'image'),
                                 self.pigeon.get(pigeon,'sire'),
                                 self.pigeon.get(pigeon,'yearsire'),
                                 self.pigeon.get(pigeon,'dam'),
                                 self.pigeon.get(pigeon,'yeardam'))

                self.pigeons[p.ring] = p
            except ConfigParser.NoOptionError, msg: #
                print msg


class ParsedPigeon:
    def __init__(self, ring, year, sex, show, extra1='', extra2='', extra3='', extra4='', extra5='', extra6='', name='', colour='', strain= '', loft='', image='', sire='', yearsire='', dam='', yeardam=''):
        self.ring = ring
        self.year = year
        self.name = name
        self.colour = colour
        self.strain = strain
        self.loft = loft
        self.sex = sex
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
        self.show = show

