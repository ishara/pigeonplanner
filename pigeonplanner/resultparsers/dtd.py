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
from test.test_strptime import StrptimeTests
from symbol import except_clause


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
            if number == 0:
                # Get Sector of the race. 
#                sector, garbage = line.split(None, 1)
                data['sector'] = line[:21]
            if number == 2:
                #TODO: This doesn't work if racepoint has multiple words
                # If an error occurs, it's mean that racepoint is composed of two words
#                racepoint, date, n_pigeons, catgory, garbage = line.split(None, 4)
#                try :
#                    day, month, year = date.split('-')
#                    dt = datetime.date(int("20"+year), int(month), int(day))
#                    data['racepoint'] = racepoint
#                    data['date'] = dt.strftime(const.DATE_FORMAT)
#                    data['n_pigeons'] = n_pigeons
#                    data['category'] = category
#                except ValueError:
#                    racepoint, racepoint2, date, n_pigeons, category, garbage = line.split(None, 5)
#                    day, month, year = date.split('-')
#                    dt = datetime.date(int("20"+year), int(month), int(day))
#                    data['racepoint'] = racepoint + " " + racepoint2
#                    data['date'] = dt.strftime(const.DATE_FORMAT)
#                    data['n_pigeons'] = n_pigeons
#                continue
                words= line.split()
                try :
                    racepoint = words[0]
                    date = words[1]
                    day, month, year = date.split('-')
                    dt = datetime.date(int("20"+year), int(month), int(day))
                    n_pigeons = words[2]
                    if words[4] == "LOS":
                        category = words[3]
                    else:
                        category = words[3] + " " + words[4]
                except ValueError:
                    racepoint = words[0]+" "+words[1]
                    date = words[2]
                    day, month, year = date.split('-')
                    dt = datetime.date(int("20"+year), int(month), int(day))
                    n_pigeons = words[3]
                    if words[5] == "LOS":
                        category = words[4]
                    else:
                        category = words[4] + " " + words[5]
                    
                    
                data['racepoint'] = racepoint
                data['date'] = dt.strftime(const.DATE_FORMAT)
                data['n_pigeons'] = n_pigeons
                data['category'] = category

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

