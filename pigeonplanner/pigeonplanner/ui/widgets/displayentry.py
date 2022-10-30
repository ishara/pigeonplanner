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


class DisplayEntry(Gtk.Entry):
    __gtype_name__ = "DisplayEntry"

    def __init__(self, is_editable=False):
        Gtk.Entry.__init__(self)
        self._is_editable = is_editable
        self.set_is_editable(is_editable)

    def get_is_editable(self):
        return self._is_editable

    def set_is_editable(self, is_editable):
        self._is_editable = is_editable
        self.set_has_frame(is_editable)
        self.set_editable(is_editable)
        if is_editable:
            self.get_style_context().remove_class("displayentry")
        else:
            self.get_style_context().add_class("displayentry")

    is_editable = GObject.property(get_is_editable, set_is_editable, bool, False, "Is editable")
