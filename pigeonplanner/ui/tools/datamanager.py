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

import const
import builder
import messages
from ui import dialogs
from ui.widgets import comboboxes
from translation import gettext as _


class DataManager(builder.GtkBuilder):
    def __init__(self, parent, database, parser):
        builder.GtkBuilder.__init__(self, "DataManager.ui")

        self.database = database
        self.parser = parser
        if parser is None:
            self.frameobjects.set_sensitive(False)

        # XXX: Translated strings are not unicode on some Windows XP systems
        # that were tested.
        self.tables = {unicode(_("Colours")): self.database.COLOURS,
                       unicode(_("Sectors")): self.database.SECTORS,
                       unicode(_("Types")): self.database.TYPES,
                       unicode(_("Categories")): self.database.CATEGORIES,
                       unicode(_("Racepoints")): self.database.RACEPOINTS,
                       unicode(_("Strains")): self.database.STRAINS,
                       unicode(_("Lofts")): self.database.LOFTS,
                       unicode(_("Weather")): self.database.WEATHER,
                       unicode(_("Wind")): self.database.WIND}
        comboboxes.fill_combobox(self.comboset, self.tables.keys())

        self._build_treeview()
        self.window.set_transient_for(parent)
        self.window.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.window.destroy()

    def on_buttonremove_clicked(self, widget):
        dataset = unicode(self.comboset.get_active_text())
        item = self.comboitem.get_active_text()
        d = dialogs.MessageDialog(const.QUESTION, messages.MSG_REMOVE_ITEM,
                                  self.window, (item, dataset))
        if d.yes:
            self.database.delete_from_table(self.tables[dataset], item)
            index = self.comboitem.get_active()
            self.comboitem.remove_text(index)
            self.comboitem.set_active(0)

    def on_buttonadd_clicked(self, widget):
        dataset = unicode(self.comboset.get_active_text())
        item = (self.entryitem.get_text(), )
        if dataset == _("Racepoints"):
            item = item+("", "", "", "")
        self.database.insert_into_table(self.tables[dataset], item)
        self.entryitem.set_text('')
        self._fill_item_combobox(dataset)

    def on_comboset_changed(self, widget):
        dataset = unicode(widget.get_active_text())
        self._fill_item_combobox(dataset)

    def on_entryitem_changed(self, widget):
        value = len(widget.get_text()) > 0
        self.buttonadd.set_sensitive(value)

    def on_buttonsearch_clicked(self, widget):
        self.liststore.clear()
        for pindex, pigeon in self.parser.pigeons.iteritems():
            if pigeon.get_visible(): continue
            sex = int(pigeon.get_sex())
            if sex == const.YOUNG: continue
            is_parent = self.database.has_parent(sex, *pigeon.get_band())
            if not is_parent:
                self.liststore.insert(0, [pigeon, False, pigeon.get_band_string()])

    def on_buttoninfo_clicked(self, widget):
        model, node = self.selection.get_selected()
        pigeon = self.liststore.get_value(node, 0)
        if not pigeon.get_pindex() in self.parser.pigeons:
            return
        from ui.detailsview import DetailsDialog
        DetailsDialog(self.database, self.parser, pigeon, self.window)

    def on_buttondelete_clicked(self, widget):
        for row_num in range(len(self.liststore)-1, -1, -1):
            row = self.liststore[row_num]
            if not row[1]: continue
            pindex = row[0].get_pindex()
            self.parser.remove_pigeon(pindex)
            self.liststore.remove(row.iter)
        self.buttondelete.set_sensitive(False)

    def on_selection_changed(self, selection):
        model, node = selection.get_selected()
        value = False if node is None else True
        self.buttoninfo.set_sensitive(value)

    def on_selection_toggled(self, cell, path):
        row = self.liststore[path]
        row[1] = not row[1]
        value = row[1]
        if not value:
            for row in self.liststore:
                if row[1]:
                    value = True
                    break
        self.buttondelete.set_sensitive(value)

    # Private methods
    def _fill_item_combobox(self, dataset):
        data = self.database.select_from_table(self.tables[dataset])
        comboboxes.fill_combobox(self.comboitem, data)
        value = self.comboitem.get_active_text() is not None
        self.buttonremove.set_sensitive(value)

    def _build_treeview(self):
        self.selection = self.treeview.get_selection()
        self.selection.connect('changed', self.on_selection_changed)
        self.liststore = gtk.ListStore(object, bool, str)
        self.treeview.set_model(self.liststore)

        textrenderer = gtk.CellRendererText()
        boolrenderer = gtk.CellRendererToggle()
        boolrenderer.connect('toggled', self.on_selection_toggled)

        check = gtk.CheckButton()
        check.set_active(True)
        check.show()
        mark_column = gtk.TreeViewColumn(None, boolrenderer, active=1)
        mark_column.set_widget(check)
        mark_column.set_sort_column_id(1)
        self.treeview.append_column(mark_column)
        band_column = gtk.TreeViewColumn(None, textrenderer, text=2)
        band_column.set_sort_column_id(2)
        self.treeview.append_column(band_column)

