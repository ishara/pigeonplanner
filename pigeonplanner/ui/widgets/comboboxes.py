# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Parts taken and inspired by Gramps

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
from translation import gettext as _


def set_entry_completion(widget):
    """
    Set entrycompletion on given widget

    @param widget: the widget to set entrycompletion
    """

    completion = gtk.EntryCompletion()
    completion.set_model(widget.get_model())
    completion.set_minimum_key_length(1)
    completion.set_text_column(0)
    widget.child.set_completion(completion)

def set_combobox_wrap(combobox):
    """
    Wrap the columns of a combobox depending on the number of items

    @param combobox: the combobox
    """

    length = len(combobox.get_model())
    if length > 10 and length <= 30:
        combobox.set_wrap_width(2)
    elif length > 30:
        combobox.set_wrap_width(3)

def fill_combobox(combobox, items, active=0, sort=True):
    """
    Fill a combobox with the given data

    @param widget: the combobox
    @param items: list of items to add
    @param active: index of the active value
    @param sort: sort the data or not
    """

    model = combobox.get_model()
    model.clear()
    if sort:
        items.sort()
    for item in items:
        model.append([item])

    set_combobox_wrap(combobox)
    combobox.set_active(active)


class SexCombobox(gtk.ComboBox):

    __gtype_name__ = 'SexCombobox'

    def __init__(self):
        store = gtk.ListStore(str, str)
        gtk.ComboBox.__init__(self, store)

        for key, value in common.get_sexdic().items():
            store.insert(int(key), [key, value])
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        self.set_active(0)
        self.show()


class StatusCombobox(gtk.ComboBox):

    __gtype_name__ = 'StatusCombobox'

    def __init__(self):
        store = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, store)

        for item in [_("Dead"), _("Active"), _("Sold"), _("Lost")]:
            store.append([item])
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(0)


class DistanceCombobox(gtk.ComboBox):

    __gtype_name__ = 'DistanceCombobox'

    def __init__(self):
        store = gtk.ListStore(str, float)
        gtk.ComboBox.__init__(self, store)

        units = ((_('Yards'), 0.9144),
                 (_('Kilometres'), 1000.),
                 (_('Metres'), 1.),
                 (_('Centimetres'), 0.01),
                 (_('Inches'), 0.025),
                 (_('Feet'), 0.3048),
                 (_('Miles'), 1609.344),
                 (_('Nautical Miles'), 1852.)
            )
        for unit in units:
            store.append(unit)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(0)
        self.show()

    def get_unit(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]


class SpeedCombobox(gtk.ComboBox):

    __gtype_name__ = 'SpeedCombobox'

    def __init__(self):
        store = gtk.ListStore(str, float)
        gtk.ComboBox.__init__(self, store)

        units = ((_('Yard per Minute'), 0.01524),
                 (_('Metres per Minute'), 0.0166666666),
                 (_('Metres per Second'), 1.),
                 (_('Kilometre per Hour'), 0.27777777777777777777777777777777),
                 (_('Feet per Second'), 0.3048),
                 (_('Feet per Minute'), 0.00508),
                 (_('Mile per Hour'), 0.44704)
            )
        for unit in units:
            store.append(unit)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(0)
        self.show()

    def get_unit(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]

