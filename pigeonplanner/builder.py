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

"""
Interface for Gtkbuilder
"""


import os

import gtk

import const


class GtkBuilder(object):
    def __init__(self, uifile):
        """
        Initialize Gtkbuilder, connect all signals and get all widgets

        @param uifile: Filename of the Glade file
        """

        self._builder = gtk.Builder()
        self._builder.set_translation_domain(const.DOMAIN)
        self._builder.add_from_file(os.path.join(const.GLADEDIR, uifile))
        self._builder.connect_signals(self)
        for obj in self._builder.get_objects():
            if issubclass(type(obj), gtk.Buildable):
                setattr(self, gtk.Buildable.get_name(obj), obj)

    def get_objects_from_prefix(self, prefix):
        """
        Retrieve all widgets starting with the given prefix

        @param prefix: The prefix to search for
        """

        objects = []
        for obj in self._builder.get_objects():
            if issubclass(type(obj), gtk.Buildable):
                name = gtk.Buildable.get_name(obj)
                if name.startswith(prefix):
                    objects.append(getattr(self, name))

        return objects

    def get_object_name(self, obj):
        """
        Get the widget name of the object

        @param obj: The object to get the name from 
        """

        return gtk.Buildable.get_name(obj)

