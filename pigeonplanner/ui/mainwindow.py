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

"""
Main window class
"""


import os
import os.path
import time
import string
import webbrowser
import logging

import gi
from gi.repository import Gtk
from gi.repository import Gdk

from pigeonplanner import messages
from pigeonplanner.ui import tabs
from pigeonplanner.ui import tools
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import dbmanager
from pigeonplanner.ui import logdialog
from pigeonplanner.ui import component
from pigeonplanner.ui import detailsview
from pigeonplanner.ui import exportwindow
from pigeonplanner.ui import backupdialog
from pigeonplanner.ui import updatedialog
from pigeonplanner.ui import optionsdialog
from pigeonplanner.ui import pedigreewindow
from pigeonplanner.ui.widgets import treeview
from pigeonplanner.ui.messagedialog import ErrorDialog, InfoDialog
from pigeonplanner.ui.pedigreeprintsetup import setupwindow
from pigeonplanner.core import enums
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import backup
from pigeonplanner.core import config
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.database import session
from pigeonplanner.database.models import Pigeon
from pigeonplanner.reportlib import report
from pigeonplanner.reports.pigeons import PigeonsReport, PigeonsReportOptions

logger = logging.getLogger(__name__)

try:
    gi.require_version("GtkosxApplication", "1.0")
    from gi.repository import GtkosxApplication

    macapp = GtkosxApplication.Application()
except (ValueError, ImportError):
    GtkosxApplication = None
    macapp = None
    if const.OSX:
        logger.error("Unable to import GtkosxApplication")


