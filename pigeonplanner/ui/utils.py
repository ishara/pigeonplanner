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


def set_multiple_sensitive(widgets, value=None):
    """ 
    Set multiple widgets sensitive at once

    @param widgets: dic or list of widgets
    @param value: bool to indicate the state
    """

    if isinstance(widgets, dict):
        for widget, sensitive in widgets.items():
            widget.set_sensitive(sensitive)
    else:
        for widget in widgets:
            widget.set_sensitive(value)

def set_multiple_visible(widgets, value=None):
    """ 
    Set multiple widgets visible at once

    @param widgets: dic or list of widgets
    @param value: bool to indicate the state
    """

    if isinstance(widgets, dict):
        for widget, visible in widgets.items():
            widget.set_visible(visible)
    else:
        for widget in widgets:
            widget.set_visible(value)

def popup_menu(event, entries):
    """
    Make a right click menu

    @param entries: List of wanted menuentries
    """

    menu = gtk.Menu()
    for stock_id, callback, data in entries:
        item = gtk.ImageMenuItem(stock_id)
        if data:
            item.connect("activate", callback, *data)
        else:
            item.connect("activate", callback)
        item.show()
        menu.append(item)
    menu.popup(None, None, None, event.button, event.time)
