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

import gtk
import gtk.gdk

from pigeonplanner import const


class BaseTab(object):
    def __init__(self, name, img):

        self._root = None

        self._label = gtk.VBox()
        img = os.path.join(const.IMAGEDIR, img)
        if const.SMALL_SCREEN:
            self._label.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(img, 18, 18)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(img)
        image = gtk.image_new_from_pixbuf(pixbuf)
        label = gtk.Label(name)
        self._label.pack_start(image)
        self._label.pack_start(label)
        self._label.show_all()

    def get_tab_widgets(self):
        return self._root, self._label

