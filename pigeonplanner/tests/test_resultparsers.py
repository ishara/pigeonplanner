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


import nose.tools as nt
from yapsy.PluginManager import PluginManager

from . import utils
from pigeonplanner.core import const
from pigeonplanner.core import enums
from pigeonplanner.database.models import Pigeon

manager = PluginManager()
manager.setPluginPlaces([const.RESULTPARSERDIR])
manager.collectPlugins()

def test_dtd():
    data1 = {"band_number": "1234567", "band_year": "2013", "sex": enums.Sex.cock}
    pigeon1 = Pigeon.create(**data1)
    data2 = {"band_number": "1234568", "band_year": "2013", "sex": enums.Sex.cock}
    pigeon2 = Pigeon.create(**data2)

    parser = manager.getPluginByName("Data Technology-Deerlijk").plugin_object

    filedata = {"sector": "HET LOKAAL", "category": "JONGE",
                "racepoint": "FONTENAY SUR EURE", "date": "2013-05-25", "n_pigeons": "247"}
    fileresults = {pigeon1: ["1234567", "2013", 1, "1397,00"],
                   pigeon2: ["1234568", "2013", 3, "1369,40"]}
    # 2 word sector, 3 word racepoint
    with open("tests/data/result_dtd_1.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    #TODO
#    nt.assert_dict_equal(results, fileresults)
    # Same as previous test, prepended empty lines and seperator dashes
    with open("tests/data/result_dtd_2.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # Same as previous tests, 1 word racepoint
    filedata["racepoint"] = "CHIMAY"
    with open("tests/data/result_dtd_3.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # Bogus header, needs to fail
    with open("tests/data/result_dtd_4.txt") as resultfile:
        nt.assert_raises(ValueError, parser.parse_file, resultfile)
    # 2 word category
    filedata["category"] = "JONGE R3"
    with open("tests/data/result_dtd_5.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # Extra column at the end
    filedata["category"] = "JONGEN"
    filedata["n_pigeons"] = "66"
    filedata["racepoint"] = "LA SOUTERRAINE"
    with open("tests/data/result_dtd_6.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # Newer header with participants and different "LOSTIJD" in header
    filedata["category"] = "Oude Duiven"
    filedata["n_pigeons"] = "120"
    filedata["racepoint"] = "CHIMAY-industrie"
    with open("tests/data/result_dtd_7.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # French header
    filedata["category"] = "JEUNES"
    filedata["n_pigeons"] = "110"
    filedata["racepoint"] = "ARGENTON"
    with open("tests/data/result_dtd_8.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)
    # 3 word category
    filedata["category"] = "Oude + jaarse"
    filedata["n_pigeons"] = "839"
    filedata["racepoint"] = "ARRAS"
    filedata["date"] = "2021-04-24"
    with open("tests/data/result_dtd_9.txt") as resultfile:
        data, results = parser.parse_file(resultfile)
    nt.assert_dict_equal(data, filedata)

def test_kbdb_scrape_race_data():
    parser = manager.getPluginByName("KBDB online").plugin_object

    html_files = [
        "tests/data/result_kbdb_1.html",
        "tests/data/result_kbdb_2.html",
        "tests/data/result_kbdb_3.html",
    ]
    race_datas = [
        {"sector": "Nationaal", "category": "oude", "n_pigeons": "9469", "date": "2020-07-25",
         "racepoint": "LA SOUTERRAINE"},
        {"sector": "PE Limburg", "category": "jaarse", "n_pigeons": "1736", "date": "2020-07-25",
         "racepoint": "LA SOUTERRAINE"},
        {"sector": "SPE Henegouwen/Waals-Brabant", "category": "oude", "n_pigeons": "863", "date": "2020-07-24",
         "racepoint": "MONTELIMAR"}
    ]
    for html_file, race_data in zip(html_files, race_datas):
        with open(html_file) as f:
            html = f.read()

        parser.scrape_race_data(html)
        nt.assert_dict_equal(parser.race_data, race_data)


def test_kbdb_parse_results():
    pigeon1_data = {"band_number": "1234567", "band_year": "2013", "sex": enums.Sex.cock}
    pigeon1 = Pigeon.create(**pigeon1_data)

    html_file = "tests/data/result_kbdb_1.html"
    with open(html_file) as f:
        html = f.read()
    parser = manager.getPluginByName("KBDB online").plugin_object
    parser.scrape_results(html)
    nt.assert_in(pigeon1, parser.results)
    nt.assert_list_equal(parser.results[pigeon1], ["1234567", "2013", "2", "1661.3061"])


test_dtd.setup = utils.open_test_db
test_dtd.teardown = utils.close_test_db
test_kbdb_parse_results.setup = utils.open_test_db
test_kbdb_parse_results.teardown = utils.close_test_db
