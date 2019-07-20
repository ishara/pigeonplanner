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


from gi.repository import Gtk
from gi.repository import GLib

from pigeonplanner.ui import builder
from pigeonplanner.ui import locationchooser
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.database.models import Racepoint
from .datamanager import DataManager
from .distancecalculator import DistanceCalculator


class RacepointManager(builder.GtkBuilder):
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "RaceManager.ui")

        self._fill_racepoints_combo()
        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show()

    def close_window(self, widget, event=None):
        self.widgets.window.destroy()

    def on_combopoint_changed(self, widget):
        rp = widget.get_active_text()
        if rp is None:
            return
        racepoint = Racepoint.get(Racepoint.racepoint == rp)
        self.widgets.entrylatitude.set_text(racepoint.xco)
        self.widgets.entrylongitude.set_text(racepoint.yco)
        try:
            distance = float(racepoint.distance)
        except ValueError:
            distance = 0.0
        self.widgets.spindistance.set_value(distance)
        unit = racepoint.unit
        if not unit:
            unit = 0
        self.widgets.combodistance.set_active(unit)

    def on_buttonhelp_clicked(self, widget):
        common.open_help(13)

    def on_buttonadd_clicked(self, widget):
        manager = DataManager(self.widgets.window)
        response = manager.widgets.window.run()
        if response == Gtk.ResponseType.CLOSE:
            self._fill_racepoints_combo()
        manager.widgets.window.destroy()

    def on_buttonsearch_clicked(self, widget):
        racepoint = self.widgets.combopoint.get_active_text()
        dialog = locationchooser.LocationChooser(self.widgets.window, racepoint)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            lat, lng = dialog.get_latlng()
            self.widgets.entrylatitude.set_text(lat)
            self.widgets.entrylongitude.set_text(lng)
        dialog.destroy()

    def on_buttoncalculate_clicked(self, widget):
        point = self.widgets.combopoint.get_active()
        calculator = DistanceCalculator(self.widgets.window, point)
        response = calculator.widgets.window.run()
        if response == Gtk.ResponseType.CLOSE:
            self.widgets.spindistance.set_value(float(calculator.get_distance()))
            self.widgets.combodistance.set_active(calculator.get_unit())
        calculator.widgets.window.destroy()

    def on_buttonsave_clicked(self, widget):
        try:
            latitude = self.widgets.entrylatitude.get_text()
            longitude = self.widgets.entrylongitude.get_text()
        except errors.InvalidInputError:
            return

        rp = self.widgets.combopoint.get_active_text()
        racepoint = Racepoint.get(Racepoint.racepoint == rp)
        racepoint.xco = latitude
        racepoint.yco = longitude
        racepoint.distance = self.widgets.spindistance.get_value()
        racepoint.unit = self.widgets.combodistance.get_active()
        racepoint.save()

        def clear_image():
            self.widgets.image.clear()
            return False
        self.widgets.image.set_from_stock(Gtk.STOCK_OK, Gtk.IconSize.BUTTON)
        GLib.timeout_add(3000, clear_image)

    def _fill_racepoints_combo(self):
        comboboxes.fill_combobox(self.widgets.combopoint, Racepoint.get_data_list())
        value = self.widgets.combopoint.get_active_text() is not None
        self.widgets.entrylatitude.set_sensitive(value)
        self.widgets.entrylongitude.set_sensitive(value)
        self.widgets.hboxdistance.set_sensitive(value)
        self.widgets.buttonsave.set_sensitive(value)
