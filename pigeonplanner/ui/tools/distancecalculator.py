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


import math

import gtk
import gobject

import errors
import builder
from ui.widgets import comboboxes
from ui.widgets import latlongentry
from ui.messagedialog import ErrorDialog
from translation import gettext as _


class DistanceCalculator(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, "DistanceCalculator.ui")

        self.database = database

        self._distance = 0.0
        self._unit = 0
        self._fill_location_combos()
        self.window.set_transient_for(parent)
        self.window.show()

    def close_window(self, widget, event=None):
        self._unit = self.combounit.get_active()
        self._distance = self.entryresult.get_text() or 0.0
        self.window.destroy()
        return False

    def on_buttoncalculate_clicked(self, widget):
        try:
            latitudefrom = self.entrylatfrom.get_text(as_float=True)
            longitudefrom = self.entrylongfrom.get_text(as_float=True)
            latitudeto = self.entrylatto.get_text(as_float=True)
            longitudeto = self.entrylongto.get_text(as_float=True)
        except errors.InvalidInputError:
            ErrorDialog((_("The latitude and longitude need to be in "
                           "DD.dddddd° format to use this function."),
                         None, _("Error")), self.window)
            return

        # Code taken from:
        # http://www.johndcook.com/python_longitude_latitude.html
        degrees_to_radians = math.pi/180.0
        phi1 = (90.0 - latitudefrom)*degrees_to_radians
        phi2 = (90.0 - latitudeto)*degrees_to_radians
        theta1 = longitudefrom*degrees_to_radians
        theta2 = longitudeto*degrees_to_radians

        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
               math.cos(phi1)*math.cos(phi2))
        arc = math.acos(cos)
        # Multiply the arc by the radius of the earth in meters, just 
        # because our distance units combobox holds meters as 1
        dist_meters = arc*6373000
        distance = dist_meters/self.combounit.get_unit()
        self.entryresult.set_text(str(round(distance, 2)))

    def on_combolocationfrom_changed(self, widget):
        if widget.get_active() == 0:
            # Custom selected
            editable = True
            latitude = ''
            longitude = ''
        elif widget.get_active() == 1:
            # Loft selected
            editable = False
            latitude, longitude = self.database.get_loft_latlong()
        else:
            editable = False
            rp = widget.get_active_text()
            latitude, longitude, dist, unit = self.database.get_racepoint_data(rp)
            # Older versions stored these values as None instead of ''
            if latitude is None: latitude = ''
            if longitude is None: longitude = ''
        self.entrylatfrom.set_editable(editable)
        self.entrylongfrom.set_editable(editable)
        self.entrylatfrom.set_text(latitude)
        self.entrylongfrom.set_text(longitude)

    def on_combolocationto_changed(self, widget):
        if widget.get_active() == 0:
            # Custom selected
            editable = True
            latitude = ''
            longitude = ''
        elif widget.get_active() == 1:
            # Loft selected
            editable = False
            latitude, longitude = self.database.get_loft_latlong()
        else:
            editable = False
            rp = widget.get_active_text()
            latitude, longitude, dist, unit = self.database.get_racepoint_data(rp)
            # Older versions stored these values as None instead of ''
            if latitude is None: latitude = ''
            if longitude is None: longitude = ''
        self.entrylatto.set_editable(editable)
        self.entrylongto.set_editable(editable)
        self.entrylatto.set_text(latitude)
        self.entrylongto.set_text(longitude)

    def get_unit(self):
        return self._unit

    def get_distance(self):
        return self._distance

    def _fill_location_combos(self):
        data = self.database.select_from_table(self.database.RACEPOINTS)
        data.sort()
        data.insert(0, _("Custom"))
        data.insert(1, _("Loft"))
        comboboxes.fill_combobox(self.combolocationfrom, data, sort=False)
        comboboxes.fill_combobox(self.combolocationto, data, sort=False)

