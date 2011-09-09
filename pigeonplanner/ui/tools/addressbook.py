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
from ui.messagedialog import QuestionDialog


def check_user_info(parent, database, name):
    """
    Check if the user has entered his personal info

    @param parent: A parent window
    @param database: The database instance
    @param name: The name of the user
    """

    if name == '':
        if QuestionDialog(messages.MSG_NO_INFO, parent).run():
            book = AddressBook(parent, database)
            book.on_buttonadd_clicked(None)
            book.checkme.set_active(True)
            return False
    return True


class AddressBook(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, "AddressBook.ui")

        self.db = database

        self._mode = None
        self._entries = self.get_objects_from_prefix("entry")
        self._normalbuttons = [self.buttonadd, self.buttonedit, self.buttonremove]
        self._editbuttons = [self.buttonsave, self.buttoncancel]
        self._fill_treeview()
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)
        self._selection.select_path(0)

        self.addressbookwindow.set_transient_for(parent)
        self.addressbookwindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.addressbookwindow.destroy()

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        self._set_widgets(True)
        self._empty_entries()

    def on_buttonedit_clicked(self, widget):
        self._mode = const.EDIT
        self._set_widgets(True)

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        key, name = model[rowiter][0], model[rowiter][1]

        if not QuestionDialog(messages.MSG_REMOVE_ADDRESS,
                              self.addressbookwindow, name).run():
            return

        self.db.delete_from_table(self.db.ADDR, key, 0)
        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def on_buttonsave_clicked(self, widget):
        self._set_widgets(False)
        data = self._get_entry_data()
        name = data[0]
        if self._mode == const.ADD:
            rowid = self.db.insert_into_table(self.db.ADDR, data)
            rowiter = self.liststore.insert(0, [rowid, name])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        else:
            data = data + (self._get_address_key(),)
            self.db.update_table(self.db.ADDR, data, 1, 0)
            model, rowiter = self._selection.get_selected()
            self.liststore.set_value(rowiter, 1, name)
            self._selection.emit('changed')

    def on_buttoncancel_clicked(self, widget):
        self._set_widgets(False)
        self._selection.emit('changed')

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()

        widgets = [self.buttonremove, self.buttonedit]
        if rowiter:
            self.set_multiple_sensitive(widgets, True)
        else:
            self.set_multiple_sensitive(widgets, False)
            self._empty_entries()
            return

        data = self.db.get_address(model[rowiter][0])
        self.entryname.set_text(data[1])
        self.entrystreet.set_text(data[2])
        self.entryzip.set_text(data[3])
        self.entrycity.set_text(data[4])
        self.entrycountry.set_text(data[5])
        self.entryphone.set_text(data[6])
        self.entryemail.set_text(data[7])
        self.entrycomment.set_text(data[8])
        self.checkme.set_active(data[9])

    # Internal methods
    def _fill_treeview(self):
        self.liststore.clear()
        for item in self.db.get_all_addresses():
            self.liststore.insert(0, [item[0], item[1]])
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def _set_widgets(self, value):
        """
        Set the widgets tot their correct state for adding/editing

        @param value: True for edit mode, False for normal
        """

        self.set_multiple_sensitive([self.treeview], not value)
        self.set_multiple_visible(self._normalbuttons, not value)
        self.set_multiple_visible(self._editbuttons, value)
        show_me = self.db.get_own_address() is None or \
                    (self._mode == const.EDIT and
                     self.db.get_own_address()[0] == self._get_address_key())
        self.set_multiple_visible([self.checkme], show_me if value else False)

        shadow = gtk.SHADOW_NONE if value else gtk.SHADOW_IN
        for entry in self._entries:
            entry.set_has_frame(value)
            entry.set_editable(value)
            entry.get_parent().set_shadow_type(shadow)

        self.entryname.grab_focus()
        self.entryname.set_position(-1)

    def _get_entry_data(self):
        return (self.entryname.get_text(),
                self.entrystreet.get_text(),
                self.entryzip.get_text(),
                self.entrycity.get_text(),
                self.entrycountry.get_text(),
                self.entryphone.get_text(),
                self.entryemail.get_text(),
                self.entrycomment.get_text(),
                int(self.checkme.get_active())
                )

    def _get_address_key(self):
        model, rowiter = self._selection.get_selected()
        return model[rowiter][0]

    def _empty_entries(self):
        for entry in self._entries:
            entry.set_text('')

