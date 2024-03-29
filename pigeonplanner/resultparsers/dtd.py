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

from yapsy.IPlugin import IPlugin

from pigeonplanner.core import const
from pigeonplanner.database.models import Pigeon


def expand_year(year):
    if len(year) == 4:
        return year
    return str(int(year) + 2000)


class DTDParser(IPlugin):
    def check(self, resultfile):
        for line in resultfile:
            line = line.lower()
            if "data technology-deerlijk" in line or "data technology deerlijk" in line:
                return True
        return False

    def parse_file(self, resultfile):
        data = {"sector": "", "category": "", "n_pigeons": "", "date": "", "racepoint": ""}
        results = {}
        firstline = -1
        revindex = -1
        for linenumber, line in enumerate(resultfile):
            # Remove all whitspace
            line = line.strip()

            # Don't parse empty lines or dashed lines(sometimes in front of file)
            if line == "" or line.startswith("----"):
                continue

            # Save the linenumber for the first real line
            if firstline < 0:
                firstline = linenumber

            # The first line contains:
            #    Name of club      Location of club      DATA TECHNOLOGY-DEERLIJK
            if linenumber == firstline:
                data["sector"] = line.split("  ")[0]

            # Split each line by a space
            items = line.split()

            # Information is on the third line:
            #    Racepoint       Date Pigeons Category     LOS TE-LACHES A : Hour
            # alt:  "              "     "       "         LOSTIJD/LACHER  :  "
            # alt:  "              "     "       "         deelnemers:N LOSTIJD:HOUR
            if linenumber == firstline + 2:
                # Go backwards through the line. The racepoint can have multiple
                # words, but "LOS" (or "LOSTIJD") is a fixed word.
                try:
                    losindex = items.index("LOS")
                except ValueError:
                    try:
                        losindex = items.index("LOSTIJD/LACHER")
                    except ValueError:
                        items2 = line.split(":")[0].split()
                        try:
                            losindex = items2.index("Deelnemers")
                        except ValueError:
                            losindex = items2.index("Amateurs")
                pigeonsindex = losindex - 2
                while not items[pigeonsindex].isdigit():
                    # Category can be 1 or more words long. Loop until the number of pigeons is found,
                    # then build the category string based on how many items in the list have passed.
                    # Possible categories: Oude, Oude duiven, Jonge R3, Oude + jaarse
                    pigeonsindex -= 1
                data["category"] = " ".join(items[pigeonsindex + 1 : losindex])
                data["n_pigeons"] = items[pigeonsindex]
                day, month, year = items[pigeonsindex - 1].split("-")
                dt = datetime.date(int(expand_year(year)), int(month), int(day))
                data["date"] = dt.strftime(const.DATE_FORMAT)
                # The remaining items before the date form the racepoint
                data["racepoint"] = " ".join(items[: pigeonsindex - 1])
                continue

            # We parse the lines from the end for easier column detection.
            # Usually the last column is the speed, but in some cases the position
            # column is duplicated at the end for readability. Detect this and move the
            # searchindex by one.
            # NR { }  NAAM { } GEMEENTE AD IG AFSTAND RING   JR BESTAT   SNELH.   {NR}
            if linenumber == firstline + 4:
                if items[-1] == "NR":
                    revindex -= 1
                continue

            # Only parse lines that start with a number (place)
            try:
                place = int(items[0])
            except ValueError:
                continue
            speed = items[revindex]
            ring, year = items[revindex - 3], items[revindex - 2]
            # If the year is 2 digits, no space exists between the ring and year
            if len(year) > 1:
                ring, year = year[:-2], year[-2:]
            year = expand_year(year)
            try:
                pigeon = Pigeon.get_for_band(("", "", ring, year))
                results[pigeon] = [ring, year, str(place), speed]
            except Pigeon.DoesNotExist:
                pass
        return data, results
