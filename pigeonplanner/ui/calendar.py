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
import time

import gtk

from pigeonplanner import const
from pigeonplanner import checks
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner.ui import dialogs


class Calendar(builder.GtkBuilder):
    def __init__(self, parent, database, notification_id=None):
        builder.GtkBuilder.__init__(self, const.GLADECALENDAR)

        self.db = database

        self._mode = None
        self._textbuffer = self.textview.get_buffer()
        self._entries = self.get_objects_from_prefix("entry")
        self._entries.append(self._textbuffer)
        self._normalbuttons = [self.buttonadd, self.buttonedit, self.buttonremove]
        self._editbuttons = [self.buttonsave, self.buttoncancel]
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)
        self._fill_treeview(notification_id)
        if notification_id is None:
            self._selection.select_path(0)

        self.calendarwindow.set_transient_for(parent)
        self.calendarwindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.calendarwindow.destroy()

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        self._set_widgets(True)
        self._empty_entries()

    def on_buttonedit_clicked(self, widget):
        self._mode = const.EDIT
        self._set_widgets(True)

        notify = int(self.labelnotify.get_text())
        if notify < 0:
            self.checknotify.set_active(False)
            self.spinnotify.set_value(1)
        else:
            self.checknotify.set_active(True)
            self.spinnotify.set_value(notify)

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        key = model[rowiter][0]

        self.db.delete_from_table(self.db.EVENTS, key, 0)
        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def on_buttonsave_clicked(self, widget):
        data = self._get_entry_data()
        date, type_ = data[0], data[1]
        if not checks.check_date_input(date):
            dialogs.MessageDialog(const.ERROR, messages.MSG_INVALID_FORMAT,
                                  self.calendarwindow)
            return
        self._set_widgets(False)
        if self._mode == const.ADD:
            rowid = self.db.insert_into_table(self.db.EVENTS, data)
            rowiter = self.liststore.insert(0, [rowid, date, type_])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        else:
            data = data + (self._get_event_key(),)
            self.db.update_table(self.db.EVENTS, data, 1, 0)
            model, rowiter = self._selection.get_selected()
            self.liststore.set(rowiter, 1, date, 2, type_)
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

        data = self.db.get_event(model[rowiter][0])
        self.entrydate.set_text(data[1])
        self.entrytype.set_text(data[2])
        self.entrydescription.set_text(data[3])
        self._textbuffer.set_text(data[4])

        if data[5]:
            self.labelnotification.set_text(
                    _("Notification set on %s days") %data[6])
            self.labelnotify.set_text(str(data[6]))
        else:
            self.labelnotification.set_text(_("No notification set"))
            self.labelnotify.set_text("-1")

    def on_dateicon_pressed(self, widget, icon, event):
        #TODO
        pass

    def on_checknotify_toggled(self, widget):
        self.set_multiple_sensitive([self.alignnotify], widget.get_active())

    # Internal methods
    def _fill_treeview(self, notification_id=None):
        self.liststore.clear()
        for item in self.db.get_all_events():
            rowiter = self.liststore.insert(0, [item[0], item[1], item[2]])
            if notification_id is not None and item[0] == notification_id:
                self._selection.select_iter(rowiter)
                self.treeview.scroll_to_cell(self.liststore.get_path(rowiter))
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def _set_widgets(self, value):
        """
        Set the widgets tot their correct state for adding/editing

        @param value: True for edit mode, False for normal
        """

        self.set_multiple_sensitive([self.treeview], not value)
        self.set_multiple_visible(self._normalbuttons+[self.hboxnotify], not value)
        self.set_multiple_visible(self._editbuttons+[self.vboxnotify], value)

        shadow = gtk.SHADOW_NONE if value else gtk.SHADOW_IN
        for entry in self._entries:
            if isinstance(entry, gtk.Entry):
                entry.set_has_frame(value)
                entry.set_editable(value)
                entry.get_parent().set_shadow_type(shadow)
            else:
                self.textview.set_editable(value)

#        icon = os.path.join(const.IMAGEDIR, 'icon_calendar.png')
#        pixbuf = gtk.gdk.pixbuf_new_from_file(icon) if value else None
#        self.entrydate.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pixbuf)

        self.entrydate.grab_focus()
        self.entrydate.set_position(-1)

    def _get_entry_data(self):
        date = self.entrydate.get_text()
        notify = self.checknotify.get_active()
        interval = self.spinnotify.get_value()
        notifyday = 0
        if notify:
            year, month, day = date.split('-')
            time_tuple = (int(year), int(month), int(day), 0, 0, 0, 0, 0, 0)
            eventday = time.mktime(time_tuple)
            notifyday = eventday - (interval*86400)

        return (date,
                self.entrytype.get_text(),
                self.entrydescription.get_text(),
                self._textbuffer.get_text(*self._textbuffer.get_bounds()),
                int(notify),
                interval,
                notifyday,
                )

    def _get_event_key(self):
        model, rowiter = self._selection.get_selected()
        return model[rowiter][0]

    def _empty_entries(self):
        for entry in self._entries:
            entry.set_text('')

        self.labelnotification.set_text("")
        self.labelnotify.set_text("-1")

