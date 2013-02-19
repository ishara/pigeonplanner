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


import time

import gtk

from pigeonplanner import const
from pigeonplanner import errors
from pigeonplanner import builder
from pigeonplanner.ui import utils
from pigeonplanner.ui.messagedialog import ErrorDialog


class Calendar(builder.GtkBuilder):
    def __init__(self, parent, database, notification_id=None):
        builder.GtkBuilder.__init__(self, "Calendar.ui")

        self.db = database

        self._mode = None
        self.widgets.textbuffer = self.widgets.textview.get_buffer()
        self._entries = self.get_objects_from_prefix("entry")
        self._entries.append(self.widgets.textbuffer)
        self._normalbuttons = [self.widgets.buttonadd,
                               self.widgets.buttonedit,
                               self.widgets.buttonremove]
        self._editbuttons = [self.widgets.buttonsave, self.widgets.buttoncancel]
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect('changed', self.on_selection_changed)
        self._fill_treeview(notification_id)
        if notification_id is None:
            self.widgets.selection.select_path(0)

        self.widgets.calendarwindow.set_transient_for(parent)
        self.widgets.calendarwindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.widgets.calendarwindow.destroy()

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        self._set_widgets(True)
        self._empty_entries()

    def on_buttonedit_clicked(self, widget):
        self._mode = const.EDIT
        self._set_widgets(True)

        notify = int(self.widgets.labelnotify.get_text())
        if notify < 0:
            self.widgets.checknotify.set_active(False)
            self.widgets.spinnotify.set_value(1)
        else:
            self.widgets.checknotify.set_active(True)
            self.widgets.spinnotify.set_value(notify)

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.liststore.get_path(rowiter)
        key = model[rowiter][0]

        self.db.delete_from_table(self.db.EVENTS, key, 0)
        self.widgets.liststore.remove(rowiter)
        self.widgets.selection.select_path(path)

    def on_buttonsave_clicked(self, widget):
        try:
            data = self._get_entry_data()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.widgets.calendarwindow)
            return
        date_, type_ = data[0], data[1]
        self._set_widgets(False)
        if self._mode == const.ADD:
            rowid = self.db.insert_into_table(self.db.EVENTS, data)
            rowiter = self.widgets.liststore.insert(0, [rowid, date_, type_])
            self.widgets.selection.select_iter(rowiter)
            path = self.widgets.liststore.get_path(rowiter)
            self.widgets.treeview.scroll_to_cell(path)
        else:
            data = data + (self._get_event_key(),)
            self.db.update_table(self.db.EVENTS, data, 1, 0)
            model, rowiter = self.widgets.selection.get_selected()
            self.widgets.liststore.set(rowiter, 1, date_, 2, type_)
            self.widgets.selection.emit('changed')

    def on_buttoncancel_clicked(self, widget):
        self._set_widgets(False)
        self.widgets.selection.emit('changed')

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()

        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        if rowiter:
            utils.set_multiple_sensitive(widgets, True)
        else:
            utils.set_multiple_sensitive(widgets, False)
            self._empty_entries()
            return

        data = self.db.get_event(model[rowiter][0])
        self.widgets.entrydate.set_text(data[1])
        self.widgets.entrytype.set_text(data[2])
        self.widgets.entrydescription.set_text(data[3])
        self.widgets.textbuffer.set_text(data[4])

        if data[5]:
            self.widgets.labelnotification.set_text(
                    _("Notification set on %s days") %data[6])
            self.widgets.labelnotify.set_text(str(data[6]))
        else:
            self.widgets.labelnotification.set_text(_("No notification set"))
            self.widgets.labelnotify.set_text("-1")

    def on_checknotify_toggled(self, widget):
        utils.set_multiple_sensitive([self.widgets.alignnotify], widget.get_active())

    # Internal methods
    def _fill_treeview(self, notification_id=None):
        self.widgets.liststore.clear()
        for item in self.db.get_all_events():
            rowiter = self.widgets.liststore.insert(0, [item[0], item[1], item[2]])
            if notification_id is not None and item[0] == notification_id:
                self.widgets.selection.select_iter(rowiter)
                self.widgets.treeview.scroll_to_cell(
                                    self.widgets.liststore.get_path(rowiter))
        self.widgets.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def _set_widgets(self, value):
        """
        Set the widgets tot their correct state for adding/editing

        @param value: True for edit mode, False for normal
        """

        utils.set_multiple_sensitive([self.widgets.treeview], not value)
        utils.set_multiple_visible(self._normalbuttons+[self.widgets.hboxnotify], not value)
        utils.set_multiple_visible(self._editbuttons+[self.widgets.vboxnotify], value)

        shadow = gtk.SHADOW_NONE if value else gtk.SHADOW_IN
        for entry in self._entries:
            if isinstance(entry, gtk.Entry):
                entry.set_has_frame(value)
                entry.set_editable(value)
                entry.get_parent().set_shadow_type(shadow)
            else:
                self.widgets.textview.set_editable(value)

        self.widgets.entrydate.set_editable(value)
        self.widgets.entrydate.grab_focus()

    def _get_entry_data(self):
        date = self.widgets.entrydate.get_text()
        notify = self.widgets.checknotify.get_active()
        interval = self.widgets.spinnotify.get_value()
        notifyday = 0
        if notify:
            year, month, day = date.split('-')
            time_tuple = (int(year), int(month), int(day), 0, 0, 0, 0, 0, 0)
            eventday = time.mktime(time_tuple)
            notifyday = eventday - (interval*86400)

        return (date,
                self.widgets.entrytype.get_text(),
                self.widgets.entrydescription.get_text(),
                self.widgets.textbuffer.get_text(*self.widgets.textbuffer.get_bounds()),
                int(notify),
                interval,
                notifyday,
                )

    def _get_event_key(self):
        model, rowiter = self.widgets.selection.get_selected()
        return model[rowiter][0]

    def _empty_entries(self):
        for entry in self._entries:
            entry.set_text('')

        self.widgets.labelnotification.set_text("")
        self.widgets.labelnotify.set_text("-1")

