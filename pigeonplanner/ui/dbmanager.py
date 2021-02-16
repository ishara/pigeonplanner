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
from xml.sax.saxutils import escape

from gi.repository import Gtk
from gi.repository import GObject

from pigeonplanner import messages
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui import filechooser
from pigeonplanner.ui import exceptiondialog
from pigeonplanner.ui.maildialog import MailDialog
from pigeonplanner.ui.messagedialog import (InfoDialog, QuestionDialog,
                                            ErrorDialog, WarningDialog)
from pigeonplanner.ui.databaserepairdialog import DatabaseRepairDialog
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.database import session
from pigeonplanner.database.main import DatabaseVersionError, DatabaseMigrationError
from pigeonplanner.database.manager import (dbmanager,
                                            DatabaseOperationError, DatabaseInfoError)


class DBFileChooserDialog(filechooser._FileChooserDialog):
    def __init__(self, parent):
        super(DBFileChooserDialog, self).__init__(parent, preview=False)
        self.set_title(_("Select a database file..."))
        self.add_button(_("OK"), Gtk.ResponseType.OK)
        self.set_extra_widget(self._create_extra_widget())
        self.add_custom_filter(_("Pigeon Planner database"), "pigeonplanner*.db")

    def _create_extra_widget(self):
        labeltitle = Gtk.Label(_("Name"))
        labeltitle.set_alignment(0, .5)
        self.entryname = Gtk.Entry()

        labeldesc = Gtk.Label(_("Description"))
        labeldesc.set_alignment(0, .5)
        self.entrydescription = Gtk.Entry()

        table = Gtk.Table(2, 2, False)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        table.attach(labeltitle, 0, 1, 0, 1, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entryname, 1, 2, 0, 1)
        table.attach(labeldesc, 0, 1, 1, 2, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entrydescription, 1, 2, 1, 2)
        table.show_all()
        return table

    def get_db_name(self):
        return self.entryname.get_text()

    def get_db_description(self):
        return self.entrydescription.get_text()


