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


from gi.repository import Gtk

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.ui.messagedialog import QuestionDialog
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.database.models import (
    Pigeon,
    Colour,
    Sector,
    Type,
    Category,
    Racepoint,
    Strain,
    Loft,
    Weather,
    Wind,
)


class DataManager(builder.GtkBuilder):
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "DataManager.ui")

        # XXX: Translated strings are not unicode on some Windows XP systems
        #      that were tested.
        self.tables = {
            _("Colours"): Colour,
            _("Sectors"): Sector,
            _("Types"): Type,
            _("Categories"): Category,
            _("Racepoints"): Racepoint,
            _("Strains"): Strain,
            _("Lofts"): Loft,
            _("Weather"): Weather,
            _("Wind"): Wind,
        }
        comboboxes.fill_combobox(self.widgets.comboset, self.tables.keys())

        self._build_treeview()
        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show()

    # Callbacks
    def close_window(self, _widget, _event=None):
        self.widgets.window.destroy()

    # noinspection PyMethodMayBeStatic
    def on_buttonhelp_clicked(self, _widget):
        common.open_help(10)

    def on_buttonremove_clicked(self, _widget):
        dataset = self.widgets.comboset.get_active_text()
        item = self.widgets.comboitem.get_active_text()
        if QuestionDialog(messages.MSG_REMOVE_ITEM, self.widgets.window, (item, dataset)).run():
            table = self.tables[dataset]
            table.delete().where(table.get_item_column() == item).execute()
            index = self.widgets.comboitem.get_active()
            self.widgets.comboitem.remove(index)
            self.widgets.comboitem.set_active(0)

    def on_buttonadd_clicked(self, _widget):
        dataset = self.widgets.comboset.get_active_text()
        item = self.widgets.entryitem.get_text()
        table = self.tables[dataset]
        try:
            data = {table.get_item_column().name: item}
            table.insert(**data).execute()
        except errors.IntegrityError:
            # This item already exists or is empty
            pass
        self.widgets.entryitem.set_text("")
        self._fill_item_combobox(dataset)

    def on_comboset_changed(self, widget):
        dataset = widget.get_active_text()
        self._fill_item_combobox(dataset)

    def on_entryitem_changed(self, widget):
        value = len(widget.get_text()) > 0
        self.widgets.buttonadd.set_sensitive(value)

    def on_buttonsearch_clicked(self, _widget):
        self.widgets.messagebox.hide()
        self.widgets.liststore.clear()
        for pigeon in Pigeon.select().where(
            (Pigeon.visible == False) & ((Pigeon.sex != enums.Sex.youngbird) | (Pigeon.sex != enums.Sex.unknown))
        ):
            is_parent = Pigeon.select().where((Pigeon.sire == pigeon) | (Pigeon.dam == pigeon)).exists()
            if not is_parent:
                self.widgets.liststore.insert(0, [pigeon, False, pigeon.band])

        if len(self.widgets.liststore) == 0:
            self.widgets.messagebox.show()

    def on_buttoninfo_clicked(self, _widget):
        model, node = self.widgets.selection.get_selected()
        pigeon = self.widgets.liststore.get_value(node, 0)
        from pigeonplanner.ui.detailsview import DetailsDialog

        DetailsDialog(pigeon, self.widgets.window)

    def on_buttondelete_clicked(self, _widget):
        main_treeview = component.get("Treeview")
        for row_num in range(len(self.widgets.liststore) - 1, -1, -1):
            row = self.widgets.liststore[row_num]
            if not row[1]:
                continue
            corepigeon.remove_pigeon(row[0])
            # The path is only valid when the pigeon is actually shown
            main_path = main_treeview.get_path_for_pigeon(row[0])
            if main_path is not None:
                main_treeview.remove_row(main_path)
            # Do this last since we use row for other things as well
            self.widgets.liststore.remove(row.iter)
        self.widgets.buttondelete.set_sensitive(False)

    def on_selection_changed(self, selection):
        model, node = selection.get_selected()
        value = False if node is None else True
        self.widgets.buttoninfo.set_sensitive(value)

    def on_selection_toggled(self, _cell, path):
        row = self.widgets.liststore[path]
        row[1] = not row[1]
        value = row[1]
        if not value:
            for row in self.widgets.liststore:
                if row[1]:
                    value = True
                    break
        self.widgets.buttondelete.set_sensitive(value)

    # Private methods
    def _fill_item_combobox(self, dataset):
        table = self.tables[dataset]
        comboboxes.fill_combobox(self.widgets.comboitem, table.get_data_list())
        value = self.widgets.comboitem.get_active_text() is not None
        self.widgets.buttonremove.set_sensitive(value)

    def _build_treeview(self):
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)
        self.widgets.liststore = Gtk.ListStore(object, bool, str)
        self.widgets.treeview.set_model(self.widgets.liststore)

        textrenderer = Gtk.CellRendererText()
        boolrenderer = Gtk.CellRendererToggle()
        boolrenderer.connect("toggled", self.on_selection_toggled)

        check = Gtk.CheckButton()
        check.set_active(True)
        check.show()
        mark_column = Gtk.TreeViewColumn(None, boolrenderer, active=1)
        mark_column.set_widget(check)
        mark_column.set_sort_column_id(1)
        self.widgets.treeview.append_column(mark_column)
        band_column = Gtk.TreeViewColumn(None, textrenderer, text=2)
        band_column.set_sort_column_id(2)
        self.widgets.treeview.append_column(band_column)
