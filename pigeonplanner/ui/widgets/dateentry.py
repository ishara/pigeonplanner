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

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from pigeonplanner import messages
from pigeonplanner.core import const


class InvalidDateInput(Exception):
    # noinspection PyMethodMayBeStatic
    def format_error(self):
        """Format the error to be displayed in an error dialog.

        :return: a 3-tuple of (primary, secondary, title)
        """
        return messages.MSG_INVALID_FORMAT


class DateEntry(Gtk.Viewport):
    __gtype_name__ = "DateEntry"
    __gsignals__ = {"changed": (GObject.SIGNAL_RUN_LAST, None, ())}
    can_empty = GObject.property(type=bool, default=False, nick="Can empty")

    def __init__(self, editable=False, clear=False, can_empty=False):
        Gtk.Viewport.__init__(self)
        self.set_shadow_type(Gtk.ShadowType.NONE)

        self._entry = Gtk.Entry()
        self._entry.set_max_length(10)
        self._entry.set_width_chars(16)
        self._entry.set_alignment(0.5)
        self._entry.connect("icon-press", self.on_icon_pressed)

        self.can_empty = can_empty
        self.clear = self._clear = clear
        self.editable = self._editable = editable
        self.add(self._entry)
        self.show_all()

    def on_icon_pressed(self, _widget, icon_pos, _event):
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            icon_area = self._entry.get_icon_area(Gtk.EntryIconPosition.SECONDARY)
            popover = CalendarPopover(self)
            popover.set_relative_to(self)
            popover.set_pointing_to(icon_area)
            popover.show_all()
            popover.popup()

    def get_editable(self):
        return self._editable

    def set_editable(self, editable):
        self._editable = editable
        self._entry.set_has_frame(editable)
        self._entry.set_editable(editable)
        if editable:
            self._entry.get_style_context().remove_class("displayentry")
        else:
            self._entry.get_style_context().add_class("displayentry")
        icon = os.path.join(const.IMAGEDIR, "icon_calendar.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon) if editable else None
        self._entry.set_icon_from_pixbuf(Gtk.EntryIconPosition.SECONDARY, pixbuf)

    editable = GObject.property(get_editable, set_editable, bool, False)

    def get_clear(self):
        return self._clear

    def set_clear(self, clear):
        self._clear = clear
        if clear:
            text = ""
        else:
            today = datetime.datetime.today()
            text = today.strftime(const.DATE_FORMAT)
        self._entry.set_text(text)

    clear = GObject.property(get_clear, set_clear, bool, False)

    def set_text(self, text):
        if text is None:
            text = ""
        self._remove_warning()
        self._entry.set_text(str(text))
        self.emit("changed")

    def get_text(self, validate=True):
        if validate:
            self._validate()
        return self._entry.get_text()

    def set_today(self):
        today = datetime.datetime.today()
        text = today.strftime(const.DATE_FORMAT)
        self.set_text(text)

    def is_valid_date(self):
        try:
            self.get_text()
        except InvalidDateInput:
            return False
        return True

    def grab_focus(self):
        self._entry.grab_focus()
        self._entry.set_position(-1)

    def _remove_warning(self):
        self._entry.get_style_context().remove_class("warning")

    def _validate(self):
        self._remove_warning()
        date = self._entry.get_text()

        if self.can_empty and date == "":
            return
        try:
            datetime.datetime.strptime(date, const.DATE_FORMAT)
        except ValueError:
            self._entry.get_style_context().add_class("warning")
            raise InvalidDateInput


class CalendarPopover(Gtk.Popover):
    __gtype_name__ = "CalendarPopover"

    def __init__(self, entry):
        Gtk.Popover.__init__(self)
        self.set_position(Gtk.PositionType.BOTTOM)

        buttonapply = Gtk.Button.new_from_icon_name("icon_check", Gtk.IconSize.BUTTON)
        buttonapply.connect("clicked", self.on_buttonapply_clicked)
        buttoncancel = Gtk.Button.new_from_icon_name("icon_cancel", Gtk.IconSize.BUTTON)
        buttoncancel.connect("clicked", self.on_buttoncancel_clicked)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.get_style_context().add_class("linked")
        button_box.pack_start(buttonapply, False, False, 0)
        button_box.pack_start(buttoncancel, False, False, 0)

        calendar = Gtk.Calendar()
        calendar.connect("day-selected", self.on_day_selected)
        calendar.connect("day-selected-double-click", self.on_day_clicked)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        main_box.pack_start(button_box, False, False, 0)
        main_box.pack_start(calendar, False, False, 0)

        self._calendar = calendar
        self._entry = entry
        self._saved_date = entry.get_text(validate=False)
        if self._saved_date:
            try:
                year, month, day = map(int, self._saved_date.split("-"))
                calendar.select_month(month - 1, year)
                calendar.select_day(day)
                # Check for a valid date, mostly incorrect year
                datetime.date(year, month, day).strftime(const.DATE_FORMAT)
            except ValueError:
                # Raised by both splitting and setting an incorrect date
                date = datetime.date.today().strftime(const.DATE_FORMAT)
                self._saved_date = date
                self._entry.set_text(date)

        self.add(main_box)

    def on_buttonapply_clicked(self, _widget):
        self.popdown()

    def on_buttoncancel_clicked(self, _widget):
        if not self._entry.can_empty and self._saved_date == "":
            # Don't trigger the changed signal on the entry
            pass
        else:
            self._entry.set_text(self._saved_date)
        self.popdown()

    def on_day_selected(self, _widget):
        year, month, day = self._calendar.get_date()
        the_date = datetime.date(year, month + 1, day)

        if the_date:
            try:
                self._entry.set_text(the_date.strftime(const.DATE_FORMAT))
            except ValueError:
                pass
        else:
            self._entry.set_text("")

    def on_day_clicked(self, _widget):
        self.popdown()
