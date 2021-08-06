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


import operator

from gi.repository import Gtk

from pigeonplanner.core import enums
from pigeonplanner.core import config
from pigeonplanner.core import pigeon as corepigeon


def get_sex_icon_name(sex):
    if sex == enums.Sex.cock:
        return "symbol_male"
    elif sex == enums.Sex.hen:
        return "symbol_female"
    else:
        return "symbol_young"


def get_status_icon_name(status):
    status_icon_mapping = {
        enums.Status.dead: "status_dead",
        enums.Status.active: "status_active",
        enums.Status.sold: "status_sold",
        enums.Status.lost: "status_lost",
        enums.Status.breeder: "status_breeder",
        enums.Status.loaned: "status_onloan",
        enums.Status.widow: "status_widow"
    }
    return status_icon_mapping[status]


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
    for callback, data, label in entries:
        item = Gtk.MenuItem.new()
        if data:
            item.connect("activate", callback, *data)
        else:
            item.connect("activate", callback)
        if label is not None:
            item.set_label(label)
        item.show()
        menu.append(item)
    menu.popup_at_pointer(event)


def draw_pedigree(grid, root_pigeon=None, draw_cb=None):
    # Moved down here to avoid import errors
    from pigeonplanner.ui.widgets import pedigreeboxes

    pedigree_tree = [None] * 15
    if root_pigeon is not None:
        corepigeon.build_pedigree_tree(root_pigeon, 0, 1, pedigree_tree)

    for grid_child in grid.get_children():
        if isinstance(grid_child, (pedigreeboxes.PedigreeBox, pedigreeboxes.PedigreeExtraBox)):
            pigeon = pedigree_tree[grid_child.index]
            if pigeon is root_pigeon:
                pigeon_child = None
            else:
                pigeon_child = root_pigeon if grid_child.index == 0 else pedigree_tree[(grid_child.index - 1) // 2]
            grid_child.set_pigeon(pigeon, pigeon_child)

    if callable(draw_cb):
        draw_cb()

    grid.queue_draw()


class HiddenPigeonsMixin:
    # noinspection PyMethodMayBeStatic
    def _visible_func(self, model, rowiter, _data=None):
        pigeon = model.get_value(rowiter, 0)
        if not pigeon.visible:
            return not config.get("interface.missing-pigeon-hide")
        return True

    # noinspection PyMethodMayBeStatic
    def _cell_func(self, _column, cell, model, rowiter, _data=None):
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
        # noinspection PyProtectedMember
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
