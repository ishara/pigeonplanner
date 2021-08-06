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

"""
A detailed pedigree of the selected pigeon.
"""

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui.widgets import pedigreeboxes
from pigeonplanner.ui.pedigreeprintsetup import setupwindow
from pigeonplanner.database.models import Pigeon


(PREVIOUS,
 NEXT_SIRE,
 NEXT_DAM) = range(3)


class PedigreeWindow(builder.GtkBuilder):
    def __init__(self, parent, pigeon):
        builder.GtkBuilder.__init__(self, "PedigreeWindow.ui")

        self.widgets.treeview = component.get("Treeview")
        self.pigeon = None
        self._current_pigeon = None
        self._current_pigeon_path = None
        self._previous_pigeons = []
        self._original_pigeon = pigeon
        self._build_ui()
        self.set_pigeon(pigeon)

        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show_all()

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon
        self._current_pigeon = pigeon
        self._current_pigeon_path = self.widgets.treeview.get_path_for_pigeon(pigeon)
        self._previous_pigeons = []
        name = pigeon.name
        if name:
            name = ", " + name
        title = "%s: %s%s - %s" % (_("Pedigree"), pigeon.band,
                                   name, pigeon.sex_string)
        self.widgets.window.set_title(title)

        is_home = self._original_pigeon == pigeon
        self.widgets.home_pedigree_button.set_sensitive(not is_home)
        has_previous = self._current_pigeon_path != 0
        self.widgets.previous_pedigree_button.set_sensitive(has_previous)
        has_next = self._current_pigeon_path < len(self.widgets.treeview.get_model()) - 1
        self.widgets.next_pedigree_button.set_sensitive(has_next)

        utils.draw_pedigree(self.widgets.grid, pigeon, self.on_pedigree_draw)

    def _build_ui(self):
        for child in self.widgets.grid.get_children():
            if isinstance(child, pedigreeboxes.PedigreeBox):
                child.connect("redraw-pedigree", self.on_redraw_pedigree)

    def _nav_change(self, nav):
        if nav == PREVIOUS:
            pigeon = self._previous_pigeons.pop()
        else:
            self._previous_pigeons.append(self._current_pigeon)
            pigeon = self._current_pigeon.sire if nav == NEXT_SIRE else self._current_pigeon.dam

        self._current_pigeon = pigeon
        utils.draw_pedigree(self.widgets.grid, pigeon, self.on_pedigree_draw)

    def on_close_dialog(self, _widget, _event=None):
        self.widgets.window.destroy()
        return False

    def on_navbutton_prev_clicked(self, _widget):
        self._nav_change(PREVIOUS)

    def on_navbutton_sire_clicked(self, _widget):
        self._nav_change(NEXT_SIRE)

    def on_navbutton_dam_clicked(self, _widget):
        self._nav_change(NEXT_DAM)

    def on_redraw_pedigree(self, _widget):
        self.pigeon = Pigeon.get_by_id(self.pigeon.id)
        utils.draw_pedigree(self.widgets.grid, self.pigeon, self.on_pedigree_draw)
        self.widgets.treeview.get_selection().emit("changed")

    def on_pedigree_draw(self):
        can_prev = self._current_pigeon != self.pigeon
        self.widgets.buttonprev.set_sensitive(can_prev)

        can_next_sire = self._current_pigeon.sire is not None
        self.widgets.buttonnextsire.set_sensitive(can_next_sire)
        can_next_dam = self._current_pigeon.dam is not None
        self.widgets.buttonnextdam.set_sensitive(can_next_dam)

    def on_home_clicked(self, _widget):
        self.set_pigeon(self._original_pigeon)

    def on_previous_clicked(self, _widget):
        new_pigeon = self.widgets.treeview.get_pigeon_at_path(self._current_pigeon_path - 1)
        self.set_pigeon(new_pigeon)

    def on_next_clicked(self, _widget):
        new_pigeon = self.widgets.treeview.get_pigeon_at_path(self._current_pigeon_path + 1)
        self.set_pigeon(new_pigeon)

    def on_preview_clicked(self, _widget):
        setupwindow.PedigreePrintSetupWindow(self.widgets.window, self.pigeon)
