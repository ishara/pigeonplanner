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


import gtk
import gobject

import const
import builder
from ui.widgets import comboboxes


class RacepointManager(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, const.GLADERACEMGR)

        self.database = database

        self._fill_racepoints_combo()
        self.window.set_transient_for(parent)
        self.window.show()

    def close_window(self, widget, event=None):
        self.window.destroy()

    def on_combopoint_changed(self, widget):
        rp = widget.get_active_text()
        latitude, longitude, distance = self.database.get_racepoint_data(rp)
        self.entrylatitude.set_text(latitude)
        self.entrylongitude.set_text(longitude)
        self.entrydistance.set_text(distance)

    def on_buttonsave_clicked(self, widget):
        data = (self.entrylatitude.get_text(),
                self.entrylongitude.get_text(),
                self.entrydistance.get_text(),
                self.combopoint.get_active_text())
        self.database.update_table(self.database.RACEPOINTS, data, 2)
        def clear_image():
            self.image.clear()
            return False
        self.image.set_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
        gobject.timeout_add(4000, clear_image)

    def _fill_racepoints_combo(self):
        data = self.database.select_from_table(self.database.RACEPOINTS)
        comboboxes.fill_combobox(self.combopoint, data)
        value = self.combopoint.get_active_text() is not None
        self.entrylatitude.set_sensitive(value)
        self.entrylongitude.set_sensitive(value)
        self.entrydistance.set_sensitive(value)
        self.buttonsave.set_sensitive(value)

