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


from . import utils
from pigeonplanner.core import common


__all__ = ["ExportCSV"]


class ExportCSV(object):
    name = "CSV"
    extension = ".csv"
    filefilter = ("CSV", "*.csv")

    @classmethod
    def run(cls, filepath, pigeons):
        with open(filepath, "wb") as output:
            writer = common.UnicodeWriter(output, fieldnames=utils.COLS_PIGEON)
            writer.writerow(dict((name, name) for name in utils.COLS_PIGEON))
            for pigeon in pigeons:
                writer.writerow({
                    "band": pigeon.band,
                    "country": pigeon.band_country,
                    "letters": pigeon.band_letters,
                    "number": pigeon.band_number,
                    "year": pigeon.band_year,
                    "sex": pigeon.sex,
                    "visible": pigeon.visible,
                    "status": pigeon.status_id,
                    "colour": pigeon.colour,
                    "name": pigeon.name,
                    "strain": pigeon.strain,
                    "loft": pigeon.loft,
                    "image": "" if pigeon.main_image is None else pigeon.main_image,
                    "sire": "" if pigeon.sire is None else pigeon.sire.band,
                    "dam": "" if pigeon.dam is None else pigeon.dam.band,
                    "extra1": pigeon.extra1,
                    "extra2": pigeon.extra2,
                    "extra3": pigeon.extra3,
                    "extra4": pigeon.extra4,
                    "extra5": pigeon.extra5,
                    "extra6": pigeon.extra6
                })
