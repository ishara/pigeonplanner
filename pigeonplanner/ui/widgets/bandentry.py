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


import re

import gtk
import gobject

from pigeonplanner.ui import dialogs
from pigeonplanner.core import config
from pigeonplanner.core import checks
from pigeonplanner.core import errors


class BandEntry(gtk.HBox):
    __gtype_name__ = "BandEntry"
    __gsignals__ = {"search-clicked": (gobject.SIGNAL_RUN_LAST, object, ())}
    can_empty = gobject.property(type=bool, default=False, nick="Can empty")
    show_band_format = gobject.property(type=bool, default=True, nick="Show band format")

    def __init__(self, editable=False, can_empty=False, has_search=False, show_band_format=True):
        gtk.HBox.__init__(self)
        self.set_spacing(2)

        self.band_format = config.get("options.band-format")
        self._build_ui()
        self.can_empty = can_empty
        self.has_search = self._has_search = has_search
        self.editable = self._editable = editable
        self.show_band_format = show_band_format

    def _build_ui(self):
        self._entry_display = gtk.Entry()
        self._entry_display.set_alignment(.5)
        self._entry_display.set_editable(False)
        self._entry_display.set_has_frame(False)
        self._entry_display.set_activates_default(False)
        self._viewport_display = gtk.Viewport()
        self._viewport_display.set_no_show_all(True)
        self._viewport_display.set_shadow_type(gtk.SHADOW_IN)
        self._viewport_display.add(self._entry_display)

        self.entry_country = gtk.Entry()
        self.entry_country.set_width_chars(4)
        self.entry_country.set_tooltip_text(_("Country"))
        self.entry_country.set_activates_default(True)
        self.entry_letters = gtk.Entry()
        self.entry_letters.set_width_chars(6)
        self.entry_letters.set_tooltip_text(_("Letters"))
        self.entry_letters.set_activates_default(True)
        self.entry_number = gtk.Entry()
        self.entry_number.set_width_chars(10)
        self.entry_number.set_tooltip_text(_("Number"))
        self.entry_number.set_activates_default(True)
        self.entry_year = gtk.Entry()
        self.entry_year.set_width_chars(4)
        self.entry_year.set_tooltip_text(_("Year"))
        self.entry_year.set_max_length(4)
        self.entry_year.set_activates_default(True)
        self._hbox_band = gtk.HBox(False, 2)
        self._hbox_band.set_no_show_all(True)
        self._hbox_band.pack_start(self.entry_country, False, False, 0)
        self._hbox_band.pack_start(self.entry_letters, False, False, 0)
        self._hbox_band.pack_start(self.entry_number, False, False, 0)
        self._hbox_band.pack_start(self.entry_year, False, False, 0)

        self._button_image = gtk.image_new_from_stock(gtk.STOCK_PROPERTIES, gtk.ICON_SIZE_BUTTON)
        self._button_help = gtk.Button()
        self._button_help.add(self._button_image)
        self._button_help.set_relief(gtk.RELIEF_NONE)
        self._button_help.set_focus_on_click(False)
        self._button_help.set_no_show_all(True)
        self._button_help.set_tooltip_text(_("Information"))
        self._button_help.connect("clicked", self.on_button_help_clicked)

        image = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        self._button_search = gtk.Button()
        self._button_search.add(image)
        self._button_search.set_relief(gtk.RELIEF_NONE)
        self._button_search.set_focus_on_click(False)
        self._button_search.set_no_show_all(True)
        self._button_search.connect("clicked", self.on_button_search_clicked)

        self.pack_start(self._viewport_display, True, True, 0)
        self.pack_start(self._hbox_band, False, False, 0)
        self.pack_start(self._button_help, False, False, 0)
        self.pack_start(self._button_search, False, False, 0)

    def on_button_help_clicked(self, widget):
        self.get_toplevel().get_child().set_sensitive(False)
        BandEntryPopup(self)

    def on_button_search_clicked(self, widget):
        try:
            band_tuple, sex, year = self.emit("search-clicked")
        except TypeError:
            return
        parent = self.get_toplevel()
        dialog = dialogs.PigeonListDialog(parent)
        dialog.fill_treeview(band_tuple, sex, year)
        response = dialog.run()
        if response == gtk.RESPONSE_APPLY:
            pigeon = dialog.get_selected()
            self.set_pigeon(pigeon)
        dialog.destroy()

    def get_has_search(self):
        return self._has_search

    def set_has_search(self, has_search):
        self._has_search = has_search
        self._button_search.set_visible(has_search)
        self._button_search.child.set_visible(has_search)
    has_search = gobject.property(get_has_search, set_has_search, bool, False, nick="Has search")

    def get_editable(self):
        return self._editable

    def set_editable(self, editable):
        self._editable = editable
        self._viewport_display.set_visible(not editable)
        self._viewport_display.forall(lambda child, value: child.set_visible(value), not editable)
        self._hbox_band.set_visible(editable)
        self._hbox_band.forall(lambda child, value: child.set_visible(value), editable)
        self._button_help.set_visible(editable)
        self._button_help.child.set_visible(editable)
    editable = gobject.property(get_editable, set_editable, bool, False, nick="Editable")

    def is_empty(self):
        return self.get_band(False) == ("", "", "", "")

    def set_pigeon(self, pigeon):
        if pigeon is None:
            self.set_band("", "", "", "")
            self._entry_display.set_text("")
        else:
            self.band_format = pigeon.band_format
            self.set_band(pigeon.band_country, pigeon.band_letters, pigeon.band_number, pigeon.band_year)
            self._entry_display.set_text(pigeon.band)

    def set_band(self, country, letters, number, year):
        self._unwarn()
        self.entry_country.set_text(country)
        self.entry_letters.set_text(letters)
        self.entry_number.set_text(number)
        self.entry_year.set_text(year)

    def get_band(self, validate=True):
        number, year = self.entry_number.get_text(), self.entry_year.get_text()
        if validate:
            self.__validate(number, year)
        return self.entry_country.get_text(), self.entry_letters.get_text(), number, year

    def clear(self):
        self.set_band("", "", "", "")
        self._entry_display.set_text("")

    def grab_focus(self):
        self.entry_country.grab_focus()
        self.entry_country.set_position(-1)

    def _warn(self):
        self.entry_number.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_STOP)

    def _unwarn(self):
        self.entry_number.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, None)

    def __validate(self, number, year):
        if self.can_empty and (number == "" and year == ""):
            return

        try:
            checks.check_ring_entry(number, year)
        except errors.InvalidInputError:
            self._warn()
            raise

        self._unwarn()


