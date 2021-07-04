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
import logging
from typing import Optional

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui import filechooser
from pigeonplanner.ui import exceptiondialog
from pigeonplanner.ui.maildialog import MailDialog
from pigeonplanner.ui.messagedialog import (InfoDialog, QuestionDialog,
                                            ErrorDialog, WarningDialog)
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.database import session
from pigeonplanner.database.main import DatabaseVersionError, DatabaseMigrationError
from pigeonplanner.database.models import Pigeon, Racepoint
from pigeonplanner.database.manager import (dbmanager, DatabaseInfo,
                                            DatabaseOperationError, DatabaseInfoError)


logger = logging.getLogger(__name__)


class DBFileChooserDialog(filechooser._FileChooserDialog):  # noqa
    def __init__(self, parent: Gtk.Window):
        super(DBFileChooserDialog, self).__init__(parent, preview=False)
        self.set_title(_("Select a database file..."))
        self.add_button(_("OK"), Gtk.ResponseType.OK)
        self.set_extra_widget(self._create_extra_widget())
        self.add_custom_filter(_("Pigeon Planner database"), "pigeonplanner*.db")

    def _create_extra_widget(self) -> Gtk.Table:
        label_title = Gtk.Label()
        label_template = "%s <span style='italic' size='smaller' foreground='#787878'>(%s)</span>"
        label_title.set_markup(label_template % (_("Name"), _("Required")))
        label_title.set_alignment(0, .5)
        self.entry_name = Gtk.Entry()
        self.entry_name.set_width_chars(40)

        label_desc = Gtk.Label(_("Description"))
        label_desc.set_alignment(0, .5)
        self.entry_description = Gtk.Entry()

        table = Gtk.Table(2, 2, False)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        table.attach(label_title, 0, 1, 0, 1, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entry_name, 1, 2, 0, 1)
        table.attach(label_desc, 0, 1, 1, 2, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entry_description, 1, 2, 1, 2)
        table.show_all()
        return table

    def get_db_name(self) -> str:
        return self.entry_name.get_text()

    def get_db_description(self) -> str:
        return self.entry_description.get_text()


