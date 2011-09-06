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

import common
import errors
import messages


class BandEntry(gtk.Viewport):
    def __init__(self, editable=False):
        gtk.Viewport.__init__(self)
        self.set_shadow_type(gtk.SHADOW_NONE if editable else gtk.SHADOW_IN)

        self._entryband = gtk.Entry()
        self._entryband.set_width_chars(15)
        self._entryband.set_alignment(.5)
        self._entryyear = gtk.Entry(4)
        self._entryyear.set_width_chars(4)
        if editable:
            self._entryband.set_activates_default(True)
            self._entryyear.set_activates_default(True)
        self.set_editable(editable)
        label = gtk.Label("/")

        hbox = gtk.HBox()
        hbox.pack_start(self._entryband, False, True, 0)
        hbox.pack_start(label, False, True, 4)
        hbox.pack_start(self._entryyear, False, True, 0)

        self.add(hbox)
        self.show_all()

    def set_editable(self, editable):
        self._entryband.set_has_frame(editable)
        self._entryband.set_editable(editable)
        self._entryyear.set_has_frame(editable)
        self._entryyear.set_editable(editable)

    def set_pindex(self, pindex):
        self.set_band(*common.get_band_from_pindex(pindex))

    def set_band(self, band, year):
        self._entryband.set_text(band)
        self._entryyear.set_text(year)

    def get_pindex(self, validate=True, can_empty=False):
        band, year = self.get_band(validate, can_empty)
        return common.get_pindex_from_band(band, year)

    def get_band(self, validate=True, can_empty=False):
        band, year = self._entryband.get_text(), self._entryyear.get_text()
        if validate:
            self.__validate(band, year, can_empty)
        return band, year

    def grab_focus(self):
        self._entryband.grab_focus()
        self._entryband.set_position(-1)

    def __validate(self, band, year, can_empty=False):
        if can_empty and (band == '' and year == ''):
            return

        if not band or not year:
            raise errors.InvalidInputError(messages.MSG_EMPTY_FIELDS)

        elif not year.isdigit():
            raise errors.InvalidInputError(messages.MSG_INVALID_NUMBER)

        elif not len(year) == 4:
            raise errors.InvalidInputError(messages.MSG_INVALID_LENGTH)