class MainWindow(Gtk.ApplicationWindow, builder.GtkBuilder, component.Component):
    ui = """
<ui>
   <menubar name="MenuBar">
      <menu action="FileMenu">
         <menuitem action="Add"/>
         <menuitem action="Addrange"/>
         <separator/>
         <menuitem action="DBMan"/>
         <menuitem action="Log"/>
         <separator/>
         <menuitem action="Export"/>
         <menu action="PrintMenu">
            <menuitem action="PrintPigeons"/>
            <menuitem action="PrintPedigree"/>
            <menuitem action="PrintBlank"/>
         </menu>
         <separator/>
         <menuitem action="Backup"/>
         <separator/>
         <menuitem action="Quit"/>
      </menu>
      <menu action="EditMenu">
         <menuitem action="Search"/>
         <menuitem action="SelectAll"/>
         <separator/>
         <menuitem action="Preferences"/>
      </menu>
      <menu action="ViewMenu">
         <menuitem action="Filter"/>
         <menuitem action="ShowAll"/>
         <separator/>
         <menuitem action="Arrows"/>
         <menuitem action="Stats"/>
         <menuitem action="Toolbar"/>
         <menuitem action="Statusbar"/>
      </menu>
      <menu action="PigeonMenu">
         <menuitem action="Edit"/>
         <menuitem action="Remove"/>
         <menuitem action="Pedigree"/>
         <menuitem action="PrintPedigreeAlt"/>
         <menuitem action="Addresult"/>
      </menu>
      <menu action="ToolsMenu">
         <menuitem action="Velocity"/>
         <menuitem action="Racepointsmap"/>
         <menuitem action="Album"/>
         <menuitem action="Addresses"/>
         <menuitem action="Data"/>
      </menu>
      <menu action="HelpMenu">
         <menuitem action="Help"/>
         <menuitem action="Home"/>
         <menuitem action="Forum"/>
         <separator/>
         <menuitem action="Update"/>
         <separator/>
         <menuitem action="Info"/>
         <separator/>
         <menuitem action="About"/>
      </menu>
   </menubar>

   <toolbar name="Toolbar">
      <toolitem action="Add"/>
      <separator/>
      <toolitem action="Edit"/>
      <toolitem action="Remove"/>
      <toolitem action="Pedigree"/>
      <separator/>
      <toolitem action="Search"/>
      <toolitem action="Filter"/>
      <separator/>
      <toolitem action="Preferences"/>
      <toolitem action="About"/>
      <toolitem action="Quit"/>
   </toolbar>
   <popup name="PopupMenu">
      <menuitem action="Edit"/>
      <menuitem action="Remove"/>
      <menuitem action="Pedigree"/>
      <menuitem action="PrintPedigreeAlt"/>
      <menuitem action="RestoreHidden"/>
   </popup>
</ui>
"""

    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(self, application=application)
        builder.GtkBuilder.__init__(self, "MainWindow.ui")
        component.Component.__init__(self, "MainWindow")

        self.widgets.treeview = treeview.MainTreeView()
        self.widgets.treeview.connect("pigeons-changed", self.on_treeview_pigeons_changed)
        self.widgets.treeview.connect("key-press-event", self.on_treeview_key_press)
        self.widgets.treeview.connect("button-release-event", self.on_treeview_release_event)
        self.widgets.treeview.set_search_entry(self.widgets.pigeon_search_entry)
        self.widgets.scrolledwindow.add(self.widgets.treeview)
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)

        self.detailsview = detailsview.DetailsView(self, True)
        self.widgets.aligndetails.add(self.detailsview.get_root_widget())

        pedigreetab = tabs.PedigreeTab()
        relativestab = tabs.RelativesTab()
        self.resultstab = tabs.ResultsTab()
        breedingtab = tabs.BreedingTab()
        mediatab = tabs.MediaTab()
        medicationtab = tabs.MedicationTab()
        self._loaded_tabs = [pedigreetab, relativestab, self.resultstab, breedingtab, mediatab, medicationtab]
        for tab in self._loaded_tabs:
            self.widgets.notebook.append_page(*tab.get_tab_widgets())
        self.widgets.notebook.set_current_page(application.cmdline_args.tab)

        self._build_menubar()
        self.current_pigeon = 0
        self.widgets.rangedialog.set_transient_for(self)

        self.widgets.MenuShowAll.set_active(config.get("interface.show-all-pigeons"))
        self.widgets.MenuArrows.set_active(config.get("interface.arrows"))
        self.widgets.MenuStats.set_active(config.get("interface.stats"))
        self.widgets.MenuToolbar.set_active(config.get("interface.toolbar"))
        self.widgets.MenuStatusbar.set_active(config.get("interface.statusbar"))

        self.connect("delete-event", self.quit_program)
        self.set_title(const.NAME)
        self.add(self.widgets.mainvbox)
        self.resize(config.get("interface.window-w"), config.get("interface.window-h"))
        self.move(config.get("interface.window-x"), config.get("interface.window-y"))
        self.show()

        infobar_label = Gtk.Label(label=_("Open a database to use the application."))
        self.widgets.database_infobar = Gtk.InfoBar()
        self.widgets.database_infobar.get_content_area().add(infobar_label)
        self.widgets.database_infobar.add_button(_("Database manager"), Gtk.ResponseType.APPLY)
        self.widgets.database_infobar.connect("response", lambda *args: self.widgets.DBMan.activate())
        self.widgets.database_infobar.show_all()
        self.widgets.mainvbox.pack_start(self.widgets.database_infobar, False, False, 0)

        self._dbman = dbmanager.DBManagerWindow(parent=self)
        self._dbman.connect("database-loaded", self.on_database_loaded)
        self._dbman.connect("database-closed", self.on_database_closed)
        self._dbman.run(True)

        if macapp is not None:

            def macapp_quit(*_args):
                self.quit_program(bckp=False)
                return False

            macapp.connect("NSApplicationBlockTermination", macapp_quit)
            macapp.ready()

    def quit_program(self, _widget=None, _event=None, bckp=True):
        if session.is_open():
            try:
                session.optimize_database()
            except Exception as exc:
                logger.error("Database optimizing failed: %s", exc)
            session.close()

        x, y = self.get_position()
        w, h = self.get_size()
        config.set("interface.window-x", x)
        config.set("interface.window-y", y)
        config.set("interface.window-w", w)
        config.set("interface.window-h", h)

        # NOTE: added in version 3.6.0 to see if it makes things more clear for the user.
        #       The "show all pigeons" option is meant to help with operations on hidden pigeons
        #       for a short time and then to be turned off again to only see the main list
        #       of pigeons. It can be confusing to see these pigeons if the option was toggled
        #       and then forgotten about.
        config.set("interface.show-all-pigeons", False)

        if config.get("backup.automatic-backup") and bckp:
            days_in_seconds = config.get("backup.interval") * 24 * 60 * 60
            if time.time() - config.get("backup.last") >= days_in_seconds:
                save_path = os.path.join(config.get("backup.location"), backup.create_backup_filename())
                try:
                    backup.create_backup(save_path, overwrite=True, include_config=True)
                except Exception as exc:
                    logger.error(exc)
                    msg = (_("There was an error making the backup."), str(exc), _("Failed!"))
                    InfoDialog(msg, self)
                else:
                    InfoDialog(messages.MSG_BACKUP_SUCCES, self)
                config.set("backup.last", time.time())
        config.save()
        self.get_application().quit()

    ####################
    # Callbacks
    ####################
    # Various
    # noinspection PyMethodMayBeStatic
    def on_dialog_delete(self, dialog, _event):
        dialog.hide()
        return True

    def on_database_loaded(self, _dbman):
        self.widgets.database_infobar.hide()
        self.widgets.mainvpaned.set_sensitive(True)
        self.widgets.actiongroup_database.set_sensitive(True)
        self.widgets.treeview.fill_treeview()
        self.widgets.treeview.grab_focus()

    def on_database_closed(self, _dbman):
        self.widgets.database_infobar.show()
        self.widgets.mainvpaned.set_sensitive(False)
        self.widgets.actiongroup_database.set_sensitive(False)
        self.widgets.treeview.clear_treeview()

    def on_interface_changed(self, _dialog, arrows, stats, toolbar, statusbar):
        self.widgets.MenuArrows.set_active(arrows)
        self.widgets.MenuStats.set_active(stats)
        self.widgets.MenuToolbar.set_active(toolbar)
        self.widgets.MenuStatusbar.set_active(statusbar)

        self.resultstab.reset_result_mode()

        self.widgets.treeview.set_columns()
        self.resultstab.set_columns()

    def on_edit_finished(self, _detailsview, pigeon, operation):
        if operation == enums.Action.edit:
            model, paths = self.widgets.selection.get_selected_rows()
            path = self.widgets.treeview.get_child_path(paths[0])
            self.widgets.treeview.update_pigeon(pigeon, path=path)
            self.widgets.selection.emit("changed")
        elif operation == enums.Action.add:
            if not pigeon.visible:
                return
            self.widgets.treeview.add_pigeon(pigeon)
            self.widgets.statusbar.display_message(_("Pigeon %s has been added") % pigeon.band)
        self.widgets.treeview.grab_focus()

    # Menu callbacks
    def on_uimanager_connect_proxy(self, _uimgr, action, widget):
        tooltip = action.get_property("tooltip")
        if isinstance(widget, Gtk.MenuItem) and tooltip:
            widget.connect("select", self.on_menuitem_select, tooltip)
            widget.connect("deselect", self.on_menuitem_deselect)

    def on_menuitem_select(self, _menuitem, tooltip):
        self.widgets.statusbar.push(888, tooltip)

    def on_menuitem_deselect(self, _menuitem):
        self.widgets.statusbar.pop(888)

    def menudbman_activate(self, _widget):
        self._dbman.run()

    def menuexport_activate(self, _widget):
        exportwindow.ExportWindow(self)

    @common.LogFunctionCall()
    def menuprintpigeons_activate(self, _widget):
        userinfo = common.get_own_address()
        if not tools.check_user_info(self, userinfo):
            return

        pigeons = self.widgets.treeview.get_pigeons(True, True)
        psize = common.get_pagesize_from_opts()
        reportopts = PigeonsReportOptions(psize)
        report(PigeonsReport, reportopts, pigeons, userinfo)

    @common.LogFunctionCall()
    def menuprintpedigree_activate(self, _widget):
        pigeon = self.widgets.treeview.get_selected_pigeon()
        if pigeon is None or isinstance(pigeon, list):
            return
        setupwindow.PedigreePrintSetupWindow(self, pigeon)

    @common.LogFunctionCall()
    def menuprintblank_activate(self, _widget):
        setupwindow.PedigreePrintSetupWindow(self, None)

    @common.LogFunctionCall()
    def menubackup_activate(self, _widget):
        backupdialog.BackupDialog(self)

    @common.LogFunctionCall()
    def menuclose_activate(self, _widget):
        self.quit_program()

    @common.LogFunctionCall()
    def menuselectall_activate(self, _widget):
        self.widgets.treeview.select_all_pigeons()

    @common.LogFunctionCall()
    def menualbum_activate(self, _widget):
        tools.PhotoAlbum(self)

    # noinspection PyMethodMayBeStatic
    @common.LogFunctionCall()
    def menulog_activate(self, _widget):
        logdialog.LogDialog()

    def menuadd_activate(self, _widget):
        dialog = detailsview.DetailsDialog(None, self, enums.Action.add)
        dialog.details.connect("edit-finished", self.on_edit_finished)

    @common.LogFunctionCall()
    def menuaddrange_activate(self, _widget):
        self.widgets.entryRangeFrom.set_text("")
        self.widgets.entryRangeTo.set_text("")
        self.widgets.entryRangeYear.set_text("")
        self.widgets.combosexrange.set_active(2)
        self.widgets.entryRangeFrom.grab_focus()
        self.widgets.rangedialog.show()

    def menuedit_activate(self, _widget):
        model, paths = self.widgets.selection.get_selected_rows()
        if len(paths) != 1:
            return
        pigeon = self.widgets.treeview.get_selected_pigeon()
        dialog = detailsview.DetailsDialog(pigeon, self, enums.Action.edit)
        dialog.details.connect("edit-finished", self.on_edit_finished)

    def menuremove_activate(self, _widget):
        model, paths = self.widgets.selection.get_selected_rows()

        if self.widgets.selection.count_selected_rows() == 0:
            return
        elif self.widgets.selection.count_selected_rows() == 1:
            pigeon = self.widgets.treeview.get_selected_pigeon()
            pigeons = [pigeon]
            statusbarmsg = _("Pigeon %s has been removed") % pigeon.band
        else:
            pigeons = self.widgets.treeview.get_selected_pigeon()
            statusbarmsg = _("%s pigeons have been removed") % len(pigeons)

        removedialog = dialogs.RemovePigeonDialog(self, len(pigeons) > 1)
        response = removedialog.run()
        if response == removedialog.RESPONSE_REMOVE or response == removedialog.RESPONSE_HIDE:
            if response == removedialog.RESPONSE_REMOVE:
                for pigeon in pigeons:
                    corepigeon.remove_pigeon(pigeon)
            elif response == removedialog.RESPONSE_HIDE:
                logger.debug("Remove: Hiding the pigeon(s)")
                for pigeon in pigeons:
                    pigeon.visible = False
                    pigeon.save()
                    self.widgets.treeview.update_pigeon(pigeon)

            if response == removedialog.RESPONSE_HIDE and config.get("interface.show-all-pigeons"):
                # Do not remove the pigeon(s) from the treeview when hiding and
                # hidden pigeons are shown.
                pass
            else:
                # Reverse the pathlist so we can safely remove each row without
                # having problems with invalid paths.
                paths.reverse()
                # Block the selection changed handler during deletion. In some cases
                # while removing multiple rows the tree iters would get invalid in
                # the handler. There's no need for it to be called anyway after each
                # call, once at the end is enough.
                self.widgets.selection.handler_block_by_func(self.on_selection_changed)
                for path in paths:
                    self.widgets.treeview.remove_row(path)
                self.widgets.selection.handler_unblock_by_func(self.on_selection_changed)
                self.widgets.selection.select_path(paths[-1])
                self.widgets.selection.emit("changed")
            self.widgets.statusbar.display_message(statusbarmsg)

        removedialog.hide()

    @common.LogFunctionCall()
    def menupedigree_activate(self, _widget):
        model, paths = self.widgets.selection.get_selected_rows()
        if len(paths) != 1:
            return
        pigeon = self.widgets.treeview.get_selected_pigeon()
        pedigreewindow.PedigreeWindow(self, pigeon)

    @common.LogFunctionCall()
    def menuaddresult_activate(self, _widget):
        self.widgets.notebook.set_current_page(2)
        self.resultstab.add_new_result()

    def menusearch_activate(self, _widget):
        search_mode = self.widgets.pigeon_search_bar.get_search_mode()
        self.widgets.pigeon_search_bar.set_search_mode(not search_mode)
        if not search_mode:
            self.widgets.pigeon_search_entry.grab_focus()
        else:
            self.widgets.treeview.grab_focus()

    @common.LogFunctionCall()
    def menufilter_activate(self, _widget):
        self.widgets.treeview.run_filterdialog(self)

    def menushowall_toggled(self, widget):
        config.set("interface.show-all-pigeons", widget.get_active())
        # This callback is already called on window creation, but it's
        # possible no database has been opened yet.
        if session.is_open():
            self.widgets.treeview.fill_treeview()

    @common.LogFunctionCall()
    def menupref_activate(self, _widget):
        dialog = optionsdialog.OptionsDialog(self)
        dialog.connect("interface-changed", self.on_interface_changed)

    def menuarrows_toggled(self, widget):
        value = widget.get_active()
        utils.set_multiple_visible([self.widgets.vboxButtons], value)
        config.set("interface.arrows", value)

    def menustats_toggled(self, widget):
        value = widget.get_active()
        utils.set_multiple_visible([self.widgets.alignStats], value)
        config.set("interface.stats", value)

    def menutoolbar_toggled(self, widget):
        value = widget.get_active()
        utils.set_multiple_visible([self.widgets.toolbar], value)
        config.set("interface.toolbar", value)

    def menustatusbar_toggled(self, widget):
        value = widget.get_active()
        utils.set_multiple_visible([self.widgets.statusbar], value)
        config.set("interface.statusbar", value)

    @common.LogFunctionCall()
    def menuvelocity_activate(self, _widget):
        tools.VelocityCalculator(self)

    @common.LogFunctionCall()
    def menuracepointsmap_activate(self, _widget):
        tools.RacepointsmapWindow(self)

    @common.LogFunctionCall()
    def menuaddresses_activate(self, _widget):
        tools.AddressBook(self)

    @common.LogFunctionCall()
    def menudata_activate(self, _widget):
        tools.DataManager(self)

    # noinspection PyMethodMayBeStatic
    @common.LogFunctionCall()
    def menuhelp_activate(self, _widget):
        webbrowser.open(const.DOCURLMAIN)

    # noinspection PyMethodMayBeStatic
    @common.LogFunctionCall()
    def menuhome_activate(self, _widget):
        webbrowser.open(const.WEBSITE)

    # noinspection PyMethodMayBeStatic
    @common.LogFunctionCall()
    def menuforum_activate(self, _widget):
        webbrowser.open(const.FORUMURL)

    @common.LogFunctionCall()
    def menuupdate_activate(self, _widget):
        updatedialog.UpdateDialog(self, False)

    @common.LogFunctionCall()
    def menuinfo_activate(self, _widget):
        dialogs.InformationDialog(self)

    @common.LogFunctionCall()
    def menuabout_activate(self, _widget):
        dialogs.AboutDialog(self)

    # range callbacks
    def on_rangeadd_clicked(self, _widget):
        rangefrom = self.widgets.entryRangeFrom.get_text()
        rangeto = self.widgets.entryRangeTo.get_text()
        rangeyear = self.widgets.entryRangeYear.get_text()
        rangesex = self.widgets.combosexrange.get_sex()

        if not rangefrom or not rangeto or not rangeyear:
            ErrorDialog(messages.MSG_EMPTY_FIELDS, self)
            return
        if not rangeyear.isdigit():
            ErrorDialog(messages.MSG_INVALID_NUMBER, self)
            return
        if not len(rangeyear) == 4:
            ErrorDialog(messages.MSG_INVALID_LENGTH, self)
            return
        if not rangefrom.isdigit() or not rangeto.isdigit():
            ErrorDialog(messages.MSG_INVALID_RANGE, self)
            return

        logger.debug("Adding a range of pigeons")
        value = int(rangefrom)
        while value <= int(rangeto):
            band = str(value)
            data = {
                "band_number": band,
                "band_year": rangeyear,
                "band_country": "",
                "band_letters": "",
                "sex": rangesex,
                "sire": None,
                "dam": None,
                "image": None,
            }
            logger.debug("Range: adding '%s'", (band, rangeyear))
            try:
                pigeon = corepigeon.add_pigeon(data, enums.Status.active, {})
            except (errors.PigeonAlreadyExists, errors.PigeonAlreadyExistsHidden):
                value += 1
                continue
            self.widgets.treeview.add_pigeon(pigeon)
            value += 1

        self.widgets.rangedialog.hide()

    def on_rangecancel_clicked(self, _widget):
        self.widgets.rangedialog.hide()

    # Main treeview callbacks
    def on_treeview_pigeons_changed(self, _widget):
        pigeons = self.widgets.treeview.get_pigeons(filtered=True)
        pigeon_count = common.count_active_pigeons(pigeons)
        self.widgets.labelStatTotal.set_markup("<b>%i</b>" % pigeon_count["total"])
        self.widgets.labelStatCocks.set_markup("<b>%i</b>" % pigeon_count[enums.Sex.cock])
        self.widgets.labelStatHens.set_markup("<b>%i</b>" % pigeon_count[enums.Sex.hen])
        self.widgets.labelStatYoung.set_markup("<b>%i</b>" % pigeon_count[enums.Sex.youngbird])
        self.widgets.labelStatUnknown.set_markup("<b>%i</b>" % pigeon_count[enums.Sex.unknown])
        self.widgets.statusbar.set_total(pigeon_count["total"])

    def on_treeview_release_event(self, widget, event):
        pthinfo = widget.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return

        if event.button == 3:
            selected = self.widgets.treeview.get_selected_pigeon()
            self.widgets.MenuRestoreHidden.set_visible(isinstance(selected, Pigeon) and not selected.visible)
            self.widgets.popupmenu.popup_at_pointer(event)

    def restore_pigeon(self, _widget):
        pigeon = self.widgets.treeview.get_selected_pigeon()
        pigeon.visible = True
        pigeon.save()
        self.widgets.treeview.update_pigeon(pigeon)

    def on_treeview_key_press(self, _widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == "Delete":
            self.menuremove_activate(None)
        elif keyname == "Insert":
            self.menuadd_activate(None)
        elif event.string and event.string in string.ascii_letters:
            self.widgets.pigeon_search_bar.set_search_mode(True)
            self.widgets.pigeon_search_entry.grab_focus()
            self.widgets.pigeon_search_entry.set_text(event.string)
            self.widgets.pigeon_search_entry.set_position(-1)

    def on_selection_changed(self, selection):
        n_rows_selected = selection.count_selected_rows()
        model, paths = selection.get_selected_rows()
        widgets = [self.widgets.actiongroup_pigeon, self.widgets.actiongroup_pigeon_remove]
        for tab in self._loaded_tabs:
            widgets.extend(tab.get_pigeon_state_widgets())

        if n_rows_selected == 1:
            utils.set_multiple_sensitive(widgets, True)
        elif n_rows_selected == 0:
            self._clear_pigeon_data()
            utils.set_multiple_sensitive(widgets, False)
            return
        elif n_rows_selected > 1:
            # Disable everything except the remove buttons
            self._clear_pigeon_data()
            utils.set_multiple_sensitive(widgets, False)
            self.widgets.actiongroup_pigeon_remove.set_sensitive(True)
            return
        self.current_pigeon = paths[0][0]
        pigeon = self.widgets.treeview.get_selected_pigeon()
        self.detailsview.set_details(pigeon)
        for tab in self._loaded_tabs:
            tab.set_pigeon(pigeon)

    def on_pigeon_search_entry_stop_search(self, _widget):
        self.widgets.pigeon_search_bar.set_search_mode(False)
        self.widgets.treeview.grab_focus()

    # Navigation arrows callbacks
    def on_button_top_clicked(self, _widget):
        self._set_pigeon(0)

    def on_button_up_clicked(self, _widget):
        self._set_pigeon(self.current_pigeon - 1)

    def on_button_down_clicked(self, _widget):
        self._set_pigeon(self.current_pigeon + 1)

    def on_button_bottom_clicked(self, _widget):
        self._set_pigeon(len(self.widgets.treeview.get_model()) - 1)

    ####################
    # Public methods
    ####################

    ####################
    # Internal methods
    ####################
    def _build_menubar(self):
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(self.widgets.actiongroup_main, 0)
        uimanager.insert_action_group(self.widgets.actiongroup_database, 0)
        uimanager.insert_action_group(self.widgets.actiongroup_pigeon, 0)
        uimanager.insert_action_group(self.widgets.actiongroup_pigeon_remove, 0)
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        widget_dic = {
            "menubar": uimanager.get_widget("/MenuBar"),
            "toolbar": uimanager.get_widget("/Toolbar"),
            "popupmenu": uimanager.get_widget("/PopupMenu"),
            "MenuShowAll": uimanager.get_widget("/MenuBar/ViewMenu/ShowAll"),
            "MenuArrows": uimanager.get_widget("/MenuBar/ViewMenu/Arrows"),
            "MenuStats": uimanager.get_widget("/MenuBar/ViewMenu/Stats"),
            "MenuToolbar": uimanager.get_widget("/MenuBar/ViewMenu/Toolbar"),
            "MenuStatusbar": uimanager.get_widget("/MenuBar/ViewMenu/Statusbar"),
            "MenuRestoreHidden": uimanager.get_widget("/PopupMenu/RestoreHidden"),
        }
        for name, widget in widget_dic.items():
            setattr(self.widgets, name, widget)

        self.widgets.mainvbox.pack_start(self.widgets.menubar, False, False, 0)
        self.widgets.mainvbox.pack_start(self.widgets.toolbar, False, False, 0)

        if macapp is not None:
            # We need to wait until the window holding the menu bar is fully realised before
            # passing it to the GtkosxApplication library. It'll throw errors otherwise.
            def on_window_realize(_widget):
                logger.debug("Setting up Mac menubar")
                self.widgets.menubar.hide()
                macapp.set_menu_bar(self.widgets.menubar)

                quit_item = uimanager.get_widget("/MenuBar/FileMenu/Quit")
                quit_item.hide()

                about_item = uimanager.get_widget("/MenuBar/HelpMenu/About")
                update_item = uimanager.get_widget("/MenuBar/HelpMenu/Update")
                prefs_item = uimanager.get_widget("/MenuBar/EditMenu/Preferences")
                macapp.insert_app_menu_item(about_item, 0)
                macapp.insert_app_menu_item(Gtk.SeparatorMenuItem(), 1)
                macapp.insert_app_menu_item(update_item, 2)
                macapp.insert_app_menu_item(prefs_item, 3)

            self.connect("realize", on_window_realize)

    def _clear_pigeon_data(self):
        self.detailsview.clear_details()
        for tab in self._loaded_tabs:
            tab.clear_pigeon()

    def _set_pigeon(self, pigeon_no):
        if pigeon_no < 0 or pigeon_no >= len(self.widgets.treeview.get_model()):
            return

        if self.current_pigeon != pigeon_no:
            self.widgets.selection.unselect_all()
            self.widgets.selection.select_path(pigeon_no)
            self.widgets.treeview.scroll_to_cell(pigeon_no)
