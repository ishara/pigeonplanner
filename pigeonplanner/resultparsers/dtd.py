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


import datetime

import const
import common
from baseparser import BaseParser
from translation import gettext as _


def expand_year(year):
    if len(year) == 4:
        return year
    year = int(year)
    return str(year+2000)


class DTDParser(BaseParser):
    name = _("Data Technology-Deerlijk - Belgium")
    description = _("Data Technology-Deerlijk")

    def parse_file(self, resultfile, pindexlist):
        data = {}
        results = {}
        for number, line in enumerate(resultfile):
            if number == 2:
                #TODO: This doesn't work if racepoint has multiple words
                racepoint, date, n_pigeons, garbage = line.split(None, 3)
                day, month, year = date.split('-')
                dt = datetime.date(int("20"+year), int(month), int(day))
                data['racepoint'] = racepoint
                data['date'] = dt.strftime(const.DATE_FORMAT)
                data['n_pigeons'] = n_pigeons
                continue
            line = line.split()
            # Only parse lines that start with a number (place)
            try:
                place = int(line[0])
            except ValueError:
                continue
            ring, year = line[-4], line[-3]
            # If the year is 2 digits, no space exists between the ring and year
            if len(year) > 1:
                ring, year = year[:-2], year[-2:]
            year = expand_year(year)
            pindex = common.get_pindex_from_band(ring, year)
            if pindex in pindexlist:
                results[pindex] = [ring, year, place]
        return data, results

