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


import os.path

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from pigeonplanner.ui import component
from pigeonplanner.core import const


class BaseTab(component.Component):
    def __init__(self, name, title, img):
        component.Component.__init__(self, name)

        self._parent = component.get("MainWindow")

        self.widgets._label = Gtk.VBox()
        img = os.path.join(const.IMAGEDIR, img)
        if Gdk.Screen.height() <= 768:
            self.widgets._label.set_orientation(Gtk.Orientation.HORIZONTAL)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(img, 18, 18)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(img)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        label = Gtk.Label(title)
        self.widgets._label.pack_start(image, False, False, 0)
        self.widgets._label.pack_start(label, False, False, 0)
        self.widgets._label.show_all()

    def get_tab_widgets(self):
        return self.widgets._root, self.widgets._label

    def set_pigeon(self, pigeon):
        pass

    def clear_pigeon(self):
        pass

    def get_pigeon_state_widgets(self):
        """ List of widgets that need a 'sensitive' property update whenever
        a pigeon is selected/deselected in the main treeview.
        """
        return []
