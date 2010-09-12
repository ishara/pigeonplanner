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

"""
Provides an interface to draw the pedigree
"""


try:
    import cairo
    cairo_available = True
except:
    cairo_available = False

from pigeonplanner import const
from pigeonplanner import pedigree
from pigeonplanner.ui.widgets import pedigreeboxes


#FIXME: Cairo-drawn boxes don't show up on Mac OS X
if const.OSX:
    cairo_available = False

class DrawPedigree(object):
    def __init__(self, main=None, pedigree=None):
        self.main = main
        self.pedigree = pedigree

    def draw_pedigree(self, pigeons, tables, pindex=None, detailed=False):
        if detailed:
            rng = 31
            pos = [(),
                   ((0, 1, 7, 8), ((1,0,7),(1,8,7))),
                   ((0, 1, 7, 8), ((1,0,7),(1,8,7))),
                   ((2, 3, 3, 4), ((3,0,3),(3,4,3))),
                   ((2, 3, 11, 12), ((3,8,3),(3,12,3))),
                   ((2, 3, 3, 4), ((3,0,3),(3,4,3))),
                   ((2, 3, 11, 12), ((3,8,3),(3,12,3))),
                   ((4, 5, 1, 2), ((5,0,1),(5,2,1))),
                   ((4, 5, 5, 6), ((5,4,1),(5,6,1))),
                   ((4, 5, 9, 10), ((5,8,1),(5,10,1))),
                   ((4, 5, 13, 14), ((5,12,1),(5,14,1))),
                   ((4, 5, 1, 2), ((5,0,1),(5,2,1))),
                   ((4, 5, 5, 6), ((5,4,1),(5,6,1))),
                   ((4, 5, 9, 10), ((5,8,1),(5,10,1))),
                   ((4, 5, 13, 14), ((5,12,1),(5,14,1))),
                   ((6, 7, 0, 1), (None)),
                   ((6, 7, 2, 3), (None)),
                   ((6, 7, 4, 5), (None)),
                   ((6, 7, 6, 7), (None)),
                   ((6, 7, 8, 9), (None)),
                   ((6, 7, 10, 11), (None)),
                   ((6, 7, 12, 13), (None)),
                   ((6, 7, 14, 15), (None)),
                   ((6, 7, 0, 1), (None)),
                   ((6, 7, 2, 3), (None)),
                   ((6, 7, 4, 5), (None)),
                   ((6, 7, 6, 7), (None)),
                   ((6, 7, 8, 9), (None)),
                   ((6, 7, 10, 11), (None)),
                   ((6, 7, 12, 13), (None)),
                   ((6, 7, 14, 15), (None))]
        else:
            rng = 15
            pos = [(),
                   ((0, 1, 4, 5), ((1,0,3),(1,5,3))),
                   ((0, 1, 4, 5), ((1,0,3),(1,5,3))),
                   ((2, 3, 1, 2), ((3,0,1),(3,2,1))),
                   ((2, 3, 6, 7), ((3,5,1),(3,7,1))),
                   ((2, 3, 1, 2), ((3,0,1),(3,2,1))),
                   ((2, 3, 6, 7), ((3,5,1),(3,7,1))),
                   ((4, 5, 0, 1), None), ((4, 5, 2, 3), None),
                   ((4, 5, 5, 6), None), ((4, 5, 7, 8), None),
                   ((4, 5, 0, 1), None), ((4, 5, 2, 3), None),
                   ((4, 5, 5, 6), None), ((4, 5, 7, 8), None)]

        lst = [None]*rng

        try:
            ring = pigeons[pindex].ring
            year = pigeons[pindex].year
            sex = pigeons[pindex].sex
        except KeyError:
            ring = ''
            year = ''
            sex = ''

        pedigree.build_tree(pigeons, pindex, ring, year, sex, '', '',
                            '', '', '', '', 0, 1, lst)

        for table in tables:
            for child in table.get_children():
                child.destroy()

        for i in range(1, rng):
            x = pos[i][0][0]
            y = pos[i][0][1]
            w = pos[i][0][2]
            h = pos[i][0][3]

            table = tables[0]
            if i in [2, 5, 6, 11, 12, 13, 14, 23, 24, 25, 26, 27, 28, 29, 30]:
                table = tables[1]

            height, attach = 0, 0
            if detailed:
                if i <= 6:
                    height = 6
                    attach = 4
                elif i >= 7 and i <= 14:
                    height = 3
                    attach = 2
                else:
                    height = 1
                    attach = 1

            if i%2 == 1:
                sex = '0'
            else:
                sex = '1'

            try:
                kinfo = lst[(i - (int(sex) + 1)) / 2]
            except TypeError:
                kinfo = None

            extrabox = None
            if not lst[i]:
                # No pigeon here, set empty values
                pindex = ''
                ring = ''
                year = ''
                extra = ''
            else:
                # There is a pigeon, set correct values
                pindex = lst[i][0]
                ring = lst[i][1]
                year = lst[i][2]
                sex = lst[i][3]
                extra = [lst[i][4], lst[i][5], lst[i][6], lst[i][7],
                         lst[i][8], lst[i][9]]

            if detailed:
                if cairo_available:
                    extrabox = pedigreeboxes.ExtraBox_cairo(extra, height)
                else:
                    extrabox = pedigreeboxes.ExtraBox(extra, height)
                table.attach(extrabox, x, y, w+1, h+attach)

            if cairo_available:
                box = pedigreeboxes.PedigreeBox_cairo(pindex, ring, year,
                                                      sex, extra,
                                                      kinfo, detailed,
                                                      self.main, self)
            else:
                box = pedigreeboxes.PedigreeBox(pindex, ring, year, sex, extra,
                                                kinfo, detailed,
                                                self.main, self)
            table.attach(box, x, y, w, h)

            if pos[i][1]:
                cross = pedigreeboxes.PedigreeCross()
                table.attach(cross, x+1, x+2, h-1, h)

                x = pos[i][1][0][0]
                y = pos[i][1][0][1]
                w = 1
                h = pos[i][1][0][2]
                line_up = pedigreeboxes.PedigreeLine()
                line_up.set_data("idx", i*2+1)
                table.attach(line_up, x, x+w, y, y+h)
                
                x = pos[i][1][1][0]
                y = pos[i][1][1][1]
                w = 1
                h = pos[i][1][1][2]
                line_down = pedigreeboxes.PedigreeLine()
                line_down.set_data("idx", i*2+2)
                line_down.set_data("height", h)
                table.attach(line_down, x, x+w, y, y+h)

        for table in tables:
            table.show_all()

