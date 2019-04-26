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

import os
import json
import logging
from xml.sax.saxutils import escape

import gtk

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.ui import filechooser
from pigeonplanner.ui import messagedialog
from pigeonplanner.core import const
from pigeonplanner.core import backup
from pigeonplanner.database import session
from pigeonplanner.database.manager import DBManager
from pigeonplanner.database.manager import DatabaseInfo

logger = logging.getLogger(__name__)


class BackupDialog(builder.GtkBuilder):
    (PAGE_MAIN,
     PAGE_CREATE,
     PAGE_RESTORE) = range(3)

    (LS_RESTORE_CHECK,
     LS_RESTORE_INFO,
     LS_RESTORE_ACTION,
     LS_RESTORE_DBOBJ) = range(4)

    (RESTORE_ACTION_ADD,
     RESTORE_ACTION_OVERWRITE,
     RESTORE_ACTION_INVALID) = range(3)

    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "BackupDialog.ui")
        self.widgets.dialog.set_transient_for(parent)

        self.widgets.button_fileselect = filechooser.FileChooser()
        self.widgets.button_fileselect.connect("file-set", self.on_button_fileselect_file_set)
        self.widgets.button_fileselect.add_backup_filter()
        self.widgets.align_fileselect.add(self.widgets.button_fileselect)

        self.widgets.selection_dbrestore = self.widgets.treeview_dbrestore.get_selection()
        self.widgets.selection_dbrestore.connect("changed", self.on_selection_dbrestore_changed)

        self.widgets.dialog.show_all()

        self.restore_op = None

    def on_dialog_delete_event(self, widget, event):
        self.widgets.dialog.destroy()
        return False

    def on_button_close_clicked(self, widget):
        self.widgets.dialog.destroy()

    def on_button_back_clicked(self, widget):
        self.widgets.button_back.hide()
        self.widgets.button_create.hide()
        self.widgets.button_restore.hide()
        self.widgets.notebook.set_current_page(self.PAGE_MAIN)

    def on_button_main_create_clicked(self, widget):
        self.widgets.liststoredbcreate.clear()
        for dbobj in backup.get_valid_databases():
            self.widgets.liststoredbcreate.append([dbobj, self._format_dbobj_liststore_create_info(dbobj)])

        self.widgets.button_back.show()
        self.widgets.button_create.show()
        self.widgets.notebook.set_current_page(self.PAGE_CREATE)

    def on_button_main_restore_clicked(self, widget):
        self.widgets.button_back.show()
        self.widgets.button_restore.show()
        self.widgets.notebook.set_current_page(self.PAGE_RESTORE)

    def on_button_create_clicked(self, widget):
        save_path = self.widgets.label_savepath.get_text()
        save_config = self.widgets.check_saveconfig.get_active()
        try:
            backup.create_backup(save_path, overwrite=True, include_config=save_config)
        except Exception as exc:
            logger.error(exc)
            msg = (_("There was an error making the backup."), str(exc), _("Failed!"))
            messagedialog.ErrorDialog(msg, self.widgets.dialog)
        else:
            messagedialog.InfoDialog(messages.MSG_BACKUP_SUCCES, self.widgets.dialog)

    def on_button_restore_clicked(self, widget):
        dbobjs = [row[self.LS_RESTORE_DBOBJ] for row in self.widgets.liststoredbrestore if row[self.LS_RESTORE_CHECK]]
        configfile = self.widgets.check_restoreconfig.get_active()
        try:
            self.restore_op.restore_backup(dbobjs, configfile)
        except Exception as exc:
            logger.error(exc)
            msg = (_("There was an error restoring the backup."), str(exc), _("Failed!"))
            messagedialog.ErrorDialog(msg, self.widgets.dialog)
        else:
            messagedialog.InfoDialog(messages.MSG_RESTORE_SUCCES, self.widgets.dialog)
            if session.is_open():
                session.close()
            gtk.main_quit()

    def on_button_saveselect_clicked(self, widget):
        filename = backup.create_backup_filename()
        chooser = filechooser.BackupSaver(self.widgets.dialog, filename)
        chooser.set_do_overwrite_confirmation(True)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            save_path = chooser.get_filename()
            if not save_path.endswith(".zip"):
                save_path = save_path + ".zip"
            self.widgets.label_savepath.set_text(save_path)
            self.widgets.button_create.set_sensitive(True)
        chooser.destroy()

    def on_button_fileselect_file_set(self, button):
        path = button.get_filename()
        self.restore_op = backup.RestoreOperation(path)
        valid = self.restore_op.is_valid_archive()
        self.widgets.button_restore.set_sensitive(valid)
        if not valid:
            msg = (_("The selected file is not a valid backup file."), None, _("Error"))
            messagedialog.ErrorDialog(msg, self.widgets.dialog)
            return

        self.widgets.check_restoreconfig.set_sensitive(self.restore_op.has_config_file())

        self.widgets.liststoredbrestore.clear()
        if self.restore_op.old_backup:
            dbobjs = [DatabaseInfo(DBManager.default_name,
                                   os.path.join(const.PREFDIR, "pigeonplanner.db"),
                                   DBManager.default_description, False)]
        else:
            dbobjs = [DatabaseInfo(**entry) for entry in json.loads(self.restore_op.database_info)]
        for dbobj in dbobjs:
            # It's possible there's a DatabaseInfo entry but no actual database file
            if dbobj.filename not in self.restore_op.namelist:
                continue
            action = self._get_restore_action(dbobj)
            info = self._format_dbobj_liststore_restore_info(dbobj, action)
            checked = action is not self.RESTORE_ACTION_INVALID
            self.widgets.liststoredbrestore.append([checked, info, action, dbobj])

        self._set_restore_button()

    def on_button_changedest_clicked(self, widget):
        image_info = gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON)
        label_info = gtk.Label()
        label_info.set_markup("%s <b>%s</b>" % (_("The default location is:"), escape(const.PREFDIR)))
        button_info = gtk.Button(_("Select"))
        button_info.connect("clicked", lambda w: dialog.set_current_folder(const.PREFDIR))
        box_info = gtk.HBox(spacing=4)
        box_info.pack_start(image_info, False, False, 0)
        box_info.pack_start(label_info, False, False, 0)
        box_info.pack_start(button_info, False, False, 0)
        box_info.show_all()
        dialog = filechooser.PathChooserDialog(self.widgets.dialog, const.PREFDIR)
        dialog.set_extra_widget(box_info)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            new_path = dialog.get_filename()
            model, rowiter = self.widgets.selection_dbrestore.get_selected()
            dbobj = model.get_value(rowiter, self.LS_RESTORE_DBOBJ)
            dbobj.path = os.path.join(new_path, dbobj.filename)
            new_action = self._get_restore_action(dbobj)
            new_info = self._format_dbobj_liststore_restore_info(dbobj, new_action)
            model.set(rowiter,
                      self.LS_RESTORE_DBOBJ, dbobj,
                      self.LS_RESTORE_INFO, new_info,
                      self.LS_RESTORE_ACTION, new_action)
            self._set_restore_button()
        dialog.destroy()

    def on_celltoggle_restore_toggled(self, cell, path):
        self.widgets.liststoredbrestore[path][self.LS_RESTORE_CHECK] = \
            not self.widgets.liststoredbrestore[path][self.LS_RESTORE_CHECK]
        self._set_restore_button()

    def on_selection_dbrestore_changed(self, selection):
        model, rowiter = selection.get_selected()
        self.widgets.button_changedest.set_sensitive(rowiter is not None)

    def _set_restore_button(self):
        for row in self.widgets.liststoredbrestore:
            if row[self.LS_RESTORE_CHECK] and row[self.LS_RESTORE_ACTION] == self.RESTORE_ACTION_INVALID:
                self.widgets.button_restore.set_sensitive(False)
                return
        self.widgets.button_restore.set_sensitive(True)

    def _get_restore_action(self, dbobj):
        if os.path.exists(dbobj.path):
            action = self.RESTORE_ACTION_OVERWRITE
        elif not os.path.exists(dbobj.directory):
            action = self.RESTORE_ACTION_INVALID
        else:
            action = self.RESTORE_ACTION_ADD
        return action

    def _format_dbobj_liststore_restore_info(self, dbobj, action):
        head = "%s" % escape(dbobj.name)
        if dbobj.description:
            head += " - <small>%s</small>" % escape(dbobj.description)
        action_data = [
            (_("Add"), "#00C411"),
            (_("Overwrite"), "#FFA100"),
            (_("Invalid path"), "#C40B00")
        ]
        action_string, colour = action_data[action]
        second_format = "<span style='italic' size='smaller' foreground='%s'>%s: %s</span>"
        second = second_format % (colour, action_string, escape(dbobj.path))

        return "%s\n%s" % (head, second)

    def _format_dbobj_liststore_create_info(self, dbobj):
        head = "%s" % escape(dbobj.name)
        if dbobj.description:
            head += " - <small>%s</small>" % escape(dbobj.description)
        second = "<span style='italic' size='smaller' foreground='#B5B1B1'>%s</span>" % escape(dbobj.path)
        return "%s\n%s" % (head, second)
