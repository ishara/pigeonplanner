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
from gi.repository import GObject

from pigeonplanner.core import errors
from pigeonplanner.ui.widgets import displayentry


class LatLongEntry(displayentry.DisplayEntry):
    __gtype_name__ = "LatLongEntry"
    can_empty = GObject.property(type=bool, default=False, nick="Can empty")

    def __init__(self, can_empty=False):
        displayentry.DisplayEntry.__init__(self)

        self._can_empty = can_empty
        self._tooltip = _(u"Input should be in one of these formats:\n  "
                          u"DD.dddddd°\n  "
                          u"DD°MM.mmm’\n  "
                          u"DD°MM’SS.s”")

    def get_text(self, validate=True, as_float=False):
        value = super().get_text()
        if validate:
            self.__validate(value, as_float)
        if as_float:
            value = value.replace(u",", u".")
            return float(value)
        return value

    def _warn(self):
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "process-stop")
        self.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, self._tooltip)

    def _unwarn(self):
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, None)

    def __validate(self, value, as_float=False):
        if self.can_empty and value == "":
            self._unwarn()
            return
        # Accepted values are:
        #    DD.dddddd°
        #    DD°MM.mmm’
        #    DD°MM’SS.s”
        value = value.replace(u",", u".")
        for char in u" -+":
            value = value.replace(char, u"")
        if self.__check_float_repr(value) is not None:
            self._unwarn()
            return
        if as_float:
            # We need the float repr, above float check failed
            raise errors.InvalidInputError(value)
        if self.__check_dms_repr(value) is not None: 
            self._unwarn()
            return
        self._warn()
        raise errors.InvalidInputError(value)

    # noinspection PyMethodMayBeStatic
    def __check_float_repr(self, value):
        value = value.replace(u"°", u"")
        try:
            return float(value)      
        except ValueError:
            return None

    # noinspection PyMethodMayBeStatic
    def __check_dms_repr(self, value):
        # Replace the degree and quotes by colons...
        for char in u"°'\"":
            value = value.replace(char, u":")
        value = value.rstrip(u":")
        # ... so we can easily split the value up
        splitted = value.split(u":")

        # First value always should be all digits
        if not splitted[0].isdigit():
            return
        # Depending on format...
        if len(splitted) == 2:
            # ... minutes should be a valid float
            try:
                float(splitted[1])
            except ValueError:
                return
        elif len(splitted) == 3:
            # ... minutes should be all digits ...
            if not splitted[1].isdigit():
                return
            # ... and seconds a valid float
            try:
                float(splitted[2])
            except ValueError:
                return
        else:
            # Too many or little splitted values
            return
        return value