class DBManagerWindow(builder.GtkBuilder, GObject.GObject, component.Component):
    __gsignals__ = {"database-loaded": (GObject.SIGNAL_RUN_LAST, None, ())}

    (COL_OBJ,
     COL_ICON,
     COL_INFO,
     COL_MODIFIED) = range(4)

    RESPONSE_OK = 2

    def __init__(self, parent=None):
        builder.GtkBuilder.__init__(self, "DBManager.ui")
        GObject.GObject.__init__(self)
        component.Component.__init__(self, "DBManager")

        dbmanager.prompt_do_upgrade = self._prompt_do_upgrade
        dbmanager.upgrade_finished = self._upgrade_finished

        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)

        db_dialog = filechooser.DatabasePathChooserDialog(self.widgets.dialog)
        self.widgets.pathchooser = pc = filechooser.PathChooser(dialog=db_dialog)
        self.widgets.pathchooser.set_hexpand(True)
        self.widgets.pathchooser.show()
        self.widgets.gridadvanced.attach(pc, 1, 0, 1, 1)

        self.widgets.dialog.set_transient_for(parent)

    # Callbacks
    def on_dialog_delete_event(self, _widget,
                               _event):
        self._close_dialog()
        return True

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        if rowiter is None:
            self.widgets.edit.set_sensitive(False)
            self.widgets.remove.set_sensitive(False)
            self.widgets.copy_.set_sensitive(False)
            self.widgets.move.set_sensitive(False)
            self.widgets.repair.set_sensitive(False)
            self.widgets.open.set_sensitive(False)
            self.widgets.default.set_sensitive(False)
        else:
            dbobj = model.get_value(rowiter, self.COL_OBJ)
            is_open = dbobj.path == session.dbfile
            self.widgets.edit.set_sensitive(dbobj.exists and dbobj.writable and not is_open)
            self.widgets.remove.set_sensitive(dbobj.exists and dbobj.writable and not is_open)
            self.widgets.copy_.set_sensitive(dbobj.exists and dbobj.writable and not is_open)
            self.widgets.move.set_sensitive(dbobj.exists and dbobj.writable and not is_open)
            self.widgets.repair.set_sensitive(dbobj.exists and dbobj.writable and not is_open)
            self.widgets.default.set_sensitive(dbobj.exists and dbobj.writable)
            self.widgets.default.set_active(dbobj.default)
            self.widgets.open.set_sensitive(dbobj.exists and dbobj.writable)

    def on_treeview_button_press_event(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return

        if event.button == 3:
            entries = [
                (self.on_edit_clicked, None, _("Edit")),
                (self.on_remove_clicked, None, _("Remove")),
                (self.on_send_clicked, None, _("Send to the developers"))
            ]
            utils.popup_menu(event, entries)

    def on_treeview_row_activated(self, _widget, _path, _view_column):
        if self.widgets.open.get_sensitive():
            # This avoids opening a non-existing database
            self.on_open_clicked(None)

    def on_close_clicked(self, _widget):
        self._close_dialog()

    def on_quit_clicked(self, _widget):
        self._save_list_order()
        component.get("MainWindow").quit_program(bckp=False)

    # noinspection PyMethodMayBeStatic
    def on_help_clicked(self, _widget):
        common.open_help(19)

    @common.LogFunctionCall()
    def on_open_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)

        try:
            dbmanager.open(dbobj)
        except DatabaseVersionError:
            ErrorDialog(messages.MSG_NEW_DATABASE, self.widgets.dialog)
            return
        except DatabaseMigrationError:
            exceptiondialog.ExceptionDialog(messages.MSG_ERROR_DATABASE[0])
            return
        except DatabaseInfoError:
            return

        self._close_dialog()
        self.emit("database-loaded")

    @common.LogFunctionCall()
    def on_add_clicked(self, _widgets):
        dialog = DBFileChooserDialog(self.widgets.dialog)
        while True:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                name = dialog.get_db_name()
                description = dialog.get_db_description()
                path = dialog.get_filename()

                try:
                    dbobj = dbmanager.add(name, description, path)
                except DatabaseInfoError as exc:
                    ErrorDialog((exc.message, None, ""), dialog)
                else:
                    self.add_liststore_item(dbobj, select=True)
                    break
            else:
                break
        dialog.destroy()
        self.widgets.treeview.grab_focus()

    @common.LogFunctionCall()
    def on_new_clicked(self, _widgets):
        name, description = "", ""
        if len(dbmanager.get_databases()) == 0:
            # There's no database yet, give the user some help.
            name = dbmanager.default_name
            description = dbmanager.default_description
        self.widgets.entryname.set_text(name)
        self.widgets.entryname.grab_focus()
        self.widgets.entrydescription.set_text(description)
        self.widgets.pathchooser.set_filename(const.PREFDIR)

        while True:
            response = self.widgets.editdialog.run()
            if response == self.RESPONSE_OK:
                name = self.widgets.entryname.get_text()
                description = self.widgets.entrydescription.get_text()
                path = self.widgets.pathchooser.get_filename()

                try:
                    dbobj = dbmanager.create(name, description, path)
                except DatabaseInfoError as exc:
                    ErrorDialog((exc.message, None, ""), self.widgets.editdialog)
                else:
                    self.add_liststore_item(dbobj, select=True)
                    break
            else:
                break
        self.widgets.editdialog.hide()
        self.widgets.treeview.grab_focus()

    @common.LogFunctionCall()
    def on_edit_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        dbpath = os.path.dirname(dbobj.path)
        dbfile = os.path.basename(dbobj.path)

        self.widgets.entryname.set_text(dbobj.name)
        self.widgets.entryname.grab_focus()
        self.widgets.entrydescription.set_text(dbobj.description)
        self.widgets.pathchooser.set_filename(dbpath)

        while True:
            response = self.widgets.editdialog.run()
            if response == self.RESPONSE_OK:
                name = self.widgets.entryname.get_text()
                description = self.widgets.entrydescription.get_text()
                newdbpath = self.widgets.pathchooser.get_filename()
                path = os.path.join(newdbpath, dbfile)

                try:
                    dbobj = dbmanager.edit(dbobj, name, description, path)
                except (DatabaseInfoError, DatabaseOperationError) as exc:
                    ErrorDialog((exc.message, None, ""), self.widgets.editdialog)
                else:
                    self.edit_liststore_item(rowiter, dbobj)
                    break
            else:
                break
        self.widgets.editdialog.hide()
        self.widgets.treeview.grab_focus()

    @common.LogFunctionCall()
    def on_remove_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        if not WarningDialog(messages.MSG_DELETE_DATABASE, self.widgets.dialog).run():
            return

        try:
            dbmanager.delete(dbobj)
        except DatabaseOperationError as exc:
            ErrorDialog((exc.message, None, ""), self.widgets.dialog)
            return

        model.remove(rowiter)

    @common.LogFunctionCall()
    def on_copy_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        new_dbobj = dbmanager.copy(dbobj)
        self.add_liststore_item(new_dbobj, select=True)

    @common.LogFunctionCall()
    def on_move_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        dialog = filechooser.DatabasePathChooserDialog(self.widgets.dialog)

        while True:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                try:
                    dbobj = dbmanager.move(dbobj, path)
                except DatabaseOperationError as exc:
                    ErrorDialog((exc.message, None, ""), self.widgets.dialog)
                else:
                    self.edit_liststore_item(rowiter, dbobj)
                    break
            else:
                break

        dialog.destroy()
        self.widgets.treeview.grab_focus()

    @common.LogFunctionCall()
    def on_repair_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        DatabaseRepairDialog(dbobj, self.widgets.dialog)

    @common.LogFunctionCall()
    def on_send_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        MailDialog(self.widgets.dialog, dbobj.path, kind="database")

    def on_default_toggled(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        value = widget.get_active()
        dbmanager.set_default(dbobj, value)

    # Public methods
    def run(self, startup=False):
        self.fill_treeview()
        self.widgets.dialog.show()

        # Load the default database only if this dialog is run on startup
        if startup:
            for row in self.widgets.liststore:
                dbobj = row[self.COL_OBJ]
                # Make sure the database really exists
                if dbobj.exists and dbobj.default:
                    self.widgets.selection.select_iter(row.iter)
                    self.widgets.open.clicked()
                    break

    def fill_treeview(self):
        self.widgets.liststore.clear()
        for dbobj in dbmanager.get_databases():
            self.add_liststore_item(dbobj)

    def add_liststore_item(self, dbobj, select=False):
        icon, info, modified = self._dbobj_liststore_info(dbobj)
        rowiter = self.widgets.liststore.append([dbobj, icon, info, modified])
        if select:
            path = self.widgets.liststore.get_path(rowiter)
            self.widgets.selection.select_iter(rowiter)
            self.widgets.treeview.scroll_to_cell(path)

    def edit_liststore_item(self, rowiter, dbobj):
        icon, info, modified = self._dbobj_liststore_info(dbobj)
        self.widgets.liststore.set(rowiter, self.COL_OBJ, dbobj, self.COL_ICON, icon,
                                   self.COL_INFO, info, self.COL_MODIFIED, modified)

    # Private methods
    def _close_dialog(self):
        self._save_list_order()
        self.widgets.dialog.hide()

    def _save_list_order(self):
        dbs = [row[self.COL_OBJ] for row in self.widgets.liststore]
        dbmanager.reorder(dbs)

    # noinspection PyMethodMayBeStatic
    def _format_info(self, name, description, path):
        head = "%s" % escape(name)
        if description:
            head += " - <small>%s</small>" % escape(description)
        second = "<span style='italic' size='smaller' foreground='#B5B1B1'>%s</span>" % escape(path)

        return "%s\n%s" % (head, second)

    def _dbobj_liststore_info(self, dbobj):
        icon = None
        if not dbobj.exists or not dbobj.writable:
            icon = "dialog-error"
        elif dbobj.path == session.dbfile:
            icon = "document-open"

        info = self._format_info(dbobj.name, dbobj.description, dbobj.path)
        modified = "%s\n%s" % tuple(dbobj.last_access.split())

        return icon, info, modified

    def _prompt_do_upgrade(self):
        if not QuestionDialog(messages.MSG_UGRADE_DATABASE, self.widgets.dialog).run():
            return False
        return True

    def _upgrade_finished(self):
        InfoDialog(messages.MSG_UPDATED_DATABASE, self.widgets.dialog)
