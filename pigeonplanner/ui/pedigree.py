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


import gtk
try:
    import cairo
    cairo_available = True
except:
    cairo_available = False

from pigeonplanner import const
from pigeonplanner import messages
from pigeonplanner.ui import dialogs
from pigeonplanner.ui.widgets import menus
from pigeonplanner.ui.widgets import pedigreeboxes
from pigeonplanner.ui.detailsview import DetailsDialog


#FIXME: Cairo-drawn boxes don't show up on Mac OS X
if const.OSX:
    cairo_available = False


def build_tree(parser, pigeon, index, depth, lst):
    if depth > 5 or pigeon is None or index >= len(lst):
        return

    lst[index] = pigeon
    pindex = pigeon.get_pindex()
    if pindex in parser.get_pigeons():
        sire , dam = parser.get_parents(pigeon)
        build_tree(parser, sire, (2*index)+1, depth+1, lst)
        build_tree(parser, dam, (2*index)+2, depth+1, lst)


class DrawPedigree(object):
    def __init__(self, database, parser, treeview=None):
        self.database = database
        self.parser = parser
        self.treeview = treeview

        self.tables = None
        self.pigeon = None

    # Callbacks
    def on_button_press(self, box, event, detailed):
        parent = box.get_toplevel()
        entries = None
        if detailed:
            if not box.editable:
                return
            if event.button == 1:
                self._edit_pigeon_details(None, box.pigeon, box.child,
                                          box.get_sex(), parent)
            elif event.button == 3:
                entries = [(gtk.STOCK_EDIT, self._edit_pigeon_details,
                            (box.pigeon, box.child, box.get_sex(), parent))]
                if box.pigeon is not None:
                    entries.insert(0, (gtk.STOCK_INFO, self._show_pigeon_details,
                                                       (box.pigeon, parent)))
                    if not box.pigeon.get_visible():
                        entries.append((gtk.STOCK_CLEAR, self._clear_box,
                                        (box.pigeon, box.child)))
                        entries.append((gtk.STOCK_REMOVE, self._remove_pigeon,
                                        (box.pigeon, box.child)))
        else:
            if box.textlayout.get_text() == '':
                return
            box.set_highlight(True)
            box.grab_focus()
            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                self._show_pigeon_details(None, box.pigeon, parent)
            elif event.button == 3:
                entries = [
                           (gtk.STOCK_INFO, self._show_pigeon_details,
                                            (box.pigeon, parent)),
                           (gtk.STOCK_JUMP_TO, self._select_pigeon,
                                               (box.pigeon, parent)),
                          ]
        if entries is not None:
            menus.popup_menu(event, entries)

    def on_edit_finished(self, detailsview, pigeon, operation):
        child = detailsview.get_child()
        self._edit_child(pigeon, child)
        self._redraw()

    # Public methods
    def draw_pedigree(self, tables, pigeon=None, detailed=False):
        self.pigeon = pigeon
        if detailed:
            # Only save the tables when in the detailed window. Otherwise
            # these will be overwritten when a reselect of a pigeon happens
            # in the _redraw method.
            self.tables = tables
            pos = [
                   ((0, 7, 8), ((0,7),(8,7))),
                   ((2, 3, 4), ((0,3),(4,3))),
                   ((2, 11, 12), ((8,3),(12,3))),
                   ((4, 1, 2), ((0,1),(2,1))),
                   ((4, 5, 6), ((4,1),(6,1))),
                   ((4, 9, 10), ((8,1),(10,1))),
                   ((4, 13, 14), ((12,1),(14,1))),
                   ((6, 0, 1), (None)),
                   ((6, 2, 3), (None)),
                   ((6, 4, 5), (None)),
                   ((6, 6, 7), (None)),
                   ((6, 8, 9), (None)),
                   ((6, 10, 11), (None)),
                   ((6, 12, 13), (None)),
                   ((6, 14, 15), (None)),
                ]
        else:
            pos = [
                   ((0, 4, 5), ((0,3),(5,3))),
                   ((2, 1, 2), ((0,1),(2,1))),
                   ((2, 6, 7), ((5,1),(7,1))),
                   ((4, 0, 1), None), ((4, 2, 3), None),
                   ((4, 5, 6), None), ((4, 7, 8), None),
                ]

        lstsire = [None]*len(pos)
        lstdam = [None]*len(pos)
        if pigeon is not None:
            sire , dam = self.parser.get_parents(pigeon)
            build_tree(self.parser, sire, 0, 1, lstsire)
            build_tree(self.parser, dam, 0, 1, lstdam)
        self._draw(tables[0], pos, lstsire, const.SIRE, detailed)
        self._draw(tables[1], pos, lstdam, const.DAM, detailed)

    # Internal methods
    def _draw(self, table, positions, lst, sex, detailed):
        for child in table.get_children():
            child.destroy()

        for index, position in enumerate(positions):
            try:
                x = position[0][0]
                y = x + 1
                w = position[0][1]
                h = position[0][2]
            except IndexError:
                continue

            pigeon = lst[index]
            child = self.pigeon if index == 0 else lst[(index - 1) / 2]

            if cairo_available:
                box = pedigreeboxes.PedigreeBox_cairo(pigeon, child, detailed)
            else:
                 box = pedigreeboxes.PedigreeBox(pigeon, child, detailed)
            box.set_sex(0 if (index%2 == 1 or (index == 0 and sex == const.SIRE)) else 1)
            box.connect("button-press-event", self.on_button_press, detailed)
            table.attach(box, x, y, w, h)

            if detailed:
                if index <= 2:
                    lines = 6
                    attach = 4
                elif index >= 3 and index <= 6:
                    lines = 3
                    attach = 2
                else:
                    lines = 1
                    attach = 1
                if cairo_available:
                    extrabox = pedigreeboxes.ExtraBox_cairo(pigeon, lines)
                else:
                    extrabox = pedigreeboxes.ExtraBox(pigeon, lines)
                table.attach(extrabox, x, y, w+1, h+attach)

            if position[1]:
                left = x+1
                right = left+1
                cross = pedigreeboxes.PedigreeCross()
                table.attach(cross, left, right, w, h)

                y = position[1][0][0]
                h = position[1][0][1]
                line_up = pedigreeboxes.PedigreeLine()
                line_up.set_data("idx", index*2+1)
                table.attach(line_up, left, right, y, y+h)

                y = position[1][1][0]
                h = position[1][1][1]
                line_down = pedigreeboxes.PedigreeLine()
                line_down.set_data("idx", index*2+2)
                table.attach(line_down, left, right, y, y+h)

        table.show_all()

    def _show_pigeon_details(self, widget, pigeon, parent):
        if not pigeon.get_pindex() in self.parser.pigeons:
            return
        DetailsDialog(self.database, self.parser, pigeon, parent)

    def _edit_pigeon_details(self, widget, pigeon, child, sex, parent):
        mode = const.ADD if pigeon is None else const.EDIT
        dialog = DetailsDialog(self.database, self.parser, pigeon, parent, mode)
        dialog.details.set_child(child)
        dialog.details.set_pedigree_mode(True)
        dialog.details.set_sex(sex)
        dialog.details.connect('edit-finished', self.on_edit_finished)

    def _select_pigeon(self, widget, pigeon, parent):
        pindex = pigeon.get_pindex()
        if not self.treeview.select_pigeon(None, pindex):
            dialogs.MessageDialog(const.INFO, messages.MSG_NO_PIGEON, parent)

    def _edit_child(self, pigeon, child, clear=False):
        if clear:
            band, year = '', ''
        else:
            band, year = pigeon.get_band()
        startcol = 12 if pigeon.get_sex() == '0' else 14
        pindex = child.get_pindex()
        self.database.update_table(self.database.PIGEONS,
                                   (band, year, pindex), startcol, 1)
        self.parser.update_pigeon(pindex)

    def _clear_box(self, widget, pigeon, child):
        self._edit_child(pigeon, child, True)
        self._redraw()

    def _remove_pigeon(self, widget, pigeon, child):
        pindex = pigeon.get_pindex()
        self.database.delete_from_table(self.database.PIGEONS, pindex)
        self.parser.remove_pigeon(pindex)
        self._edit_child(pigeon, child, True)
        self._redraw()

    def _redraw(self):
        self.draw_pedigree(self.tables, self.pigeon, True)
        self.treeview.get_selection().emit('changed')

