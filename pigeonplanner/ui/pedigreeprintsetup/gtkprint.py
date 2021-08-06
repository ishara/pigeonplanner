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

import abc
import cairo

from gi.repository import Gtk
from gi.repository import GLib

from pigeonplanner.ui.pedigreeprintsetup import preview
from pigeonplanner.reportlib import GtkPrint
from pigeonplanner.reportlib.GtkPrint import paperstyle_to_pagesetup, PRINTER_DPI


class GtkPrintCustom(GtkPrint.GtkPrint, abc.ABC):
    def run(self, print_action):
        self.preview = None  # noqa

        page_setup = paperstyle_to_pagesetup(self.paper)

        operation = Gtk.PrintOperation()
        operation.set_allow_async(True)
        operation.set_default_page_setup(page_setup)
        operation.connect("begin_print", self.on_begin_print)
        operation.connect("draw_page", self.on_draw_page)
        operation.connect("paginate", self.on_paginate)
        operation.connect("preview", self.on_preview)

        GLib.idle_add(self.run_idle, operation, print_action, priority=GLib.PRIORITY_HIGH_IDLE)

    def run_idle(self, operation, print_action):
        operation.run(print_action, self._parent)
        return False

    def on_preview(self, operation, preview_, context, parent):
        preview_widget = preview.PrintPreviewWidget.get_instance()
        preview_widget.set_print_objects(operation, preview_, context)
        self.preview = preview_widget  # noqa

        try:
            width = int(round(context.get_width()))
        except ValueError:
            width = 0
        try:
            height = int(round(context.get_height()))
        except ValueError:
            height = 0
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        context.set_cairo_context(cr, PRINTER_DPI, PRINTER_DPI)

        return True
