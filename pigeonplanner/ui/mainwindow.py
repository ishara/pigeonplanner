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
import webbrowser
import logging
logger = logging.getLogger(__name__)

import gtk

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import backup
from pigeonplanner import checks
from pigeonplanner import update
from pigeonplanner import builder
from pigeonplanner import printing
from pigeonplanner import messages
from pigeonplanner.ui import tabs
from pigeonplanner.ui import tools
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import pedigree
from pigeonplanner.ui import logdialog
from pigeonplanner.ui import detailsview
from pigeonplanner.ui import optionsdialog
from pigeonplanner.ui import pedigreewindow
from pigeonplanner.ui.widgets import menus
from pigeonplanner.ui.widgets import treeview
from pigeonplanner.ui.widgets import comboboxes


class MainWindow(builder.GtkBuilder):
    def __init__(self, options, database, parser):
        builder.GtkBuilder.__init__(self, const.GLADEMAIN)

        self.options = options
        self.database = database
        self.parser = parser

        self.treeview = treeview.TreeView(self.parser, self.options)
        self.treeview.connect('button-press-event', self.on_treeview_press)
        self.scrolledwindow.add(self.treeview)
        self.selection = self.treeview.get_selection()
        self.selection.connect('changed', self.on_selection_changed)

        self.pedigree = pedigree.DrawPedigree(self.database, self.parser,
                                              self.treeview)

        self.detailsview = detailsview.DetailsView(self.mainwindow,
                                                   self.database, self.parser)
        self.detailsview.connect('edit-finished', self.on_edit_finished)
        self.detailsview.connect('edit-cancelled', self.on_edit_cancelled)
        self.detailsview.set_default_image()
        self.aligndetails.add(self.detailsview.get_widget())

        self.pedigreetab = tabs.PedigreeTab(self.pedigree)
        self.notebook.append_page(*self.pedigreetab.get_tab_widgets())
        self.relativestab = tabs.RelativesTab(self.mainwindow, self.treeview,
                                              self.database, self.parser)
        self.notebook.append_page(*self.relativestab.get_tab_widgets())
        self.resultstab = tabs.ResultsTab(self.mainwindow, self.database,
                                          self.options, self.parser)
        self.notebook.append_page(*self.resultstab.get_tab_widgets())
        self.medicationtab = tabs.MedicationTab(self.mainwindow, self.database,
                                                self.parser, self)
        self.notebook.append_page(*self.medicationtab.get_tab_widgets())

        self.combosexrange = comboboxes.SexCombobox()
        self.tablerange.attach(self.combosexrange, 6, 7, 1, 2, gtk.SHRINK, gtk.FILL)

        self._build_menubar()
        self.pedigreetab.draw_pedigree()
        self.treeview.fill_treeview()
        self._set_statistics()
        self.current_pigeon = 0
        self.pigeon_no = len(self.treeview.get_model())

        self.MenuArrows.set_active(self.options.arrows)
        self.MenuStats.set_active(self.options.stats)
        self.MenuToolbar.set_active(self.options.toolbar)
        self.MenuStatusbar.set_active(self.options.statusbar)

        self.mainwindow.set_title("%s %s" %(const.NAME, const.VERSION))
        self.mainwindow.resize(self.options.window_w, self.options.window_h)
        self.mainwindow.move(self.options.window_x, self.options.window_y)
        self.mainwindow.show()
        self.treeview.grab_focus()

        events = self.database.get_notification(time.time())
        if events:
            description = events[0][2]
            if len(description) > 25:
                description = description[:24]+"..."
            d = dialogs.MessageDialog(const.QUESTION, messages.MSG_EVENT_NOTIFY,
                                      self.mainwindow, description)
            if d.yes:
                tools.Calendar(self.mainwindow, self.database, events[0][0])

    def quit_program(self, widget=None, event=None, bckp=True):
        self.database.close()

        x, y = self.mainwindow.get_position()
        w, h = self.mainwindow.get_size()
        self.options.set_option('Window', 'window_x', x)
        self.options.set_option('Window', 'window_y', y)
        self.options.set_option('Window', 'window_w', w)
        self.options.set_option('Window', 'window_h', h)

        if self.options.backup and bckp:
            daysInSeconds = self.options.interval * 24 * 60 * 60
            if time.time() - self.options.last >= daysInSeconds:
                if backup.make_backup(self.options.location):
                    dialogs.MessageDialog(const.INFO,
                                          messages.MSG_BACKUP_SUCCES,
                                          self.mainwindow)
                else:
                    dialogs.MessageDialog(const.INFO,
                                          messages.MSG_BACKUP_FAILED,
                                          self.mainwindow)
                self.options.set_option('Backup', 'last', time.time())
        gtk.main_quit()

    ####################
    # Callbacks
    ####################
    # Various
    def on_dialog_delete(self, dialog, event):
        dialog.hide()
        return True

    def on_interface_changed(self, dialog, arrows, stats, toolbar, statusbar):
        self.MenuArrows.set_active(arrows)
        self.MenuStats.set_active(stats)
        self.MenuToolbar.set_active(toolbar)
        self.MenuStatusbar.set_active(statusbar)

        self.treeview.set_columns()

    def on_edit_finished(self, detailsview, pigeon, operation):
        self._finish_edit()
        band, year = pigeon.get_band()
        if operation == const.EDIT:
            model, paths = self.selection.get_selected_rows()
            path = self.treeview.get_child_path(paths[0])
            data = (0, pigeon, 1, pigeon.get_pindex(), 2, band, 3, year,
                    4, pigeon.get_name(), 5, pigeon.get_colour(),
                    6, pigeon.get_sex_string(), 7, pigeon.get_loft(),
                    8, pigeon.get_strain())
            self.treeview.update_row(data, path=path)
            self.selection.emit('changed')
        elif operation == const.ADD:
            if not pigeon.get_visible(): return
            row = [pigeon, pigeon.get_pindex(), band, year, pigeon.get_name(),
                   pigeon.get_colour(), pigeon.get_sex_string(),
                   pigeon.get_loft(), pigeon.get_strain()]
            self.treeview.add_row(row)
            common.add_statusbar_message(self.statusbar,
                        _("Pigeon %s has been added") %pigeon.get_band_string())

    def on_edit_cancelled(self, detailsview):
        self._finish_edit(True)
        self.selection.emit('changed')

    # Menu callbacks
    def on_uimanager_connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_property('tooltip')
        if isinstance(widget, gtk.MenuItem) and tooltip:
            widget.connect('select', self.on_menuitem_select, tooltip)
            widget.connect('deselect', self.on_menuitem_deselect)

    def on_menuitem_select(self, menuitem, tooltip):
        self.statusbar.push(-1, tooltip)

    def on_menuitem_deselect(self, menuitem):
        self.statusbar.pop(-1)

    def menuprintpedigree_activate(self, widget):
        logger.debug(common.get_function_name())
        pigeon = self.treeview.get_selected_pigeon()
        if pigeon is None: return
        userinfo = common.get_own_address(self.database)
        printing.PrintPedigree(self.mainwindow, pigeon, userinfo,
                               self.options, const.PRINT, '', self.parser)

    def menuprintblank_activate(self, widget):
        logger.debug(common.get_function_name())
        userinfo = common.get_own_address(self.database)
        printing.PrintPedigree(self.mainwindow, None, userinfo,
                               self.options, const.PRINT, '', self.parser)

    def menubackup_activate(self, widget):
        logger.debug(common.get_function_name())
        dialog = dialogs.BackupDialog(self.mainwindow, const.CREATE)
        dialog.run()
        dialog.destroy()

    def menurestore_activate(self, widget):
        logger.debug(common.get_function_name())
        dialog = dialogs.BackupDialog(self.mainwindow, const.RESTORE)
        dialog.run()
        dialog.destroy()

    def menuclose_activate(self, widget):
        logger.debug(common.get_function_name())
        self.quit_program()

    def menusearch_activate(self, widget):
        logger.debug(common.get_function_name())
        self.treeview.run_searchdialog(self.mainwindow)

    def menualbum_activate(self, widget):
        logger.debug(common.get_function_name())
        tools.PhotoAlbum(self.mainwindow, self.parser, self.database)

    def menulog_activate(self, widget):
        logger.debug(common.get_function_name())
        logdialog.LogDialog(self.database)

    def menuadd_activate(self, widget):
        self._clear_pigeon_data()
        self._start_edit(const.ADD)

    def menuaddrange_activate(self, widget):
        logger.debug(common.get_function_name())
        self.entryRangeFrom.set_text('')
        self.entryRangeTo.set_text('')
        self.entryRangeYear.set_text('')
        self.combosexrange.set_active(2)
        self.entryRangeFrom.grab_focus()
        self.rangedialog.show()

    def menuedit_activate(self, widget):
        model, paths = self.selection.get_selected_rows()
        if len(paths) != 1: return
        self._start_edit(const.EDIT)

    def menuremove_activate(self, widget):
        model, paths = self.selection.get_selected_rows()

        if self.selection.count_selected_rows() == 1:
            pigeon = self.treeview.get_selected_pigeon()
            pindex = pigeon.get_pindex()
            pigeonlabel = pigeon.get_band_string()
            statusbarmsg = _("Pigeon %s has been removed") %pigeonlabel
            show_result_option = self.database.has_results(pindex)
            pigeons = [pigeon]
            logger.debug("Start removing pigeon '%s'", pindex)
        else:
            logger.debug("Start removing multiple pigeons")
            pigeons = [pobj for pobj in self.treeview.get_selected_pigeon()]
            bands = ['%s' %pigeon.get_band_string() for pigeon in
                     self.treeview.get_selected_pigeon()]
            pigeonlabel = ", ".join(bands)
            statusbarmsg = _("%s pigeons have been removed") %len(pigeons)
            show_result_option = False
            for pigeon in pigeons:
                if self.database.has_results(pigeon.get_pindex()):
                    show_result_option = True
                    break

        self.labelPigeon.set_text(pigeonlabel)
        self.chkKeep.set_active(True)
        self.chkResults.set_active(False)
        self.set_multiple_visible([self.chkResults], show_result_option)

        answer = self.removedialog.run()
        if answer == 2:
            if self.chkKeep.get_active():
                logger.debug("Remove: Hiding the pigeon(s)")
                for pigeon in pigeons:
                    self.database.update_table(self.database.PIGEONS,
                                               (0, pigeon.get_pindex()), 5, 1)
            else:
                logger.debug("Remove: Removing the pigeon(s)")
                for pigeon in pigeons:
                    pindex = pigeon.get_pindex()
                    self.database.delete_from_table(self.database.PIGEONS, pindex)
                    # Only remove status when pigeon is completely removed
                    status = pigeon.get_active()
                    if status != const.ACTIVE:
                        self.database.delete_from_table(self.statusdic[status],
                                                        pindex)
                    # Same for the picture
                    image = pigeon.get_image()
                    if image:
                        os.remove(common.get_thumb_path(image))
                    # And medication
                    self.database.delete_from_table(self.database.MED, pindex, 2)
                    self.parser.remove_pigeon(pindex)

            if not self.chkResults.get_active():
                logger.debug("Remove: Removing the results")
                for pigeon in pigeons:
                    self.database.delete_from_table(self.database.RESULTS,
                                                    pigeon.get_pindex())

            # Reverse the pathlist so we can safely remove each row without
            # having problems with invalid paths.
            paths.reverse()
            for path in paths:
                self.treeview.remove_row(path)
            self.selection.select_path(paths[-1])
            self._set_statistics()
            common.add_statusbar_message(self.statusbar, statusbarmsg)
        else:
            logger.debug("Remove operation cancelled")
        self.removedialog.hide()

    def menupedigree_activate(self, widget):
        logger.debug(common.get_function_name())
        pigeon = self.treeview.get_selected_pigeon()
        pedigreewindow.PedigreeWindow(self.mainwindow, self.database, self.options,
                                      self.parser, self.pedigree, pigeon)

    def menuaddresult_activate(self, widget):
        logger.debug(common.get_function_name())
        self.notebook.set_current_page(2)
        self.resultstab.add_new_result()

    def menufilter_activate(self, widget):
        logger.debug(common.get_function_name())
        self.treeview.run_filterdialog(self.mainwindow, self.database)

    def menupref_activate(self, widget):
        logger.debug(common.get_function_name())
        dialog = optionsdialog.OptionsDialog(self.mainwindow, self.options)
        dialog.connect('interface-changed', self.on_interface_changed)

    def menuarrows_toggled(self, widget):
        value = widget.get_active()
        self.set_multiple_visible([self.vboxButtons], value)
        self.options.set_option('Options', 'arrows', str(value))

    def menustats_toggled(self, widget):
        value = widget.get_active()
        self.set_multiple_visible([self.alignStats], value)
        self.options.set_option('Options', 'stats', str(value))

    def menutoolbar_toggled(self, widget):
        value = widget.get_active()
        self.set_multiple_visible([self.toolbar], value)
        self.options.set_option('Options', 'toolbar', str(value))

    def menustatusbar_toggled(self, widget):
        value = widget.get_active()
        self.set_multiple_visible([self.statusbar], value)
        self.options.set_option('Options', 'statusbar', str(value))

    def menuvelocity_activate(self, widget):
        logger.debug(common.get_function_name())
        tools.VelocityCalculator(self.mainwindow, self.database, self.options)

    def menuaddresses_activate(self, widget):
        logger.debug(common.get_function_name())
        tools.AddressBook(self.mainwindow, self.database)

    def menucalendar_activate(self, widget):
        logger.debug(common.get_function_name())
        tools.Calendar(self.mainwindow, self.database)

    def menudata_activate(self, widget):
        logger.debug(common.get_function_name())
        tools.DataManager(self.mainwindow, self.database)

    def menuhome_activate(self, widget):
        logger.debug(common.get_function_name())
        webbrowser.open(const.WEBSITE)

    def menuforum_activate(self, widget):
        logger.debug(common.get_function_name())
        webbrowser.open(const.FORUMURL)

    def menuupdate_activate(self, widget):
        logger.debug(common.get_function_name())
        try:
            new, msg = update.update()
        except update.UpdateError, exc:
            new = False
            msg = str(exc)

        title = _("Search for updates...")
        if new:
            d = dialogs.MessageDialog(const.QUESTION,
                                      (msg, _("Go to the website?"), title),
                                      self.mainwindow)
            if d.yes:
                webbrowser.open(const.DOWNLOADURL)
        else:
            dialogs.MessageDialog(const.INFO, (msg, None, title),
                                  self.mainwindow)

    def menuinfo_activate(self, widget):
        logger.debug(common.get_function_name())
        dialogs.InfoDialog(self.mainwindow, self.database)

    def menuabout_activate(self, widget):
        logger.debug(common.get_function_name())
        dialogs.AboutDialog(self.mainwindow)

    # range callbacks
    def on_rangeadd_clicked(self, widget):
        rangefrom = self.entryRangeFrom.get_text()
        rangeto = self.entryRangeTo.get_text()
        rangeyear = self.entryRangeYear.get_text()
        rangesex = self.combosexrange.get_active_text()

        try:
            checks.check_ring_entry(rangefrom, rangeyear)
            checks.check_ring_entry(rangeto, rangeyear)
        except checks.InvalidInputError, msg:
            dialogs.MessageDialog(const.ERROR, msg.value, self.mainwindow)
            return
        if not rangefrom.isdigit() or not rangeto.isdigit():
            dialogs.MessageDialog(const.ERROR, messages.MSG_INVALID_RANGE,
                                  self.mainwindow)
            return

        logger.debug("Adding a range of pigeons")
        value = int(rangefrom)
        while value <= int(rangeto):
            band = str(value)
            pindex = common.get_pindex_from_band(band, rangeyear)
            logger.debug("Range: adding '%s'", pindex)
            if self.database.has_pigeon(pindex):
                d = dialogs.MessageDialog(const.WARNING,
                                          messages.MSG_OVERWRITE_PIGEON,
                                          self.mainwindow)
                if not d.yes:
                    continue
            data = [pindex, band, rangeyear, rangesex, 1, 1, '', '', '', '',
                    '', '', '', '', '', '', '', '', '', '', '']
            rowid = self.database.insert_into_table(self.database.PIGEONS, data)
            data.insert(0, rowid)
            pigeon = self.parser.add_pigeon(data)
            row = [pigeon, pindex, band, rangeyear, '', '',
                   pigeon.get_sex_string(), '', '']
            self.treeview.add_row(row)
            value += 1

        self._set_statistics()
        self.rangedialog.hide()

    def on_rangecancel_clicked(self, widget):
        self.rangedialog.hide()

    # Main treeview callbacks
    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return

        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.menuedit_activate, None),
                (gtk.STOCK_REMOVE, self.menuremove_activate, None),
                ("pedigree-detail", self.menupedigree_activate, None)]
            menus.popup_menu(event, entries)

    def on_selection_changed(self, selection):
        n_rows_selected = selection.count_selected_rows()
        model, paths = selection.get_selected_rows()
        widgets = [self.ToolEdit, self.ToolPedigree, self.MenuEdit,
                   self.MenuPedigree, self.MenuAddresult,
                   self.resultstab.buttonadd, self.medicationtab.buttonadd,
                   self.ToolRemove, self.MenuRemove]
        if n_rows_selected == 1:
            tree_iter = model.get_iter(paths[0])
            self.set_multiple_sensitive(widgets, True)
        elif n_rows_selected == 0:
            self._clear_pigeon_data()
            self.set_multiple_sensitive(widgets, False)
            return
        elif n_rows_selected > 1:
            # Disable everything except the remove buttons
            self._clear_pigeon_data()
            self.set_multiple_sensitive(widgets[:-2], False)
            return
        self.current_pigeon = paths[0][0]
        pigeon = model.get_value(tree_iter, 0)
        self.pedigreetab.draw_pedigree(pigeon)
        self.relativestab.fill_treeviews(pigeon)
        self.resultstab.fill_treeview(pigeon)
        self.medicationtab.fill_treeview(pigeon)
        self.detailsview.set_details(pigeon)

    # Navigation arrows callbacks
    def on_button_top_clicked(self, widget):
        self._set_pigeon(0)

    def on_button_up_clicked(self, widget):
        self._set_pigeon(self.current_pigeon - 1)

    def on_button_down_clicked(self, widget):
        self._set_pigeon(self.current_pigeon + 1)

    def on_button_bottom_clicked(self, widget):
        self._set_pigeon(self.pigeon_no - 1)

    ####################
    # Public methods
    ####################


    ####################
    # Internal methods
    ####################
    def _build_menubar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_mainwindow)
        uimanager.insert_action_group(self._create_action_group(), 0)
        uimanager.connect('connect-proxy', self.on_uimanager_connect_proxy)
        accelgroup = uimanager.get_accel_group()
        self.mainwindow.add_accel_group(accelgroup)

        widgetDic = {
            "menubar": uimanager.get_widget('/MenuBar'),
            "toolbar": uimanager.get_widget('/Toolbar'),
            "MenuArrows": uimanager.get_widget('/MenuBar/ViewMenu/Arrows'),
            "MenuStats": uimanager.get_widget('/MenuBar/ViewMenu/Stats'),
            "MenuToolbar": uimanager.get_widget('/MenuBar/ViewMenu/Toolbar'),
            "MenuStatusbar": \
                uimanager.get_widget('/MenuBar/ViewMenu/Statusbar'),
            "Filtermenu": uimanager.get_widget('/MenuBar/ViewMenu/FilterMenu'),
            "MenuEdit": uimanager.get_widget('/MenuBar/PigeonMenu/Edit'),
            "MenuRemove": uimanager.get_widget('/MenuBar/PigeonMenu/Remove'),
            "MenuPedigree": \
                uimanager.get_widget('/MenuBar/PigeonMenu/Pedigree'),
            "MenuAddresult": \
                uimanager.get_widget('/MenuBar/PigeonMenu/Addresult'),
            "ToolEdit": uimanager.get_widget('/Toolbar/Edit'),
            "ToolRemove": uimanager.get_widget('/Toolbar/Remove'),
            "ToolPedigree": uimanager.get_widget('/Toolbar/Pedigree')
            }
        for name, widget in widgetDic.items():
            setattr(self, name, widget)

        self.set_multiple_sensitive([self.MenuEdit, self.MenuRemove,
                                     self.MenuPedigree, self.MenuAddresult,
                                     self.ToolEdit, self.ToolRemove,
                                     self.ToolPedigree], False)

        self.vbox.pack_start(self.menubar, False, False)
        self.vbox.pack_start(self.toolbar, False, False)

        if const.OSX:
            try:
                import igemacintegration as igemi
            except ImportError:
                logger.warning("ige-mac-integration not found")
            else:
                # Move the menu bar from the window to the Mac menu bar
                self.menubar.hide()
                igemi.ige_mac_menu_set_menu_bar(self.menubar)

                # Reparent some items to the "Application" menu
                for widget in ('/MenuBar/HelpMenu/About',
                               '/MenuBar/EditMenu/Preferences'):
                    item = uimanager.get_widget(widget)
                    group = igemi.ige_mac_menu_add_app_menu_group()
                    igemi.ige_mac_menu_add_app_menu_item(group, item, None)

                quit_item = uimanager.get_widget('/MenuBar/FileMenu/Quit')
                igemi.ige_mac_menu_set_quit_menu_item(quit_item)

    def _create_action_group(self):
        action_group = gtk.ActionGroup("MainWindowActions")
        action_group.add_actions((
            ("FileMenu", None, _("_File")),
            ("PrintMenu", gtk.STOCK_PRINT, None),
            ("BackupMenu", None, _("_Backup")),
            ("PigeonMenu", None, _("_Pigeon")),
            ("EditMenu", None, _("_Edit")),
            ("ViewMenu", None, _("_View")),
            ("ToolsMenu", None, _("_Tools")),
            ("HelpMenu", None, _("_Help")),
            ("PrintPedigree", None, _("_Pedigree"), None,
                    _("Print this pedigree"), self.menuprintpedigree_activate),
            ("PrintBlank", None, _("Blank pedigree"), None,
                    _("Print a blank pedigree"), self.menuprintblank_activate),
            ("Backup", gtk.STOCK_FLOPPY, _("_Backup"), None,
                    _("Create a backup of your database"),
                    self.menubackup_activate),
            ("Restore", gtk.STOCK_REVERT_TO_SAVED, _("_Restore"), None,
                    _("Restore a backup of your database"),
                    self.menurestore_activate),
            ("Quit", gtk.STOCK_QUIT, None, "<control>Q",
                    _("Quit the program"), self.quit_program),
            ("Add", gtk.STOCK_ADD, None, "<control>A",
                    _("Add a new pigeon"), self.menuadd_activate),
            ("Addrange", gtk.STOCK_ADD, _("Add ran_ge"), "<control><shift>A",
                    _("Add a range of pigeons"), self.menuaddrange_activate),
            ("Log", gtk.STOCK_FILE, _("_Logfile Viewer"), "<control>L",
                    _("See the logfile"), self.menulog_activate),
            ("Search", gtk.STOCK_FIND, _("_Find..."), "<control>F",
                    _("Search through the list of pigeons"),
                    self.menusearch_activate),
            ("Edit", gtk.STOCK_EDIT, None, "<control>E",
                    _("Edit the selected pigeon"), self.menuedit_activate),
            ("Remove", gtk.STOCK_REMOVE, None, "<control>R",
                    _("Remove the selected pigeon"), self.menuremove_activate),
            ("Pedigree", "pedigree-detail", _("_Pedigree"), "<control>G",
                    _("View the detailed pedigree of this pigeon"),
                    self.menupedigree_activate),
            ("Addresult", gtk.STOCK_ADD, _("Add resul_t"), None,
                    _("Add a new result for this pigeon"),
                    self.menuaddresult_activate),
            ("Preferences", gtk.STOCK_PREFERENCES, None, "<control>P",
                    _("Configure the application"), self.menupref_activate),
            ("Filter", None, _("_Filter..."), None,
                    _("Set filter options"), self.menufilter_activate),
            ("Velocity", None, _("Velocity calculator"), None,
                    _("Calculate the velocity of flights"),
                    self.menuvelocity_activate),
            ("Album", None, _("_Photo Album"), None,
                    _("View the images of your pigeons"),
                    self.menualbum_activate),
            ("Addresses", None, _("Address book"), None,
                    _("View the address book"),  self.menuaddresses_activate),
            ("Calendar", None, _("Calendar"), None,
                    _("View the calendar"),  self.menucalendar_activate),
            ("Data", None, _("Data manager"), None,
                    _("Manage your data"),  self.menudata_activate),
            ("Home", gtk.STOCK_HOME, _("_Website"), None,
                    _("Go to the website for more information"),
                    self.menuhome_activate),
            ("Forum", gtk.STOCK_INFO, _("Forum"), None,
                    _("Go to the forum for online help"),
                    self.menuforum_activate),
            ("Update", gtk.STOCK_CONNECT, _("Search for updates..."), None,
                    _("Search online for program updates"),
                    self.menuupdate_activate),
            ("Info", gtk.STOCK_INFO, None, None,
                    _("General information"), self.menuinfo_activate),
            ("About", gtk.STOCK_ABOUT, None, None,
                    _("About this application"), self.menuabout_activate)
           ))
        action_group.add_toggle_actions((
            ("Arrows",  None, _("Navigation arrows"), None,
                    _("Show or hide the navigation arrows"),
                    self.menuarrows_toggled, False),
            ("Stats",  None, _("Statistics"), None,
                    _("Show or hide pigeon statistics"),
                    self.menustats_toggled, False),
            ("Toolbar",  None, _("Toolbar"), None,
                    _("Show or hide the toolbar"),
                    self.menutoolbar_toggled, False),
            ("Statusbar",  None, _("Statusbar"), None,
                    _("Show or hide the statusbar"),
                    self.menustatusbar_toggled, False)
           ))
        return action_group

    def _start_edit(self, operation):
        self.set_multiple_sensitive([self.menubar, self.toolbar, self.notebook,
                                     self.treeview, self.vboxButtons], False)
        self.detailsview.start_edit(operation)

    def _finish_edit(self, cancelled=False):
        if not cancelled:
            self._set_statistics()
        self.set_multiple_sensitive([self.menubar, self.toolbar, self.notebook,
                                     self.treeview, self.vboxButtons], True)
        self.treeview.grab_focus()

    def _clear_pigeon_data(self):
        self.detailsview.clear_details()
        self.pedigreetab.draw_pedigree()
        self.relativestab.clear_treeviews()
        self.medicationtab.liststore.clear()
        self.resultstab.liststore.clear()

    def _set_statistics(self):
        """
        Count all active pigeons and set the statistics labels
        """

        total, cocks, hens, ybirds = common.count_active_pigeons(self.database)
        self.labelStatTotal.set_markup("<b>%i</b>" %total)
        self.labelStatCocks.set_markup("<b>%i</b>" %cocks)
        self.labelStatHens.set_markup("<b>%i</b>" %hens)
        self.labelStatYoung.set_markup("<b>%i</b>" %ybirds)

    def _set_pigeon(self, pigeon_no):
        if pigeon_no < 0 or pigeon_no >= self.pigeon_no:
            return

        if self.current_pigeon != pigeon_no:
            self.selection.unselect_all()
            self.selection.select_path(pigeon_no)

