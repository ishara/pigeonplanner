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

import gtk
import gobject

from pigeonplanner import messages
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.messagedialog import (InfoDialog, QuestionDialog,
                                            ErrorDialog, WarningDialog)
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
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.set_extra_widget(self._create_extra_widget())
        self.add_custom_filter((_("Pigeon Planner database"), "pigeonplanner*.db"))

    def _create_extra_widget(self):
        labeltitle = gtk.Label(_("Name"))
        labeltitle.set_alignment(0, .5)
        self.entryname = gtk.Entry()

        labeldesc = gtk.Label(_("Description"))
        labeldesc.set_alignment(0, .5)
        self.entrydescription = gtk.Entry()

        table = gtk.Table(2, 2, False)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        table.attach(labeltitle, 0, 1, 0, 1, gtk.FILL, 0)
        table.attach(self.entryname, 1, 2, 0, 1)
        table.attach(labeldesc, 0, 1, 1, 2, gtk.FILL, 0)
        table.attach(self.entrydescription, 1, 2, 1, 2)
        table.show_all()
        return table

    def get_db_name(self):
        return self.entryname.get_text()

    def get_db_description(self):
        return self.entrydescription.get_text()


class DBManagerWindow(builder.GtkBuilder, gobject.GObject, component.Component):
    __gsignals__ = {"database-loaded": (gobject.SIGNAL_RUN_LAST, None, ())}

    (COL_OBJ,
     COL_ICON,
     COL_INFO,
     COL_MODIFIED) = range(4)

    RESPONSE_OK = 2

    def __init__(self, parent=None):
        builder.GtkBuilder.__init__(self, "DBManager.ui")
        gobject.GObject.__init__(self)
        component.Component.__init__(self, "DBManager")

        dbmanager.prompt_do_upgrade = self._prompt_do_upgrade
        dbmanager.upgrade_finished = self._upgrade_finished

        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)

        self.widgets.pathchooser = pc = filechooser.PathChooser()
        self.widgets.pathchooser.show()
        self.widgets.tableadvanced.attach(pc, 1, 2, 0, 1)

        self.widgets.dialog.set_transient_for(parent)

    ## Callbacks ##
    def on_dialog_delete_event(self, widget, event):
        self._close_dialog()
        return True

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        sensitive = rowiter is not None
        self.widgets.edit.set_sensitive(sensitive)
        self.widgets.remove.set_sensitive(sensitive)
        self.widgets.open.set_sensitive(sensitive)
        self.widgets.default.set_sensitive(sensitive)

        if rowiter is not None:
            dbobj = model.get_value(rowiter, self.COL_OBJ)
            self.widgets.default.set_active(dbobj.default)
            self.widgets.open.set_sensitive(dbobj.exists)
            self.widgets.open.set_sensitive(dbobj.writable)

    def on_treeview_button_press_event(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return

        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_edit_clicked, None, None),
                (gtk.STOCK_REMOVE, self.on_remove_clicked, None, None)]
            utils.popup_menu(event, entries)

    def on_treeview_row_activated(self, widget, path, view_column):
        if self.widgets.open.get_sensitive():
            # This avoids opening a non-existing database
            self.on_open_clicked(None)

    def on_close_clicked(self, widget):
        self._close_dialog()

    def on_quit_clicked(self, widget):
        self._save_list_order()
        component.get("MainWindow").quit_program(bckp=False)

    def on_help_clicked(self, widget):
        common.open_help(19)

    def on_open_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)

        try:
            dbmanager.open(dbobj)
        except DatabaseVersionError:
            ErrorDialog(messages.MSG_NEW_DATABASE, self.widgets.dialog)
            return
        except DatabaseMigrationError:
            ErrorDialog(messages.MSG_ERROR_DATABASE)
            return
        except DatabaseInfoError:
            return

        self.emit("database-loaded")
        self._close_dialog()

    def on_add_clicked(self, widgets):
        dialog = DBFileChooserDialog(self.widgets.dialog)
        while True:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                name = dialog.get_db_name()
                description = dialog.get_db_description()
                path = dialog.get_filename()

                try:
                    dbobj = dbmanager.add(name, description, path)
                except DatabaseInfoError as exc:
                    ErrorDialog((exc.msg, None, ""), dialog)
                else:
                    self.add_liststore_item(dbobj, select=True)
                    break
            else:
                break
        dialog.destroy()

    def on_new_clicked(self, widgets):
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
                    ErrorDialog((exc.msg, None, ""), self.widgets.editdialog)
                else:
                    self.add_liststore_item(dbobj, select=True)
                    break
            else:
                break
        self.widgets.editdialog.hide()

    def on_edit_clicked(self, widget):
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
                    ErrorDialog((exc.msg, None, ""), self.widgets.editdialog)
                else:
                    self.edit_liststore_item(rowiter, dbobj)
                    break
            else:
                break
        self.widgets.editdialog.hide()

    def on_remove_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        if not WarningDialog(messages.MSG_DELETE_DATABASE, self.widgets.dialog).run():
            return

        try:
            dbmanager.delete(dbobj)
        except DatabaseOperationError as exc:
            ErrorDialog((exc.msg, None, ""), self.widgets.dialog)
            return

        model.remove(rowiter)

    def on_default_toggled(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        dbobj = model.get_value(rowiter, self.COL_OBJ)
        value = widget.get_active()
        dbmanager.set_default(dbobj, value)

    ## Public methods ##
    def run(self, startup=False):
        self.fill_treeview()
        #TODO: allow dbmanager to close even without database. Needs major
        #      changes to prevent any database interaction.
        self.widgets.dialog.set_deletable(session.is_open())
        self.widgets.close.set_sensitive(session.is_open())
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
            self.widgets.selection.select_iter(rowiter)

    def edit_liststore_item(self, rowiter, dbobj):
        icon, info, modified = self._dbobj_liststore_info(dbobj)
        self.widgets.liststore.set(rowiter, self.COL_OBJ, dbobj, self.COL_ICON, icon,
                                            self.COL_INFO, info, self.COL_MODIFIED, modified)

    ## Private methods ##
    def _close_dialog(self):
        if session.is_open():
            self._save_list_order()
            self.widgets.dialog.hide()
        else:
            # Disable closing the dialog when no database is open. Pigeon Planner
            # was never built with the intention of multiple database, so this
            # database manager is built on top of the main application which has
            # some drawbacks. Unable to use Pigeon Planner without database being
            # one of them. This might (or better yet, should) change in the future.
            ErrorDialog((_("It's not allowed to close the database manager when no database is opened."), "", ""),
                        self.widgets.dialog)

    def _save_list_order(self):
        dbs = [row[self.COL_OBJ] for row in self.widgets.liststore]
        dbmanager.reorder(dbs)

    def _format_info(self, name, description, path):
        head = "%s" % name
        if description:
            head += " - <small>%s</small>" % description
        second = "<span style='italic' size='smaller' foreground='#B5B1B1'>%s</span>" % path

        return "%s\n%s" % (head, second)

    def _dbobj_liststore_info(self, dbobj):
        icon = None
        if not dbobj.exists or not dbobj.writable:
            icon = gtk.STOCK_DIALOG_ERROR
        elif dbobj.path == session.dbfile:
            icon = gtk.STOCK_YES

        info = self._format_info(dbobj.name, dbobj.description, dbobj.path)
        modified = "%s\n%s" % tuple(dbobj.last_access.split())

        return icon, info, modified

    def _prompt_do_upgrade(self):
        if not QuestionDialog(messages.MSG_UGRADE_DATABASE, self.widgets.dialog).run():
            return False
        return True

    def _upgrade_finished(self):
        InfoDialog(messages.MSG_UPDATED_DATABASE, self.widgets.dialog)