class DBManagerWindow(builder.GtkBuilder, GObject.GObject, component.Component):
    __gsignals__ = {
        "database-loaded": (GObject.SIGNAL_RUN_LAST, None, ()),
        "database-closed": (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    MODE_NEW = 0
    MODE_EDIT = 1

    def __init__(self, parent: Gtk.Window = None):
        builder.GtkBuilder.__init__(self, "DBManager.ui", ["dialog", "image_up", "image_down"])
        GObject.GObject.__init__(self)
        component.Component.__init__(self, "DBManager")

        self._new_edit_mode = None
        self._dbobj_during_edit = None
        self._dbobj_during_repair = None
        self._repair_checkers = [
            PigeonEmptyYearChecker(),
            RacepointUnitChecker(),
        ]

        dbmanager.prompt_do_upgrade = self._prompt_do_upgrade
        dbmanager.upgrade_finished = self._upgrade_finished

        db_dialog = filechooser.DatabasePathChooserDialog(self.widgets.dialog)
        self.widgets.pathchooser = pc = filechooser.PathChooser(dialog=db_dialog)
        self.widgets.pathchooser.set_hexpand(True)
        self.widgets.pathchooser.show()
        self.widgets.gridadvanced.attach(pc, 1, 0, 1, 1)

        label_template = "%s <span style='italic' size='smaller' foreground='#787878'>(%s)</span>"
        self.widgets.label_name_new.set_markup(label_template % (_("Name"), _("Required")))

        self.widgets.listbox.set_header_func(self._listbox_header_func)
        self.widgets.listbox_repair.set_header_func(self._listbox_header_func)

        self.widgets.dialog.set_transient_for(parent)

    def on_dialog_delete_event(self, _widget, _event):
        self._close_dialog()
        return True

    def on_button_close_clicked(self, _widget):
        self._close_dialog()

    def on_button_quit_clicked(self, _widget):
        self._save_list_order()
        component.get("MainWindow").quit_program(bckp=False)

    # noinspection PyMethodMayBeStatic
    def on_button_help_clicked(self, _widget):
        common.open_help(19)

    def on_listbox_row_activated(self, _widget, row: Gtk.ListBoxRow):
        if not row.is_opened and row.dbobj.exists and row.dbobj.writable:
            self.open_database(row.dbobj)

    def on_listbox_selected_rows_changed(self, listbox: Gtk.ListBox):
        num_rows = len(listbox.get_children())
        row = listbox.get_selected_row()
        if num_rows == 0 or row is None:
            up_sensitive = False
            down_sensitive = False
        elif row.get_index() == 0:
            up_sensitive = False
            down_sensitive = True
        elif row.get_index() == num_rows - 1:
            up_sensitive = True
            down_sensitive = False
        else:
            up_sensitive = True
            down_sensitive = True

        self.widgets.button_up.set_sensitive(up_sensitive)
        self.widgets.button_down.set_sensitive(down_sensitive)

    def on_listbox_add(self, _listbox, _row):
        self._set_db_info_revealer()

    def on_listbox_remove(self, _listbox, _row):
        self._set_db_info_revealer()

    def on_button_up_clicked(self, _widget):
        self._move_selected_row(-1)

    def on_button_down_clicked(self, _widget):
        self._move_selected_row(1)

    @common.LogFunctionCall()
    def on_button_new_clicked(self, _widget):
        self._new_edit_mode = self.MODE_NEW
        self.widgets.frame_advanced.set_visible(True)
        self.widgets.stack.set_visible_child_name("new_edit_page")
        name, description = "", ""
        if len(dbmanager.get_databases()) == 0:
            # There's no database yet, give the user some help.
            name = dbmanager.default_name
            description = dbmanager.default_description
        self.widgets.entry_name.set_text(name)
        self.widgets.entry_name.grab_focus()
        self.widgets.entry_name.set_position(-1)
        self.widgets.entry_description.set_text(description)
        self.widgets.pathchooser.set_filename(const.PREFDIR)

    @common.LogFunctionCall()
    def on_button_add_clicked(self, _widget):
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
                    self.add_listbox_row(dbobj, select=True)
                    break
            else:
                break
        dialog.destroy()

    def on_button_cancel_clicked(self, _widget):
        self.widgets.stack.set_visible_child_name("list_page")

    @common.LogFunctionCall()
    def on_button_save_clicked(self, _widget):
        name = self.widgets.entry_name.get_text()
        description = self.widgets.entry_description.get_text()
        path = self.widgets.pathchooser.get_filename()

        if self._new_edit_mode == self.MODE_NEW:
            try:
                dbobj = dbmanager.create(name, description, path)
            except DatabaseInfoError as exc:
                ErrorDialog((exc.message, None, ""), self.widgets.dialog)
                self.widgets.entry_name.grab_focus()
            else:
                self.add_listbox_row(dbobj, select=True)
                self.widgets.stack.set_visible_child_name("list_page")
        elif self._new_edit_mode == self.MODE_EDIT:
            dbfile = os.path.basename(self._dbobj_during_edit.path)
            path = os.path.join(path, dbfile)
            try:
                dbobj = dbmanager.edit(self._dbobj_during_edit, name, description, path)
            except (DatabaseInfoError, DatabaseOperationError) as exc:
                ErrorDialog((exc.message, None, ""), self.widgets.dialog)
                self.widgets.entry_name.grab_focus()
            else:
                self.edit_listbox_row(dbobj)
                self.widgets.stack.set_visible_child_name("list_page")

    def on_button_back_clicked(self, _widget):
        self._dbobj_during_repair = None
        self.widgets.revealer_repair_error.set_reveal_child(False)
        self.widgets.stack.set_visible_child_name("list_page")

    @common.LogFunctionCall()
    def on_button_repair_selected_clicked(self, _widget):
        session.open(self._dbobj_during_repair.path)
        if session.needs_update():
            self.widgets.label_repair_error.set_text(_("Can't repair database that needs an update."))
            self.widgets.revealer_repair_error.set_reveal_child(True)
            return

        for row in self.widgets.listbox_repair.get_children():
            row.clear_result()
            if row.is_enabled:
                result = row.checker.repair()
                row.update_result(result)

        session.close()

    def on_switch_repair_active_notify(self, switch: Gtk.Switch, _gparam):
        value = switch.get_active()
        for row in self.widgets.listbox_repair.get_children():
            row.widgets.switch_check.set_active(value)

    def run(self, startup: bool = False):
        self.widgets.stack.set_visible_child_name("list_page")
        self.fill_database_listbox()
        self.fill_repair_listbox()
        self.widgets.dialog.show()
        self._set_db_info_revealer()

        # Load the default database only if this dialog is run on startup
        default_db = dbmanager.get_default()
        if startup and default_db and default_db.exists and default_db.writable:
            self.open_database(default_db)

    def fill_database_listbox(self):
        for row in self.widgets.listbox.get_children():
            self.widgets.listbox.remove(row)
        for dbobj in dbmanager.get_databases():
            self.add_listbox_row(dbobj)
        self.widgets.listbox.show_all()

    def fill_repair_listbox(self):
        for row in self.widgets.listbox_repair.get_children():
            self.widgets.listbox_repair.remove(row)
        for checker in self._repair_checkers:
            row = RepairListboxRow(checker)
            row.show_all()
            self.widgets.listbox_repair.add(row)
        self.widgets.listbox_repair.show_all()

    def add_listbox_row(self, dbobj: DatabaseInfo, select: bool = False):
        row = DatabaseListboxRow(dbobj)
        row.show_all()
        self.widgets.listbox.add(row)
        if select:
            self.widgets.listbox.select_row(row)
            # Scroll to row
            GLib.timeout_add(100, row.grab_focus)

    def edit_listbox_row(self, dbobj: DatabaseInfo):
        for row in self.widgets.listbox.get_children():
            if row.dbobj == dbobj:
                row.update_data()
                break

    def update_all_rows(self):
        for row in self.widgets.listbox.get_children():
            row.update_data()

    def open_database(self, dbobj: DatabaseInfo):
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

    def close_database(self):
        dbmanager.close_database()
        self.emit("database-closed")
        self.update_all_rows()

    def remove_database(self, dbobj: DatabaseInfo, row: Optional[Gtk.ListBoxRow] = None):
        if not WarningDialog(messages.MSG_DELETE_DATABASE, self.widgets.dialog).run():
            return

        try:
            dbmanager.delete(dbobj)
        except DatabaseOperationError as exc:
            ErrorDialog((exc.message, None, ""), self.widgets.dialog)
            return

        if row is not None:
            self.widgets.listbox.remove(row)

    def edit_database(self, dbobj: DatabaseInfo):
        self.widgets.frame_advanced.set_visible(False)
        self.widgets.stack.set_visible_child_name("new_edit_page")

        self._new_edit_mode = self.MODE_EDIT
        self._dbobj_during_edit = dbobj

        self.widgets.entry_name.set_text(dbobj.name)
        self.widgets.entry_name.grab_focus()
        self.widgets.entry_name.set_position(-1)
        self.widgets.entry_description.set_text(dbobj.description)
        self.widgets.pathchooser.set_filename(dbobj.directory)

    def move_database(self, dbobj: DatabaseInfo):
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
                    self.edit_listbox_row(dbobj)
                    break
            else:
                break

        dialog.destroy()
        self.widgets.listbox.grab_focus()

    def show_repair(self, dbobj: DatabaseInfo):
        self._dbobj_during_repair = dbobj
        self.widgets.stack.set_visible_child_name("repair_page")

    def update_repair_button(self):
        enable = any(row.is_enabled for row in self.widgets.listbox_repair.get_children())
        self.widgets.button_repair_selected.set_sensitive(enable)

    def _close_dialog(self):
        self._save_list_order()
        self.widgets.dialog.hide()

    def _save_list_order(self):
        dbs = [row.dbobj for row in self.widgets.listbox.get_children()]
        dbmanager.reorder(dbs)

    def _move_selected_row(self, step: int):
        row = self.widgets.listbox.get_selected_row()
        current_index = row.get_index()
        self.widgets.listbox.remove(row)
        self.widgets.listbox.insert(row, current_index + step)
        self.widgets.listbox.unselect_all()
        self.widgets.listbox.select_row(row)

    # noinspection PyMethodMayBeStatic
    def _listbox_header_func(self, row, before):
        if before is None:
            return
        sep = Gtk.Separator()
        sep.show()
        row.set_header(sep)

    def _set_db_info_revealer(self):
        num_rows = len(self.widgets.listbox.get_children())
        self.widgets.revealer_no_db.set_reveal_child(num_rows == 0)

    def _prompt_do_upgrade(self) -> bool:
        if not QuestionDialog(messages.MSG_UGRADE_DATABASE, self.widgets.dialog).run():
            return False
        return True

    def _upgrade_finished(self):
        InfoDialog(messages.MSG_UPDATED_DATABASE, self.widgets.dialog)


class DatabaseListboxRow(Gtk.ListBoxRow, builder.GtkBuilder):
    def __init__(self, dbobj: DatabaseInfo):
        Gtk.ListBoxRow.__init__(self)
        builder.GtkBuilder.__init__(self, "DBManager.ui", ["listboxrowcontent", "popover_actions", "popover_more"])
        self.dbobj = dbobj
        self._switch_default_notify_handler_id = \
            self.widgets.switch_default.connect("notify::active", self.on_switch_default_active_notify)
        self._dbmanager: DBManagerWindow = component.get("DBManager")
        self.add(self.widgets.listboxrowcontent)
        self.update_data()

    def update_data(self):
        self.widgets.label_name.set_markup(self._format_info())
        self.widgets.label_path.set_markup(self._format_path())
        self.widgets.label_modified.set_markup(self._format_last_modified())

        self.widgets.button_open.set_sensitive(not self.is_opened)
        self.widgets.box_actions.set_sensitive(not self.is_opened)
        self.widgets.button_close_db.set_sensitive(self.is_opened)
        if not self.dbobj.exists or not self.dbobj.writable:
            self.widgets.button_open.set_sensitive(False)
            self.widgets.button_repair.set_sensitive(False)
        if not self.dbobj.exists:
            self.widgets.button_copy.set_sensitive(False)
            self.widgets.button_move.set_sensitive(False)
            self.widgets.button_send.set_sensitive(False)

        with self.widgets.switch_default.handler_block(self._switch_default_notify_handler_id):
            self.widgets.switch_default.set_active(self.dbobj.default)

    @property
    def is_opened(self) -> bool:
        return self.dbobj.path == session.dbfile

    def _format_info(self) -> str:
        s = "<b>%s</b>" % common.escape_text(self.dbobj.name)
        if self.dbobj.default:
            s += " <span style='italic' size='smaller' weight='bold'>(%s)</span>" % _("Default")
        if self.is_opened:
            s += " <span style='italic' size='smaller' foreground='#00C411'>(%s)</span>" % _("Opened")
        if not self.dbobj.exists:
            s += " <span style='italic' size='smaller' foreground='#C40B00'>(%s)</span>" % _("Not found")
        elif not self.dbobj.writable:
            s += " <span style='italic' size='smaller' foreground='#C40B00'>(%s)</span>" % _("Not writable")
        if self.dbobj.description:
            s += " - %s" % common.escape_text(self.dbobj.description)
        return s

    def _format_path(self) -> str:
        return "<span style='italic'>%s</span>" % common.escape_text(self.dbobj.path)

    def _format_last_modified(self) -> str:
        return "<span foreground='#787878'>%s</span> %s" % (_("Last modified:"), self.dbobj.last_access)

    @common.LogFunctionCall()
    def on_button_open_clicked(self, _widget):
        self._dbmanager.open_database(self.dbobj)

    @common.LogFunctionCall()
    def on_button_edit_clicked(self, _widget):
        self.widgets.popover_actions.popdown()
        self._dbmanager.edit_database(self.dbobj)

    @common.LogFunctionCall()
    def on_button_remove_clicked(self, _widget):
        self.widgets.popover_actions.popdown()
        self._dbmanager.remove_database(self.dbobj, self)

    @common.LogFunctionCall()
    def on_button_copy_clicked(self, _widget):
        self.widgets.popover_actions.popdown()
        new_dbobj = dbmanager.copy(self.dbobj)
        self._dbmanager.add_listbox_row(new_dbobj, select=True)

    @common.LogFunctionCall()
    def on_button_move_clicked(self, _widget):
        self.widgets.popover_actions.popdown()
        self._dbmanager.move_database(self.dbobj)

    @common.LogFunctionCall()
    def on_button_repair_clicked(self, _widget):
        self._dbmanager.show_repair(self.dbobj)

    @common.LogFunctionCall()
    def on_button_close_db_clicked(self, _widget):
        self.widgets.popover_actions.popdown()
        self._dbmanager.close_database()

    def on_switch_default_active_notify(self, switch: Gtk.Switch, _gparam):
        value = switch.get_active()
        dbmanager.set_default(self.dbobj, value)
        self._dbmanager.update_all_rows()

    @common.LogFunctionCall()
    def on_button_send_clicked(self, _widget):
        self.widgets.popover_more.popdown()
        MailDialog(self._dbmanager.widgets.dialog, self.dbobj.path, kind="database")

    @common.LogFunctionCall()
    def on_button_open_folder_clicked(self, _widget):
        self.widgets.popover_more.popdown()
        common.open_folder(self.dbobj.directory)


class RepairListboxRow(Gtk.ListBoxRow, builder.GtkBuilder):
    def __init__(self, checker):
        Gtk.ListBoxRow.__init__(self)
        builder.GtkBuilder.__init__(self, "DBManager.ui", ["listboxrowrepaircontent"])
        self.checker = checker
        self._dbmanager: DBManagerWindow = component.get("DBManager")
        self.widgets.label_checker_description.set_text(checker.description)
        self.widgets.label_checker_action.set_text(checker.action)
        self.clear_result()
        self.add(self.widgets.listboxrowrepaircontent)

    @property
    def is_enabled(self) -> bool:
        return self.widgets.switch_check.get_active()

    def on_switch_check_active_notify(self, _widget, _gparam):
        self._dbmanager.update_repair_button()

    def clear_result(self):
        text = "<span style='italic' foreground='#787878'>%s</span>" % _("Waiting for action...")
        self.widgets.label_checker_result.set_markup(text)

    def update_result(self, result: str):
        self.widgets.label_checker_result.set_text(result)


class PigeonEmptyYearChecker:
    def __init__(self):
        self.description = _("Check for pigeons with an empty value as year.")
        self.action = _("Delete pigeon.")

    def repair(self) -> str:  # noqa
        query = Pigeon.delete().where(Pigeon.band_year == "")
        num_repaired = query.execute()
        logger.debug("Database check: PigeonEmptyYearChecker deleted %s row(s)", num_repaired)
        return _("Deleted %s object(s)") % num_repaired


class RacepointUnitChecker:
    def __init__(self):
        self.description = _("Check for racepoints with an invalid unit value.")
        self.action = _("Reset unit value to the default.")

    def repair(self) -> str:  # noqa
        query = Racepoint.update(unit=0).where(Racepoint.unit.cast("text") == "")
        num_repaired = query.execute()
        logger.debug("Database check: RacepointUnitChecker updated %s row(s)", num_repaired)
        return _("Updated %s object(s)") % num_repaired
