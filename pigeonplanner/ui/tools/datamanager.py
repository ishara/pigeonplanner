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


from pigeonplanner import const
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner.ui import dialogs
from pigeonplanner.ui.widgets import comboboxes


class DataManager(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, const.GLADEDATAMGR)

        self.database = database

        self.tables = {_("Colours"): self.database.COLOURS,
                       _("Sectors"): self.database.SECTORS,
                       _("Types"): self.database.TYPES,
                       _("Categories"): self.database.CATEGORIES,
                       _("Racepoints"): self.database.RACEPOINTS,
                       _("Strains"): self.database.STRAINS,
                       _("Lofts"): self.database.LOFTS,
                       _("Weather"): self.database.WEATHER,
                       _("Wind"): self.database.WIND}
        comboboxes.fill_combobox(self.comboset, self.tables.keys())
        comboboxes.fill_combobox(self.combosetadd, self.tables.keys())

        self.managerwindow.set_transient_for(parent)
        self.managerwindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.managerwindow.destroy()

    def on_buttonremove_clicked(self, widget):
        dataset = unicode(self.comboset.get_active_text())
        item = self.comboitem.get_active_text()
        d = dialogs.MessageDialog(const.QUESTION, messages.MSG_REMOVE_ITEM,
                                  self.managerwindow, (item, dataset))
        if d.yes:
            self.database.delete_from_table(self.tables[dataset], item)
            index = self.comboitem.get_active()
            self.comboitem.remove_text(index)
            self.comboitem.set_active(0)

    def on_buttonadd_clicked(self, widget):
        dataset = unicode(self.combosetadd.get_active_text())
        item = (self.entryitem.get_text(), )
        if dataset == _("Racepoints"):
            item = item+("", "", "")
        self.database.insert_into_table(self.tables[dataset], item)
        self.entryitem.set_text('')
        if dataset == self.comboset.get_active_text():
            self._fill_item_combobox(dataset)

    def on_comboset_changed(self, widget):
        dataset = unicode(widget.get_active_text())
        self._fill_item_combobox(dataset)

    def on_entryitem_changed(self, widget):
        value = len(widget.get_text()) > 0
        self.buttonadd.set_sensitive(value)

    # Private methods
    def _fill_item_combobox(self, dataset):
        data = self.database.select_from_table(self.tables[dataset])
        comboboxes.fill_combobox(self.comboitem, data)
        value = self.comboitem.get_active_text() is not None
        self.buttonremove.set_sensitive(value)

