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
from translation import gettext as _


class LatLongEntry(gtk.Entry):
    __gtype_name__ = 'LatLongEntry'
    can_empty = gobject.property(type=bool, default=False, nick="Can empty")
    def __init__(self, can_empty=False):
        gtk.Entry.__init__(self)

        self.can_empty = can_empty
        self._tooltip = _("Input should be in one of these formats:\n  "
                          "DD.dddddd°\n  "
                          "DD°MM.mmm’\n  "
                          "DD°MM’SS.s”")

    def get_text(self, validate=True):
        value = gtk.Entry.get_text(self)
        if validate:
            self.__validate(value)
        return value

    def warn(self):
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_STOP)
        self.set_icon_tooltip_text(gtk.ENTRY_ICON_SECONDARY, self._tooltip)

    def unwarn(self):
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)

    def __validate(self, value):
        if self.can_empty and value == '':
            return
        # Accepted values are:
        #    DD.dddddd°
        #    DD°MM.mmm’
        #    DD°MM’SS.s”
        value = value.replace(u',', u'.')
        for char in u' -+':
            value = value.replace(char, u'')
        if self.__check_float_repr(value) is not None:
            return
        if self.__check_dms_repr(value) is not None: 
            return
        raise errors.InvalidInputError(value)

    def __check_float_repr(self, value):
        value = value.replace(u'°', u'')
        try : 
            return float(value)      
        except ValueError:
            return None

    def __check_dms_repr(self, value):
        # Replace the degree and quotes by colons...
        for char in u"°'\"":
            value = value.replace(char, u':')
        value = value.rstrip(u':')
        # ... so we can easily split the value up
        splitted = value.split(u':')

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

