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


import operator

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from pigeonplanner.ui import utils
from pigeonplanner.ui.widgets import treeview
from pigeonplanner.core import enums
from pigeonplanner.core import config
from pigeonplanner.core import errors


def set_entry_completion(widget):
    """Set entrycompletion on given widget

    :param widget: the widget to set entrycompletion
    """
    completion = Gtk.EntryCompletion()
    completion.set_model(widget.get_model())
    completion.set_minimum_key_length(1)
    completion.set_text_column(0)
    widget.get_child().set_completion(completion)


def fill_combobox(combobox, items, active=0, sort=True):
    """Fill a combobox with the given data

    :param combobox: the combobox
    :param items: list of items to add
    :param active: index of the active value
    :param sort: sort the data or not
    """
    if isinstance(combobox, Gtk.ComboBoxText):
        combobox.remove_all()
        for item in items:
            combobox.append_text(item)
    else:
        model = combobox.get_model()
        model.clear()
        if sort:
            items.sort()
        for item in items:
            model.append([item])

    if active is not None:
        combobox.set_active(active)


class SexCombobox(Gtk.ComboBox):

    __gtype_name__ = "SexCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(int, str, str)
        self.set_model(store)

        for key, value in enums.Sex.mapping.items():
            store.insert(key, [key, value, utils.get_sex_icon_name(key)])

        pb = Gtk.CellRendererPixbuf()
        self.pack_start(pb, expand=False)
        self.add_attribute(pb, "icon-name", 2)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 1)

    def get_sex(self):
        return self.get_active()


class StatusCombobox(Gtk.ComboBox):

    __gtype_name__ = "StatusCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(int, str, str)
        self.set_model(store)

        for key, value in enums.Status.mapping.items():
            store.insert(key, [key, value, utils.get_status_icon_name(key)])

        pb = Gtk.CellRendererPixbuf()
        self.pack_start(pb, expand=False)
        self.add_attribute(pb, "icon-name", 2)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 1)

    def get_status(self):
        return self.get_active()


class OperatorCombobox(Gtk.ComboBox):

    __gtype_name__ = "OperatorCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(str, object)
        self.set_model(store)

        items = [
            ("<", operator.lt),
            ("<=", operator.le),
            ("=", operator.eq),
            ("!=", operator.ne),
            (">=", operator.ge),
            (">", operator.gt),
        ]
        for item in items:
            store.append(item)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_id_column(0)

    def get_operator(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]


class DataComboboxEntry(Gtk.ComboBox):

    __gtype_name__ = "DataComboboxEntry"

    def __init__(self):
        Gtk.ComboBox.__init__(self, has_entry=True)
        self.store = Gtk.ListStore(str)
        self.set_model(self.store)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_id_column(0)
        self.set_entry_text_column(0)

    def set_data(self, table, active=0):
        self._table = table
        fill_combobox(self, self._table.get_data_list(), active, False)
        set_entry_completion(self)

    def add_item(self, item):
        try:
            data = {self._table.get_item_column().name: item}
            self._table.insert(**data).execute()
        except errors.IntegrityError:
            # This item already exists or is empty
            return

        self.store.append([item])
        self.store.set_sort_column_id(0, Gtk.SortType.ASCENDING)


class DistanceCombobox(Gtk.ComboBox):

    __gtype_name__ = "DistanceCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(str, float)
        self.set_model(store)

        units = (
            (_("Yards"), 0.9144),
            (_("Kilometres"), 1000.0),
            (_("Metres"), 1.0),
            (_("Centimetres"), 0.01),
            (_("Inches"), 0.025),
            (_("Feet"), 0.3048),
            (_("Miles"), 1609.344),
            (_("Nautical Miles"), 1852.0),
        )
        for unit in units:
            store.append(unit)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_id_column(0)
        self.connect("realize", lambda w: self.set_active(config.get("options.distance-unit")))

    def get_unit(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]


class SpeedCombobox(Gtk.ComboBox):

    __gtype_name__ = "SpeedCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(str, float)
        self.set_model(store)

        units = (
            (_("Yard per Minute"), 0.01524),
            (_("Metres per Minute"), 0.0166666666),
            (_("Metres per Second"), 1.0),
            (_("Kilometre per Hour"), 0.27777777777777777777777777777777),
            (_("Feet per Second"), 0.3048),
            (_("Feet per Minute"), 0.00508),
            (_("Mile per Hour"), 0.44704),
        )
        for unit in units:
            store.append(unit)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.connect("realize", lambda w: self.set_active(config.get("options.speed-unit")))

    def get_unit(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]


class PigeonSearchCombobox(Gtk.ComboBox):

    __gtype_name__ = "PigeonSearchCombobox"

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        store = Gtk.ListStore(str, int)
        self.set_model(store)
        columns = [
            (_("Band no."), treeview.MainTreeView.LS_RING),
            (_("Name"), treeview.MainTreeView.LS_NAME),
            (_("Colour"), treeview.MainTreeView.LS_COLOUR),
            (_("Loft"), treeview.MainTreeView.LS_LOFT),
            (_("Strain"), treeview.MainTreeView.LS_STRAIN),
        ]
        for column in columns:
            store.append(column)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_id_column(0)

    def get_column(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]
