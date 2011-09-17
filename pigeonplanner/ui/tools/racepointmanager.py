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

import errors
import builder
from ui.widgets import comboboxes
from ui.widgets import latlongentry
from datamanager import DataManager
from distancecalculator import DistanceCalculator


class RacepointManager(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, "RaceManager.ui")

        self.database = database

        self._fill_racepoints_combo()
        self.window.set_transient_for(parent)
        self.window.show()

    def close_window(self, widget, event=None):
        self.window.destroy()

    def on_combopoint_changed(self, widget):
        rp = widget.get_active_text()
        if rp is None: return
        latitude, longitude, distance, unit = self.database.get_racepoint_data(rp)
        # Older versions stored these values as None instead of ''
        if latitude is None: latitude = ''
        if longitude is None: longitude = ''
        if distance is None: distance = '0.0'
        self.entrylatitude.set_text(latitude)
        self.entrylongitude.set_text(longitude)
        try:
            distance = float(distance)
        except ValueError:
            distance = 0.0
        self.spindistance.set_value(distance)
        if not unit: unit = 0
        self.combodistance.set_active(unit)

    def on_buttonadd_clicked(self, widget):
        manager = DataManager(self.window, self.database, None)
        response = manager.window.run()
        if response == gtk.RESPONSE_CLOSE:
            self._fill_racepoints_combo()
        manager.window.destroy()

    def on_buttoncalculate_clicked(self, widget):
        calculator = DistanceCalculator(self.window, self.database)
        response = calculator.window.run()
        if response == gtk.RESPONSE_CLOSE:
            self.spindistance.set_value(float(calculator.get_distance()))
            self.combodistance.set_active(calculator.get_unit())
        calculator.window.destroy()

    def on_buttonsave_clicked(self, widget):
        try:
            latitude = self.entrylatitude.get_text()
            longitude = self.entrylongitude.get_text()
        except errors.InvalidInputError:
            return

        data = (latitude, longitude,
                self.spindistance.get_value(),
                self.combodistance.get_active(),
                self.combopoint.get_active_text())
        self.database.update_table(self.database.RACEPOINTS, data, 2)
        def clear_image():
            self.image.clear()
            return False
        self.image.set_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
        gobject.timeout_add(3000, clear_image)

    def _fill_racepoints_combo(self):
        data = self.database.select_from_table(self.database.RACEPOINTS)
        comboboxes.fill_combobox(self.combopoint, data)
        value = self.combopoint.get_active_text() is not None
        self.entrylatitude.set_sensitive(value)
        self.entrylongitude.set_sensitive(value)
        self.hboxdistance.set_sensitive(value)
        self.buttonsave.set_sensitive(value)

