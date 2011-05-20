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
import datetime

import gtk
import gtk.gdk

import const


class DateEntry(gtk.Viewport):
    def __init__(self, editable=True):
        gtk.Viewport.__init__(self)

        self._entry = gtk.Entry()
        self._entry.set_max_length(10)
        self._entry.set_width_chars(16)
        self._entry.set_alignment(.5)
        self._entry.connect('icon-press', self.on_icon_pressed)

        today = datetime.datetime.today()
        self._entry.set_text(today.strftime(const.DATE_FORMAT))

        self.set_editable(editable)
        self.add(self._entry)
        self.show_all()

    def on_icon_pressed(self, widget, icon, event):
        CalendarPopup(widget)

    def set_editable(self, editable):
        self.set_shadow_type(gtk.SHADOW_NONE if editable else gtk.SHADOW_IN)
        self._entry.set_has_frame(editable)
        self._entry.set_editable(editable)
        icon = os.path.join(const.IMAGEDIR, 'icon_calendar.png')
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon) if editable else None
        self._entry.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pixbuf)

    def set_text(self, text):
        self._entry.set_text(text)

    def get_text(self):
        return self._entry.get_text()

    def grab_focus(self):
        self._entry.grab_focus()
        self._entry.set_position(-1)


class CalendarPopup(gtk.Window):
    def __init__(self, entry):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_modal(True)
        self.set_resizable(False)

        buttonapply = gtk.Button()
        img = gtk.image_new_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        buttonapply.set_image(img)
        buttonapply.connect('clicked', self.on_buttonapply_clicked)
        buttoncancel = gtk.Button()
        img = gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON)
        buttoncancel.set_image(img)
        buttoncancel.connect('clicked', self.on_buttoncancel_clicked)
        vbox = gtk.VBox(False, 8)
        vbox.pack_start(buttonapply, False, False, 0)
        vbox.pack_start(buttoncancel, False, False, 0)

        calendar = gtk.Calendar()
        calendar.connect('day-selected', self.on_day_selected)
        calendar.connect('day-selected-double-click', self.on_day_clicked)
        hbox = gtk.HBox()
        hbox.pack_start(vbox, False, False, 0)
        hbox.pack_start(calendar, False, False, 0)

        self._calendar = calendar
        self._entry = entry
        self._saved_date = entry.get_text()

        vp = gtk.Viewport()
        vp.add(hbox)
        self.add(vp)
        self._set_position()
        self.show_all()

    # Callbacks
    def on_buttonapply_clicked(self, widget):
        self.destroy()

    def on_buttoncancel_clicked(self, widget):
        self._entry.set_text(self._saved_date)
        self.destroy()

    def on_day_selected(self, widget):
        year, month, day = self._calendar.get_date()
        the_date = datetime.date(year, month+1, day)

        if the_date:
            self._entry.set_text(the_date.strftime(const.DATE_FORMAT))
        else:
            self._entry.set_text('')

    def on_day_clicked(self, widget):
        self.destroy()

    # Internal methods
    def _set_position(self):
        window = self._entry.get_parent_window()
        (x, y) = gtk.gdk.Window.get_origin(window)

        x += self._entry.allocation.x
        y += self._entry.allocation.y
        bwidth = self._entry.allocation.width
        bheight = self._entry.allocation.height

        x += bwidth - self._entry.size_request()[0]
        y += bheight

        if x < 0: x = 0
        if y < 0: y = 0
        
        self.move(x, y)

