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


import os
import operator

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import config


def get_sex_image(sex):
    return GdkPixbuf.Pixbuf.new_from_file(common.SEX_IMGS[sex])


def get_status_image(status):
    return GdkPixbuf.Pixbuf.new_from_file(common.STATUS_IMGS[status])


def create_stock_button(icons):
    """Register stock buttons from custom images.

    :param icons: A list of tuples containing filename, name and description
    """
    factory = Gtk.IconFactory()
    factory.add_default()
    for img, name, description in icons:
        pb = GdkPixbuf.Pixbuf.new_from_file(os.path.join(const.IMAGEDIR, img))
        iconset = Gtk.IconSet(pb)
        factory.add(name, iconset)
        item = Gtk.StockItem()
        item.stock_id = name
        item.label = description
        item.translation_domain = "pigeonplanner"
        Gtk.stock_add([item])  # TODO GTK3: deprecated. Also might be stock_add_static instead.


def set_multiple_sensitive(widgets, value=None):
    """Set multiple widgets sensitive at once

    :param widgets: dic or list of widgets
    :param value: bool to indicate the state
    """
    if isinstance(widgets, dict):
        for widget, sensitive in widgets.items():
            widget.set_sensitive(sensitive)
    else:
        for widget in widgets:
            widget.set_sensitive(value)


def set_multiple_visible(widgets, value=None):
    """Set multiple widgets visible at once

    :param widgets: dic or list of widgets
    :param value: bool to indicate the state
    """
    if isinstance(widgets, dict):
        for widget, visible in widgets.items():
            widget.set_visible(visible)
    else:
        for widget in widgets:
            widget.set_visible(value)


def popup_menu(event, entries):
    """Make a right click menu

    :param event: The GTK event
    :param entries: List of wanted menuentries
    """
    menu = Gtk.Menu()
    for stock_id, callback, data, label in entries:
        item = Gtk.ImageMenuItem.new_from_stock(stock_id, None)
        if data:
            item.connect("activate", callback, *data)
        else:
            item.connect("activate", callback)
        if label is not None:
            item.set_label(label)
        item.show()
        menu.append(item)
    menu.popup_at_pointer(event)


class HiddenPigeonsMixin:
    def _visible_func(self, model, rowiter, data=None):
        pigeon = model.get_value(rowiter, 0)
        if not pigeon.visible:
            return not config.get("interface.missing-pigeon-hide")
        return True

    def _cell_func(self, column, cell, model, rowiter, data=None):
        pigeon = model.get_value(rowiter, 0)
        color = "white"
        if config.get("interface.missing-pigeon-color"):
            if not pigeon.visible:
                color = config.get("interface.missing-pigeon-color-value")
        cell.set_property("cell-background", color)


class TreeviewFilter:
    class FilterItem:
        def __init__(self, name, value, operator_, type_):
            self.name = name
            self.value = value
            self.operator = operator_
            self.type = type_

    def __init__(self, name=""):
        self.name = name
        self._items = []

    def __iter__(self):
        return iter(self._items)

    def __add__(self, other):
        self._items.extend(other._items)
        return self._items

    def clear(self):
        self._items = []

    def has_filters(self):
        return len(self._items) > 0

    def add(self, name, value, operator_=operator.eq, type_=str, allow_empty_value=False):
        if not value and not allow_empty_value:
            return
        item = self.FilterItem(name, value, operator_, type_)
        self._items.append(item)
