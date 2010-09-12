# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Parts taken and inspired by Gramps

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


from pigeonplanner import common


def build_tree(pigeons, pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6,
               index, depth, lst):
    if depth > 5 or ring == None or index >= len(lst):
        return

    lst[index] = (pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6)

    if pindex in pigeons:
        ringSire = pigeons[pindex].sire
        yearSire = pigeons[pindex].yearsire
        pindexsire = common.get_pindex_from_band(ringSire, yearSire)
        try:
            extra1 = pigeons[pindexsire].extra1
            extra2 = pigeons[pindexsire].extra2
            extra3 = pigeons[pindexsire].extra3
            extra4 = pigeons[pindexsire].extra4
            extra5 = pigeons[pindexsire].extra5
            extra6 = pigeons[pindexsire].extra6
        except KeyError:
            extra1 = ''
            extra2 = ''
            extra3 = ''
            extra4 = ''
            extra5 = ''
            extra6 = ''

        if ringSire:
            build_tree(pigeons, pindexsire, ringSire, yearSire, '0', extra1,
                       extra2, extra3, extra4, extra5, extra6,
                       (2*index)+1, depth+1, lst)

        ringDam = pigeons[pindex].dam
        yearDam = pigeons[pindex].yeardam
        pindexdam = common.get_pindex_from_band(ringDam, yearDam)
        try:
            extra1 = pigeons[pindexdam].extra1
            extra2 = pigeons[pindexdam].extra2
            extra3 = pigeons[pindexdam].extra3
            extra4 = pigeons[pindexdam].extra4
            extra5 = pigeons[pindexdam].extra5
            extra6 = pigeons[pindexdam].extra6
        except KeyError:
            extra1 = ''
            extra2 = ''
            extra3 = ''
            extra4 = ''
            extra5 = ''
            extra6 = ''

        if ringDam:
            build_tree(pigeons, pindexdam, ringDam, yearDam, '1', extra1,
                       extra2, extra3, extra4, extra5, extra6,
                       (2*index)+2, depth+1, lst)

