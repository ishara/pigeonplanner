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

from pigeonplanner.ui import component
from pigeonplanner.core import const


class _TotalLabel(Gtk.Label):
    __gtype_name__ = "_TotalLabel"
    TEMPLATE = _("Pigeons: %s")

    def __init__(self):
        Gtk.Label.__init__(self)
        self._value = None

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self.set_text(self.TEMPLATE % value)


class _FilterLabel(Gtk.Label):
    __gtype_name__ = "_FilterLabel"
    TEMPLATE = _("Filter: %s")
    ON = "<b>%s</b>" % _("On")
    OFF = _("Off")

    def __init__(self):
        Gtk.Label.__init__(self)
        self._value = None

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self.set_markup(self.TEMPLATE % (self.ON if value else self.OFF))


class StatusBar(Gtk.Statusbar, component.Component):
    __gtype_name__ = "StatusBar"

    def __init__(self):
        Gtk.Statusbar.__init__(self)
        component.Component.__init__(self, "Statusbar")

        self.set_margin_top(0)
        self.set_margin_bottom(0)

        self._build_labels()
        self.show_all()

    def _build_labels(self):
        total = self._total = _TotalLabel()
        self._filter = _FilterLabel()
        filterbox = Gtk.EventBox()
        filterbox.connect("button-press-event", self.on_filterbox_clicked)
        filterbox.add(self._filter)
        box = self.get_message_area()
        box.pack_end(total, False, False, 0)
        box.pack_end(filterbox, False, False, 4)
        # If the second number in the version is uneven, it's a development version.
        if const.VERSION_TUPLE[1] % 2 == 1:
            dev_label = Gtk.Label()
            dev_label.set_markup("""<span foreground="red" font_weight="bold">Development version</span>""")
            box.pack_end(dev_label, False, False, 4)

    def on_filterbox_clicked(self, widget, event):
        # TODO
        pass

    def display_message(self, message, timeout=3):
        def timer_cb():
            self.pop(0)
            return False

        self.push(0, message)
        GLib.timeout_add_seconds(timeout, timer_cb)

    def get_total(self):
        return self._total.get_value()

    def set_total(self, value):
        self._total.set_value(value)

    def get_filter(self):
        return self._filter.get_value()

    def set_filter(self, value):
        self._filter.set_value(value)
