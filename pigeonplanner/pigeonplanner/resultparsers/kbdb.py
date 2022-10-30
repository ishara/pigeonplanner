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
import re
import json
import datetime

from yapsy.IPlugin import IPlugin

from pigeonplanner.core import const
from pigeonplanner.database.models import Pigeon


class KDBDParser(IPlugin):
    def __init__(self):
        super().__init__()

        self.results = {}
        self.race_data = {}

    def check(self, resultfile):  # noqa
        if not os.path.splitext(resultfile.name)[1] == ".html":
            return False
        if "<title>KBDB/RFCB-Admin</title>" not in resultfile.read():
            return False
        return True

    def scrape_race_data(self, html):
        # Normally we'd use a proper HTML parser like BeautifulSoup to scrape the HTML looking
        # for the data we need, but the website is made by someone with no understanding of how
        # to use HTML so we're going with a dirty solution as well.
        # The wanted data is within a table with just one row and cell, all including line breaks
        # and formatting tags.

        found = re.search(r"> (.*) - (.*) - (.*) - (.*?)<", html)
        if found is None:
            raise ValueError
        racepoint, date, _, sector = found.groups()

        found = re.search(r"Aantal (\w*).* (\d*) <", html)
        if found is None:
            raise ValueError
        category, n_pigeons = found.groups()

        dt = datetime.datetime.strptime(date, "%d-%m-%y")
        date = dt.strftime(const.DATE_FORMAT)

        self.race_data = {
            "sector": sector,
            "category": category,
            "n_pigeons": n_pigeons,
            "date": date,
            "racepoint": racepoint,
        }

    def scrape_results(self, html):
        found = re.search(r"var data = (.*);", html)
        if found is None:
            raise ValueError("No results found.")
        raw_results = json.loads(found.group(1))
        for result in raw_results:
            full_ring = result["Ringnummer"]
            ring = full_ring[:-2]
            year = "20%s" % full_ring[-2:]
            place = result["Plaats"]
            speed = result["Snelheid"]
            try:
                pigeon = Pigeon.get_for_band(("", "", ring, year))
                self.results[pigeon] = [ring, year, str(place), speed]
            except Pigeon.DoesNotExist:
                pass

    def parse_file(self, resultfile):
        html = resultfile.read()
        self.scrape_race_data(html)
        self.scrape_results(html)
        return self.race_data, self.results
