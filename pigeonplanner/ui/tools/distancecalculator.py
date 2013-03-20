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


from geopy import distance as gdistance

from pigeonplanner import errors
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.ui.messagedialog import ErrorDialog


class DistanceCalculator(builder.GtkBuilder):
    def __init__(self, parent, database, racepoint=None):
        builder.GtkBuilder.__init__(self, "DistanceCalculator.ui")

        self.database = database

        self._distance = 0.0
        self._unit = 0
        self._fill_location_combos(racepoint)
        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show()

    def close_window(self, widget, event=None):
        self._unit = self.widgets.combounit.get_active()
        self._distance = self.widgets.entryresult.get_text() or 0.0
        self.widgets.window.destroy()
        return False

    def on_buttonhelp_clicked(self, widget):
        common.open_help(12)

    def on_buttoncalculate_clicked(self, widget):
        try:
            latfrom = self.widgets.entrylatfrom.get_text(as_float=True)
            lngfrom = self.widgets.entrylongfrom.get_text(as_float=True)
            latto = self.widgets.entrylatto.get_text(as_float=True)
            lngto = self.widgets.entrylongto.get_text(as_float=True)
        except errors.InvalidInputError:
            ErrorDialog((_("The latitude and longitude need to be in "
                           "DD.dddddd° format to use this function."),
                         None, _("Error")), self.widgets.window)
            return

        dist = gdistance.distance((latfrom, lngfrom), (latto, lngto))
        unit = self.widgets.combounit.get_active()
        if unit == 1:
            distance = dist.kilometers
        elif unit == 2:
            distance = dist.meters
        elif unit == 5:
            distance = dist.feet
        elif unit == 6:
            distance = dist.miles
        elif unit == 7:
            distance = dist.nautical
        else:
            distance = dist.meters / self.widgets.combounit.get_unit()
        self.widgets.entryresult.set_text(str(round(distance, 2)))

    def on_combolocationfrom_changed(self, widget):
        if widget.get_active() == 0:
            # Custom selected
            editable = True
            latitude = ''
            longitude = ''
        elif widget.get_active() == 1:
            # Loft selected
            editable = False
            try:
                latitude, longitude = self.database.get_loft_latlong()
            except TypeError:
                latitude, longitude = '', ''
        else:
            editable = False
            rp = widget.get_active_text()
            latitude, longitude, dist, unit = self.database.get_racepoint_data(rp)
            # Older versions stored these values as None instead of ''
            if latitude is None: latitude = ''
            if longitude is None: longitude = ''
        self.widgets.entrylatfrom.set_editable(editable)
        self.widgets.entrylongfrom.set_editable(editable)
        self.widgets.entrylatfrom.set_text(latitude)
        self.widgets.entrylongfrom.set_text(longitude)

    def on_combolocationto_changed(self, widget):
        if widget.get_active() == 0:
            # Custom selected
            editable = True
            latitude = ''
            longitude = ''
        elif widget.get_active() == 1:
            # Loft selected
            editable = False
            try:
                latitude, longitude = self.database.get_loft_latlong()
            except TypeError:
                latitude, longitude = '', ''
        else:
            editable = False
            rp = widget.get_active_text()
            latitude, longitude, dist, unit = self.database.get_racepoint_data(rp)
            # Older versions stored these values as None instead of ''
            if latitude is None: latitude = ''
            if longitude is None: longitude = ''
        self.widgets.entrylatto.set_editable(editable)
        self.widgets.entrylongto.set_editable(editable)
        self.widgets.entrylatto.set_text(latitude)
        self.widgets.entrylongto.set_text(longitude)

    def get_unit(self):
        return self._unit

    def get_distance(self):
        return self._distance

    def _fill_location_combos(self, racepoint):
        data = self.database.select_from_table(self.database.RACEPOINTS)
        data.sort()
        data.insert(0, _("Custom"))
        data.insert(1, _("Loft"))
        activefrom = 1 if racepoint is not None else 0
        activeto = racepoint+2 if racepoint is not None else 0
        comboboxes.fill_combobox(self.widgets.combolocationfrom, data, activefrom, False)
        comboboxes.fill_combobox(self.widgets.combolocationto, data, activeto, False)