class BandItemCombobox(gtk.ComboBox):
    __gtype_name__ = "BandItemCombobox"

    def __init__(self):
        store = gtk.ListStore(str, str)
        gtk.ComboBox.__init__(self, store)

        items = [
            (_("Country"), "{country}"),
            (_("Letters"), "{letters}"),
            (_("Number"), "{number}"),
            (_("Year"), "{year}"),
            (_("Year (short)"), "{year_short}"),
            (_("Empty"), "{empty}"),
        ]
        for item in items:
            store.append(item)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_active(0)

    @property
    def formatter(self):
        ls_iter = self.get_active_iter()
        return self.get_model().get(ls_iter, 1)[0]

    def select_value(self, value):
        for row in self.get_model():
            if row[1] == value:
                self.set_active_iter(row.iter)
                break


class BandEntryPopup(gtk.Window):
    __gtype_name__ = "BandEntryPopup"

    def __init__(self, main_entry):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_destroy_with_parent(True)
        self.set_transient_for(main_entry.get_toplevel())
        self.set_border_width(8)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_modal(True)

        self.main_entry = main_entry

        self._build_ui()
        self._set_band_entry_values()
        self._set_band_format_values()
        self.update_preview()
        # Important. Wait until after setting the initial format values to connect those widget's handlers.
        self._connect_handlers()
        self.show_all()
        # Important. Position the window only after all widgets are shown to get the proper dimensions.
        self._set_position()

    def update_preview(self, *args):
        fields = [
            self._combobox1.formatter,
            self._entry_sep1.get_text(),
            self._combobox2.formatter,
            self._entry_sep2.get_text(),
            self._combobox3.formatter,
            self._entry_sep3.get_text(),
            self._combobox4.formatter,
        ]
        format_string = "".join(fields)
        values = {
            "country": self._entry_country.get_text(),
            "letters": self._entry_letters.get_text(),
            "number": self._entry_number.get_text(),
            "year": self._entry_year.get_text(),
            "year_short": self._entry_year.get_text()[2:],
            "empty": "",
        }
        preview = format_string.format(**values)
        self._label_preview.set_text(preview)
        self.main_entry.band_format = format_string

    def on_button_apply_clicked(self, widget):
        self.main_entry.set_band(
            self._entry_country.get_text(),
            self._entry_letters.get_text(),
            self._entry_number.get_text(),
            self._entry_year.get_text()
        )
        if self.checkbox_default.get_active():
            config.set("options.band-format", self.main_entry.band_format)
        self.main_entry.get_toplevel().get_child().set_sensitive(True)
        self.destroy()

    def _build_ui(self):
        # Entry
        self._entry_country = gtk.Entry()
        self._entry_country.set_width_chars(4)
        self._entry_country.set_tooltip_text(_("Country"))
        self._entry_letters = gtk.Entry()
        self._entry_letters.set_width_chars(6)
        self._entry_letters.set_tooltip_text(_("Letters"))
        self._entry_number = gtk.Entry()
        self._entry_number.set_width_chars(10)
        self._entry_number.set_tooltip_text(_("Number"))
        self._entry_year = gtk.Entry()
        self._entry_year.set_width_chars(4)
        self._entry_year.set_tooltip_text(_("Year"))
        self._entry_year.set_max_length(4)

        button_image = gtk.image_new_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        button_apply = gtk.Button()
        button_apply.add(button_image)
        button_apply.set_focus_on_click(False)
        button_apply.connect("clicked", self.on_button_apply_clicked)

        self._hbox_entry = gtk.HBox(False, 2)
        self._hbox_entry.pack_start(self._entry_country, False, False, 0)
        self._hbox_entry.pack_start(self._entry_letters, False, False, 0)
        self._hbox_entry.pack_start(self._entry_number, False, False, 0)
        self._hbox_entry.pack_start(self._entry_year, False, False, 0)
        self._hbox_entry.pack_start(button_apply, False, False, 0)

        align_entry = gtk.Alignment()
        align_entry.set(1.0, 0.5, 0.5, 1.0)
        align_entry.add(self._hbox_entry)

        # Information
        label_info1 = gtk.Label("%s %s, %s, %s, %s" %
                                (_("The fields are:"), _("Country"), _("Letters"), _("Number"), _("Year")))
        label_info1.set_alignment(0.0, 0.5)
        label_info2 = gtk.Label(_("The number and year fields are required."))
        label_info2.set_alignment(0.0, 0.5)
        label_info3 = gtk.Label(_("The year has to be four digits long."))
        label_info3.set_alignment(0.0, 0.5)

        vbox_info = gtk.VBox(False, 8)
        vbox_info.pack_start(label_info1, False, True, 0)
        vbox_info.pack_start(label_info2, False, True, 0)
        vbox_info.pack_start(label_info3, False, True, 0)

        align_info = gtk.Alignment()
        align_info.set_padding(4, 4, 12, 4)
        align_info.add(vbox_info)
        frame_info = gtk.Frame("<b>%s</b>" % _("Information"))
        frame_info.get_label_widget().set_use_markup(True)
        frame_info.add(align_info)

        # Band format
        self._entry_sep1 = gtk.Entry()
        self._entry_sep1.set_width_chars(4)
        self._entry_sep2 = gtk.Entry()
        self._entry_sep2.set_width_chars(4)
        self._entry_sep3 = gtk.Entry()
        self._entry_sep3.set_width_chars(4)

        self._combobox1 = BandItemCombobox()
        self._combobox2 = BandItemCombobox()
        self._combobox3 = BandItemCombobox()
        self._combobox4 = BandItemCombobox()

        self._hbox_format = gtk.HBox(False, 0)
        self._hbox_format.pack_start(self._combobox1, False, False, 0)
        self._hbox_format.pack_start(self._entry_sep1, False, False, 0)
        self._hbox_format.pack_start(self._combobox2, False, False, 0)
        self._hbox_format.pack_start(self._entry_sep2, False, False, 0)
        self._hbox_format.pack_start(self._combobox3, False, False, 0)
        self._hbox_format.pack_start(self._entry_sep3, False, False, 0)
        self._hbox_format.pack_start(self._combobox4, False, False, 0)

        self._label_preview = gtk.Label()
        self.checkbox_default = gtk.CheckButton(_("Make this format the default"))

        vbox_format = gtk.VBox(False, 8)
        vbox_format.pack_start(self._hbox_format, False, False, 0)
        vbox_format.pack_start(self._label_preview, False, False, 0)
        vbox_format.pack_start(self.checkbox_default, False, False, 0)

        align_format = gtk.Alignment()
        align_format.set_padding(4, 4, 12, 4)
        align_format.add(vbox_format)
        frame_format = gtk.Frame("<b>%s</b>" % _("Band format"))
        frame_format.get_label_widget().set_use_markup(True)
        frame_format.add(align_format)

        # Main layout
        vbox = gtk.VBox(False, 8)
        vbox.pack_start(align_entry, False, False, 0)
        vbox.pack_start(frame_info, False, False, 0)
        if self.main_entry.show_band_format:
            vbox.pack_start(frame_format, False, False, 0)

        self.add(vbox)

    def _connect_handlers(self):
        for child in self._hbox_entry.get_children():
            if isinstance(child, gtk.Entry):
                child.connect("changed", self.update_preview)
        for child in self._hbox_format.get_children():
            child.connect("changed", self.update_preview)

    def _set_band_entry_values(self):
        self._entry_country.set_text(self.main_entry.entry_country.get_text())
        self._entry_letters.set_text(self.main_entry.entry_letters.get_text())
        self._entry_number.set_text(self.main_entry.entry_number.get_text())
        self._entry_year.set_text(self.main_entry.entry_year.get_text())
        self._entry_country.grab_focus()
        self._entry_country.set_position(-1)

    def _set_band_format_values(self):
        val1, val2, val3, val4 = re.findall("{\w+}", self.main_entry.band_format)
        self._combobox1.select_value(val1)
        self._combobox2.select_value(val2)
        self._combobox3.select_value(val3)
        self._combobox4.select_value(val4)

        sep1, sep2, sep3 = re.findall("}(.*?){", self.main_entry.band_format)
        self._entry_sep1.set_text(sep1)
        self._entry_sep2.set_text(sep2)
        self._entry_sep3.set_text(sep3)

    def _set_position(self):
        window = self.main_entry.get_parent_window()
        x, y = gtk.gdk.Window.get_origin(window)

        x += self.main_entry.allocation.x
        x += self.main_entry.allocation.width / 2
        x -= self.allocation.width / 2
        y += self.main_entry.allocation.y
        y -= self.get_border_width()

        self.move(x, y)


if __name__ == "__main__":
    widget = BandEntry()
    win = gtk.Window()
    win.connect("delete-event", gtk.main_quit)
    win.set_position(gtk.WIN_POS_CENTER)
    win.add(widget)
    win.show_all()
    gtk.main()
