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


import geopy

import gtk

from pigeonplanner import builder
from pigeonplanner.ui.widgets import latlongentry


class LocationChooser(builder.GtkBuilder):
    def __init__(self, parent, location=None):
        builder.GtkBuilder.__init__(self, "LocationChooser.ui")
        self.widgets.dialog.set_transient_for(parent)

        if location is not None:
            self.widgets.entryloc.set_text(location)

    def run(self):
        response = self.widgets.dialog.run()
        return response

    def destroy(self):
        self.widgets.dialog.destroy()

    def on_entryloc_icon_press(self, widget, icon_pos, event):
        location = widget.get_text()

        g = geopy.geocoders.GoogleV3()
        try:
            place, (lat, lng) = g.geocode(location)
        except (ValueError, geopy.geocoders.googlev3.GQueryError):
            widget.set_icon_from_stock(0, gtk.STOCK_DIALOG_ERROR)
            widget.set_icon_tooltip_text(0, _("Can't find location '%s'") % location)
            return

        widget.set_icon_from_stock(0, None)
        widget.set_icon_tooltip_text(0, None)
        self.widgets.entrylat.set_text(str(lat))
        self.widgets.entrylng.set_text(str(lng))

    def get_latlng(self):
        lat = self.widgets.entrylat.get_text()
        lng = self.widgets.entrylng.get_text()
        return lat, lng
