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
import datetime
import webbrowser
import logging
logger = logging.getLogger(__name__)

import gtk
import glib
import gobject

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import backup
from pigeonplanner import checks
from pigeonplanner import update
from pigeonplanner import builder
from pigeonplanner import printing
from pigeonplanner import messages
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import calendar
from pigeonplanner.ui import pedigree
from pigeonplanner.ui import logdialog
from pigeonplanner.ui import photoalbum
from pigeonplanner.ui import addressbook
from pigeonplanner.ui import toolswindow
from pigeonplanner.ui import resultwindow
from pigeonplanner.ui import optionsdialog
from pigeonplanner.ui import pedigreewindow
from pigeonplanner.ui.widgets import date
from pigeonplanner.ui.widgets import menus
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.ui.widgets import filefilters
from pigeonplanner.ui.widgets import checkbutton


class MainWindow(builder.GtkBuilder):
    def __init__(self, options, database, parser):
        builder.GtkBuilder.__init__(self, const.GLADEMAIN)

        self.options = options
        self.database = database
        self.parser = parser

        self.mainwindow.set_title("%s %s" %(const.NAME, const.VERSION))

        self.changedRowIter = None
        self.blockMenuCallback = False
        self.logoPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                                os.path.join(const.IMAGEDIR,
                                                             'icon_logo.png'),
                                                75, 75)
        self.sexImgs = {'0': gtk.gdk.pixbuf_new_from_file(os.path.join(
                                        const.IMAGEDIR, "symbol_male.png")),
                        '1': gtk.gdk.pixbuf_new_from_file(os.path.join(
                                        const.IMAGEDIR, "symbol_female.png")),
                        '2': gtk.gdk.pixbuf_new_from_file(os.path.join(
                                        const.IMAGEDIR, "symbol_young.png"))}
        self.sexDic = {'0': _('Cock'), '1': _('Hen'), '2': _('Young bird')}
        self.pigeonStatus = {0: 'Dead', 1: 'Active', 2: 'Sold', 3: 'Lost'}
        self.today = datetime.date.today().strftime(const.DATE_FORMAT)
        self.entryDate.set_text(self.today)
        self.cbStatus.set_active(1)

        self.cancelEscAG = gtk.AccelGroup()
        key, modifier = gtk.accelerator_parse('Escape')
        self.cancelEscAG.connect_group(key, modifier, gtk.ACCEL_VISIBLE,
                                       self.add_edit_finish)

        self.entrySexKey = gtk.Entry()
        self.hbox4.pack_start(self.entrySexKey)

        # Make thumbnails if they don't exist yet (new in 0.8.0)
        if not os.path.isdir(const.THUMBDIR):
            logger.info("Make thumbnail folder and building thumbnails")
            os.mkdir(const.THUMBDIR)
            self.build_thumbnails()

        self.pedigree = pedigree.DrawPedigree(self)
        self.draw_empty_pedigree()
        self.build_menubar()
        self.build_treeviews()
        self.build_treeview()
        self.fill_treeview()
        self.count_active_pigeons()

        self.cbRangeSex = comboboxes.SexCombobox(self.sexDic)
        self.cbsex = comboboxes.SexCombobox(self.sexDic)
        self.table1.attach(self.cbRangeSex, 6, 7, 1, 2, gtk.SHRINK, gtk.FILL)
        self.table4.attach(self.cbsex, 1, 2, 1, 2, gtk.SHRINK, gtk.FILL)
        self.check_vaccination = checkbutton.VaccinationCheck()
        self.alignment_vaccination.add(self.check_vaccination)

        cbentries = [self.cbRacepoint, self.cbSector, self.cbType,
                     self.cbCategory, self.cbWeather, self.cbWind,
                     self.cbColour, self.cbStrain, self.cbLoft]
        for item in cbentries:
            comboboxes.set_entry_completion(item)

        # This can't be done in Glade
        for cbentry in cbentries:
            cbentry.child.set_activates_default(True)

        if const.SMALL_SCREEN:
            common.create_stock_button([
                                ('icon_pedigree.png', 'pedigree', ''),
                                ('icon_relatives.png', 'relatives', ''),
                                ('icon_result.png', 'results', ''),
                                ('icon_medication.png', 'medication', '')
                            ])

            for tabname in ['Pedigree', 'Relatives', 'Results', 'Medication']:
                tabBox = getattr(self, 'vbox'+tabname)
                tabBox.set_orientation(gtk.ORIENTATION_HORIZONTAL)
                tabImage = getattr(self, 'image'+tabname+'Tab')
                tabImage.set_from_stock(tabname.lower(), gtk.ICON_SIZE_BUTTON)

        if self.options.optionList.arrows:
            self.MenuArrows.set_active(True)

        if self.options.optionList.stats:
            self.MenuStats.set_active(True)

        if self.options.optionList.toolbar:
            self.MenuToolbar.set_active(True)

        if self.options.optionList.statusbar:
            self.MenuStatusbar.set_active(True)

        listdata = {self.cbSector: self.database.SECTORS,
                    self.cbType: self.database.TYPES,
                    self.cbCategory: self.database.CATEGORIES,
                    self.cbRacepoint: self.database.RACEPOINTS,
                    self.cbWeather: self.database.WEATHER,
                    self.cbWind: self.database.WIND,
                    self.cbColour: self.database.COLOURS,
                    self.cbStrain: self.database.STRAINS,
                    self.cbLoft: self.database.LOFTS}
        for key, value in listdata.items():
            comboboxes.fill_combobox(key, self.database.select_from_table(value))

        self.statusmsgs = {'entryRing1': (self.statusbar.get_context_id("band"),
                            _("Enter the bandnumber of the pigeon")),
                           'entryYear1': (self.statusbar.get_context_id("year"),
                            _("Enter the year of the pigeon")),
                           'btnStatus1': (self.statusbar.get_context_id("status"),
                            _("Click here to set the status of the pigeon")),
                           'entryName1': (self.statusbar.get_context_id("name"),
                            _("Enter a name for the pigeon")),
                           'eventimage': (self.statusbar.get_context_id("img"),
                            _("Click here to add an image")),
                           'findSire': (self.statusbar.get_context_id("sire"),
                            _("Search through the list of cocks")),
                           'findDam': (self.statusbar.get_context_id("dam"),
                            _("Search through the list of hens"))
                          }

        for wname, data in self.statusmsgs.items():
            attr = getattr(self, wname)
            attr.set_tooltip_text(data[1])

        if self.options.optionList.runs == 10:
            d = dialogs.MessageDialog(const.QUESTION,
                                      messages.MSG_MAKE_DONATION,
                                      self.mainwindow)
            if d.yes:
                webbrowser.open(const.WEBSITE)

            self.options.set_option('Options', 'runs',
                                    self.options.optionList.runs+1)

        self.mainwindow.show()

        events = self.database.get_notification(time.time())
        if events:
            description = events[0][2]
            if len(description) > 20:
                description = description[:24]+"..."
            d = dialogs.MessageDialog(const.QUESTION,
                                      messages.MSG_EVENT_NOTIFY,
                                      self.mainwindow, description)
            if d.yes:
                calendar.Calendar(self.mainwindow, self.database, events[0][0])

    def quit_program(self, widget=None, event=None, bckp=True):
        if self.options.optionList.backup and bckp:
            daysInSeconds = self.options.optionList.interval * 24 * 60 * 60
            if time.time() - self.options.optionList.last >= daysInSeconds:
                if backup.make_backup(self.options.optionList.location):
                    dialogs.MessageDialog(const.INFO,
                                          messages.MSG_BACKUP_SUCCES,
                                          self.mainwindow)
                else:
                    dialogs.MessageDialog(const.INFO,
                                          messages.MSG_BACKUP_FAILED,
                                          self.mainwindow)

                self.options.set_option('Backup', 'last', time.time())

        if self.options.optionList.runs < 10:
            self.options.set_option('Options', 'runs',
                                    self.options.optionList.runs+1)

        gtk.main_quit()

    def on_dialog_delete(self, widget, event):
        widget.hide()
        return True

    def on_widget_enter(self, widget, event):
        for con_id in self.statusmsgs.values():
            self.statusbar.pop(con_id[0])

        self.statusbar.push(
                            self.statusmsgs[self.get_object_name(widget)][0],
                            self.statusmsgs[self.get_object_name(widget)][1])

    def on_widget_leave(self, widget, event):
        name = self.get_object_name(widget)
        self.statusbar.pop(self.statusmsgs[name][0])

    # Menu callbacks
    def menuprintpedigree_activate(self, widget):
        logger.info(common.get_function_name())
        userinfo = common.get_own_address(self.database)
        pigeoninfo = self.get_pigeoninfo()

        printing.PrintPedigree(self.mainwindow, pigeoninfo, userinfo,
                               self.options.optionList, const.PRINT, '',
                               self.parser.pigeons)

    def menuprintblank_activate(self, widget):
        logger.info(common.get_function_name())
        userinfo = common.get_own_address(self.database)
        pigeoninfo = dict(pindex='', ring='', year='', sex='', colour='',
                          name='', image='', extra1='', extra2='', extra3='',
                          extra4='', extra5='', extra6='')

        printing.PrintPedigree(self.mainwindow, pigeoninfo, userinfo,
                               self.options.optionList, const.PRINT, '',
                               self.parser.pigeons)

    def menubackup_activate(self, widget):
        logger.info(common.get_function_name())
        dialog = dialogs.BackupDialog(self.mainwindow, const.CREATE)
        run = dialog.run()
        dialog.destroy()

    def menurestore_activate(self, widget):
        logger.info(common.get_function_name())
        dialog = dialogs.BackupDialog(self.mainwindow, const.RESTORE)
        run = dialog.run()
        dialog.destroy()

    def menuclose_activate(self, widget):
        logger.info(common.get_function_name())
        self.quit_program()

    def menusearch_activate(self, widget):
        logger.info(common.get_function_name())
        self.searchdialog.show()
        self.srchentry.grab_focus()

    def menualbum_activate(self, widget):
        logger.info(common.get_function_name())
        photoalbum.PhotoAlbum(self.mainwindow, self.parser, self.database)

    def menulog_activate(self, widget):
        logger.info(common.get_function_name())
        logdialog.LogDialog(self.database)

    def menuadd_activate(self, widget):
        logger.info(common.get_function_name())
        self.empty_entryboxes()
        self.cbColour.child.set_text('')
        self.cbStrain.child.set_text('')
        self.cbLoft.child.set_text('')
        self.cbsex.set_active(0)
        self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)
        self.labelImgPath.set_text('')
        self.imageStatus1.set_from_file(os.path.join(const.IMAGEDIR,
                                                     'active.png'))
        self.cbStatus.set_active(1)

        self.add_edit_start(const.ADD)

    def menuaddrange_activate(self, widget):
        logger.info(common.get_function_name())
        self.entryRangeFrom.set_text('')
        self.entryRangeTo.set_text('')
        self.entryRangeYear.set_text('')
        self.cbRangeSex.set_active(2)
        self.entryRangeFrom.grab_focus()
        self.rangedialog.show()

    def menuedit_activate(self, widget):
        logger.info(common.get_function_name())
        model, paths = self.selection.get_selected_rows()
        if len(paths) != 1: return

        self.treeIterEdit = self.liststore.get_iter(paths[0])
        pindex = model[self.treeIterEdit][0]

        self.entryRing1.set_text(self.entryRing.get_text())
        self.entryYear1.set_text(self.entryYear.get_text())
        self.entryName1.set_text(self.entryName.get_text())
        self.entryExtra11.set_text(self.entryExtra1.get_text())
        self.entryExtra21.set_text(self.entryExtra2.get_text())
        self.entryExtra31.set_text(self.entryExtra3.get_text())
        self.entryExtra41.set_text(self.entryExtra4.get_text())
        self.entryExtra51.set_text(self.entryExtra5.get_text())
        self.entryExtra61.set_text(self.entryExtra6.get_text())
        self.cbColour.child.set_text(self.entryColour.get_text())
        self.cbStrain.child.set_text(self.entryStrain.get_text())
        self.cbLoft.child.set_text(self.entryLoft.get_text())
        self.entrySireEdit.set_text(self.entrySire.get_text())
        self.entryYearSireEdit.set_text(self.entryYearSire.get_text())
        self.entryDamEdit.set_text(self.entryDam.get_text())
        self.entryYearDamEdit.set_text(self.entryYearDam.get_text())

        self.cbsex.set_active(int(self.entrySexKey.get_text()))

        status = self.parser.pigeons[pindex].active
        self.cbStatus.set_active(status)
        self.notebookStatus.set_current_page(status)

        self.preEditImage = self.parser.pigeons[pindex].image

        self.add_edit_start(const.EDIT)

    def menuremove_activate(self, widget):
        logger.info(common.get_function_name())
        model, paths = self.selection.get_selected_rows()

        if self.selection.count_selected_rows() == 1:
            logger.info("Remove: Removing one pigeon")
            pindex, ring, year = self.get_main_ring()
            statusbarmsg = _("Pigeon %s/%s has been removed" %(ring, year))
            pigeonlabel = '%s / %s' %(ring, year)
            show_result_option = self.database.has_results(pindex)
            pigeons = [pindex]
        else:
            logger.info("Remove: Removing multiple pigeons")
            pigeons = [p for p, y, r in self.get_main_ring()]
            bands = ['%s / %s' %(ring, year) for pindex, ring, year in
                     self.get_main_ring()]
            pigeonlabel = ", ".join(bands)
            statusbarmsg = _("%s pigeons have been removed" %len(pigeons))
            show_result_option = False
            for p in pigeons:
                if self.database.has_results(p):
                    show_result_option = True
                    break

        self.labelPigeon.set_text(pigeonlabel)
        self.chkKeep.set_active(True)
        self.chkResults.set_active(False)
        self.set_multiple_visible([self.chkResults], show_result_option)

        answer = self.removedialog.run()
        if answer == 2:
            if self.chkKeep.get_active():
                logger.info("Remove: Hiding the pigeon(s)")
                for pindex in pigeons:
                    self.database.update_table(self.database.PIGEONS,
                                               (0, pindex), 5, 1)
            else:
                logger.info("Remove: Removing the pigeon(s)")
                for pindex in pigeons:
                    self.database.delete_from_table(self.database.PIGEONS, pindex)
                    # Only remove status when pigeon is completely removed
                    status = self.parser.pigeons[pindex].active
                    if status != const.ACTIVE:
                        self.database.delete_from_table(self.pigeonStatus[status],
                                                        pindex)
                    # Same for the picture
                    image = self.parser.pigeons[pindex].image
                    if image:
                        os.remove(common.get_thumb_path(image))
                    # And medication
                    self.database.delete_from_table(self.database.MED, pindex, 2)

            if not self.chkResults.get_active():
                logger.info("Remove: Removing the results")
                for pindex in pigeons:
                    self.database.delete_from_table(self.database.RESULTS, pindex)

            # Block the selection changed signal for each row that is being
            # removed. This will cause problems because the deleted pigeon
            # will be selected. Just emit the signal once afterwards.
            iters = [self.liststore.get_iter(path) for path in paths]
            self.selection.handler_block(self.selection_changed_id)
            for tree_iter in iters:
                self.liststore.remove(tree_iter)
            self.selection.handler_unblock(self.selection_changed_id)
            self.selection.emit('changed')

            if len(self.liststore) > 0:
                self.selection.select_path(paths[0])

            self.parser.get_pigeons()
            self.count_active_pigeons()

            common.add_statusbar_message(self.statusbar, statusbarmsg)

        self.removedialog.hide()

    def menupedigree_activate(self, widget):
        logger.info(common.get_function_name())
        pedigreewindow.PedigreeWindow(self, self.get_pigeoninfo())

    def menuaddresult_activate(self, widget):
        logger.info(common.get_function_name())
        self.notebook.set_current_page(2)
        self.on_addresult_clicked(None)

    def menufilter_activate(self, widget):
        logger.info(common.get_function_name())
        filterdialog = dialogs.FilterDialog(self.mainwindow,
                                            _("Filter pigeons"),
                                            self.fill_treeview)

        self.cbFilterSex = comboboxes.SexCombobox(self.sexDic)
        self.chkFilterSex = filterdialog.add_filter_custom(_("Sex"),
                                                           self.cbFilterSex)
        self.chkFilterColours, self.cbFilterColour = \
                                filterdialog.add_filter_combobox(_("Colours"),
                                            self.database.select_from_table(
                                                self.database.COLOURS))
        self.chkFilterStrains, self.cbFilterStrain = \
                                filterdialog.add_filter_combobox(_("Strains"),
                                            self.database.select_from_table(
                                                self.database.STRAINS))
        self.chkFilterLofts, self.cbFilterLoft = \
                                filterdialog.add_filter_combobox(_("Lofts"),
                                            self.database.select_from_table(
                                                self.database.LOFTS))
        self.cbFilterStatus = comboboxes.StatusCombobox()
        self.chkFilterStatus = filterdialog.add_filter_custom(_("Status"),
                                                        self.cbFilterStatus)

        filterdialog.run()

    def menutools_activate(self, widget):
        logger.info(common.get_function_name())
        toolswindow.ToolsWindow(self)

    def menupref_activate(self, widget):
        logger.info(common.get_function_name())
        optionsdialog.OptionsDialog(self)

    def menuarrows_toggled(self, widget):
        logger.info(common.get_function_name())
        if self.blockMenuCallback: return

        if widget.get_active():
            self.vboxButtons.show()
            self.options.set_option('Options', 'arrows', 'True')
        else:
            self.vboxButtons.hide()
            self.options.set_option('Options', 'arrows', 'False')

    def menustats_toggled(self, widget):
        logger.info(common.get_function_name())
        if self.blockMenuCallback: return

        if widget.get_active():
            self.alignStats.show()
            self.options.set_option('Options', 'stats', 'True')
        else:
            self.alignStats.hide()
            self.options.set_option('Options', 'stats', 'False')

    def menutoolbar_toggled(self, widget):
        logger.info(common.get_function_name())
        if self.blockMenuCallback: return

        if widget.get_active():
            self.toolbar.show()
            self.options.set_option('Options', 'toolbar', 'True')
        else:
            self.toolbar.hide()
            self.options.set_option('Options', 'toolbar', 'False')

    def menustatusbar_toggled(self, widget):
        logger.info(common.get_function_name())
        if self.blockMenuCallback: return

        if widget.get_active():
            self.statusbar.show()
            self.options.set_option('Options', 'statusbar', 'True')
        else:
            self.statusbar.hide()
            self.options.set_option('Options', 'statusbar', 'False')

    def menuaddresses_activate(self, widget):
        logger.info(common.get_function_name())
        addressbook.AddressBook(self.mainwindow, self.database)

    def menucalendar_activate(self, widget):
        logger.info(common.get_function_name())
        calendar.Calendar(self.mainwindow, self.database)

    def menuhome_activate(self, widget):
        logger.info(common.get_function_name())
        webbrowser.open(const.WEBSITE)

    def menuforum_activate(self, widget):
        logger.info(common.get_function_name())
        webbrowser.open(const.FORUMURL)

    def menuupdate_activate(self, widget):
        logger.info(common.get_function_name())
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

    def menuabout_activate(self, widget):
        logger.info(common.get_function_name())
        dialogs.AboutDialog(self.mainwindow)

    # range callbacks
    def on_rangeadd_clicked(self, widget):
        rangefrom = self.entryRangeFrom.get_text()
        rangeto = self.entryRangeTo.get_text()
        rangeyear = self.entryRangeYear.get_text()
        rangesex = self.cbRangeSex.get_active_text()

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

        value = int(rangefrom)
        while value <= int(rangeto):
            band = str(value)
            pindex = band + rangeyear

            if self.database.has_pigeon(pindex):
                d = dialogs.MessageDialog(const.WARNING,
                                          messages.MSG_OVERWRITE_PIGEON,
                                          self.mainwindow)
                if not d.yes:
                    continue

            self.database.insert_into_table(self.database.PIGEONS,
                                        (pindex, band, rangeyear, rangesex,
                                         1, 1, '', '', '', '', '', '', '',
                                         '', '', '', '', '', '', '', ''))

            value += 1

        self.parser.get_pigeons()
        self.fill_treeview()

        self.rangedialog.hide()

    def on_rangecancel_clicked(self, widget):
        self.rangedialog.hide()

    # Search dialog callbacks
    def on_srchentry_changed(self, widget):
        if widget.get_text():
            self.search.set_sensitive(True)
            widget.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                       gtk.STOCK_CLEAR)
        else:
            self.search.set_sensitive(False)
            widget.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)

    def on_srchentry_press(self, widget, icon, event):
        self.fill_treeview()
        widget.set_text('')
        widget.grab_focus()

    def on_search_clicked(self, widget):
        keyword = self.srchentry.get_text()
        results = []

        if self.chkband.get_active():
            results.extend([pindex for pindex in self.parser.pigeons
                            if keyword in self.parser.pigeons[pindex].ring])

        if self.chkname.get_active():
            results.extend([pindex for pindex in self.parser.pigeons
                            if keyword in self.parser.pigeons[pindex].name])

        self.fill_treeview(search_results=results)

    def on_srchclose_clicked(self, widget, event=None):
        self.fill_treeview()
        self.searchdialog.hide()

        return True

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

    # Navigation arrows callbacks
    def on_button_top_clicked(self, widget):
        if len(self.liststore) > 0:
            path = (0,)
            self.treeview.set_cursor(path)

    def on_button_up_clicked(self, widget):
        path, focus = self.treeview.get_cursor()

        try:
            temp = path[0]
            if not temp == 0:
                new_path = (temp-1,)
                self.treeview.set_cursor(new_path)
        except TypeError:
            pass

    def on_button_down_clicked(self, widget):
        path, focus = self.treeview.get_cursor()

        try:
            temp = path[0]
            if not temp == len(self.liststore)-1:
                new_path = (temp+1,)
                self.treeview.set_cursor(new_path)
        except TypeError:
            pass

    def on_button_bottom_clicked(self, widget):
        if len(self.liststore) > 0:
            path = (len(self.liststore)-1,)
            self.treeview.set_cursor(path)

    # Add/Edit callbacks
    def on_save_clicked(self, widget):
        entries = [(self.entryRing1, self.entryYear1),
                   (self.entrySireEdit, self.entryYearSireEdit),
                   (self.entryDamEdit, self.entryYearDamEdit)]
        for band, year in entries:
            # Sire and dam input are not required
            if band.get_text() == '' and \
               self.get_object_name(band) != "entryRing1":
                continue

            try:
                checks.check_ring_entry(band.get_text(), year.get_text())
            except checks.InvalidInputError, msg:
                dialogs.MessageDialog(const.ERROR, msg.value, self.mainwindow)
                return

        if self.operation == const.EDIT:
            self.write_new_data()
        elif self.operation == const.ADD:
            self.write_new_pigeon()

        self.add_edit_finish()

    def on_cancel_clicked(self, widget):
        self.add_edit_finish(True)

    # Image callbacks
    def on_eventbox_press(self, widget, event):
        try:
            pindex, ring, year = self.get_main_ring()
        except TypeError:
            # No pigeon is selected
            return

        photoalbum.PhotoAlbum(self.mainwindow, self.parser, self.database, pindex)

    def on_eventimage_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_ADD, self.open_filedialog, None),
                (gtk.STOCK_REMOVE, self.set_default_image, None)]

            menus.popup_menu(event, entries)
        else:
            self.open_filedialog()

    def on_fcnoimage_clicked(self, widget):
        self.set_default_image()
        self.filedialog.hide()

    def on_fcopen_clicked(self, widget):
        filename = self.filedialog.get_filename()
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 200, 200)
            self.imagePigeon.set_from_pixbuf(pixbuf)
            self.imagePigeon1.set_from_pixbuf(pixbuf)
            self.labelImgPath.set_text(filename)
        except:
            dialogs.MessageDialog(const.ERROR, messages.MSG_INVALID_IMAGE,
                                  self.mainwindow)

        self.filedialog.hide()

    def on_fccancel_clicked(self, widget):
        self.filedialog.hide()

    def on_filedialog_update_preview(self, widget):
        filename = self.filedialog.get_preview_filename()
        try:
          pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 128, 128)
          self.filedialog.get_preview_widget().set_from_pixbuf(pixbuf)
          have_preview = True
        except:
          have_preview = False
        self.filedialog.set_preview_widget_active(have_preview)

    # Relatives callbacks
    def on_tvBrothers_press(self, widget, event):
        self.relative_treeview_pressed(widget, event)

    def on_tvHalfBrothers_press(self, widget, event):
        self.relative_treeview_pressed(widget, event)

    def on_tvOffspring_press(self, widget, event):
        self.relative_treeview_pressed(widget, event)

    def relative_treeview_pressed(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        path, col, cellx, celly = pthinfo
        pindex = treeview.get_model()[path][0]

        if event.button == 3:
            menus.popup_menu(event, [
                                     (gtk.STOCK_INFO,
                                      self.show_pigeon_details, (pindex,)),
                                     (gtk.STOCK_JUMP_TO,
                                      self.search_pigeon, (pindex,)),
                                    ])
        elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.show_pigeon_details(None, pindex)

    # Result callbacks
    def on_tvResults_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return

        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_editresult_clicked, None),
                (gtk.STOCK_REMOVE, self.on_removeresult_clicked, None)]

            menus.popup_menu(event, entries)

    def on_allresults_clicked(self, widget):
        resultwindow.ResultWindow(self, self.parser.pigeons, self.database)

    def on_addresult_clicked(self, widget):
        self.menubar.set_sensitive(False)
        self.toolbar.set_sensitive(False)

        self.clear_resultdialog_fields()
        self.resultDialogMode = const.ADD
        self.labelModeResult.set_text(_('Add result for:'))
        self.resultdialog.show()
        self.resultdialog.set_modal(False)
        self.entryDate.set_position(10)

    def on_removeresult_clicked(self, widget):
        path, focus = self.tvResults.get_cursor()
        model, tIter = self.selResults.get_selected()
        pindex, ring, year = self.get_main_ring()

        d = dialogs.MessageDialog(const.QUESTION,
                                  messages.MSG_REMOVE_RESULT,
                                  self.mainwindow)
        if not d.yes:
            return

        self.database.delete_from_table(self.database.RESULTS,
                                        model[tIter][0], 0)

        self.lsResult.remove(tIter)

        if len(self.lsResult) > 0:
            self.tvResults.set_cursor(path)

            common.add_statusbar_message(self.statusbar,
                                         _("Result has been removed"))

    def on_editresult_clicked(self, widget):
        result = self.get_selected_result()
        for index, item in enumerate(result):
            # Happens on conversion from 0.6.0 to 0.7.0
            if item is None:
                result[index] = ''

        self.entryDate.set_text(result[1])
        self.cbRacepoint.child.set_text(result[2])
        self.spinPlaced.set_value(result[3])
        self.spinOutof.set_value(result[4])
        self.cbSector.child.set_text(result[6])
        self.cbType.child.set_text(result[7])
        self.cbCategory.child.set_text(result[8])
        self.cbWeather.child.set_text(result[9])
        self.cbWind.child.set_text(result[10])
        self.entryComment.set_text(result[11])

        self.resultDialogMode = const.EDIT
        self.labelModeResult.set_text(_('Edit result for:'))
        self.resultdialog.show()
        self.resultdialog.set_modal(True)
        self.entryDate.set_position(10)

    def on_resultdialogsave_clicked(self, widget):
        try:
            pindex, ring, year = self.get_main_ring()
        except TypeError:
            return

        try:
            (date, point, place, out, sector, ftype, category, weather,
                wind, comment) = self.get_resultdata()
        except TypeError:
            return

        cof = (float(place)/float(out))*100
        data = (date, point, place, out, sector, ftype, category, wind,
                weather, '', '', 0, 0, comment)
        if self.resultDialogMode == const.ADD:
            if self.database.has_result((pindex,)+data):
                dialogs.MessageDialog(const.ERROR,
                                      messages.MSG_RESULT_EXISTS,
                                      self.mainwindow)
                return

            data = (pindex, ) + data
            rowid = self.database.insert_into_table(self.database.RESULTS, data)
            self.lsResult.insert(0, [rowid, date, point, place, out, cof,
                                     sector, ftype, category, weather,
                                     wind, comment])
            common.add_statusbar_message(self.statusbar,
                                         _("Result has been added"))
        elif self.resultDialogMode == const.EDIT:
            selection = self.tvResults.get_selection()
            model, node = selection.get_selected()
            self.lsResult.set(node, 1, date, 2, point, 3, place, 4, out,
                              5, cof, 6, sector, 7, ftype, 8, category,
                              9, weather, 10, wind, 11, comment)

            data += (self.lsResult.get_value(node, 0), )
            self.database.update_table(self.database.RESULTS, data, 2, 0)

            self.hide_result_dialog()

        self.database.insert_into_table(self.database.RACEPOINTS,
                                        (point, "", "", ""))
        comboboxes.fill_combobox(self.cbRacepoint,
                                 self.database.select_from_table(
                                            self.database.RACEPOINTS))

        if sector:
            self.database.insert_into_table(self.database.SECTORS, (sector, ))
            comboboxes.fill_combobox(self.cbSector,
                                     self.database.select_from_table(
                                            self.database.SECTORS))

        if ftype:
            self.database.insert_into_table(self.database.TYPES, (ftype, ))
            comboboxes.fill_combobox(self.cbType,
                                     self.database.select_from_table(
                                            self.database.TYPES))

        if category:
            self.database.insert_into_table(self.database.CATEGORIES,
                                            (category, ))
            comboboxes.fill_combobox(self.cbCategory,
                                     self.database.select_from_table(
                                            self.database.CATEGORIES))

        if weather:
            self.database.insert_into_table(self.database.WEATHER, (weather, ))
            comboboxes.fill_combobox(self.cbWeather,
                                     self.database.select_from_table(
                                            self.database.WEATHER))

        if wind:
            self.database.insert_into_table(self.database.WIND, (wind, ))
            comboboxes.fill_combobox(self.cbWind,
                                     self.database.select_from_table(
                                            self.database.WIND))

    def on_resultdialogclose_clicked(self, widget):
        self.hide_result_dialog()

    def hide_result_dialog(self, widget=None, event=None):
        self.menubar.set_sensitive(True)
        self.toolbar.set_sensitive(True)
        self.resultdialog.hide()

        return True

    def on_spinPlaced_changed(self, widget):
        self.spinOutof.set_range(widget.get_value_as_int(),
                                 widget.get_range()[1])

    def clear_resultdialog_fields(self):
        self.entryDate.set_text(self.today)
        self.cbRacepoint.child.set_text('')
        self.spinPlaced.set_value(1)
        self.spinOutof.set_value(1)
        self.cbSector.child.set_text('')
        self.cbType.child.set_text('')
        self.cbCategory.child.set_text('')
        self.cbWeather.child.set_text('')
        self.cbWind.child.set_text('')
        self.entryComment.set_text('')

    # Medication callbacks
    def on_tvMedication_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return

        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_editmedication_clicked, None),
                (gtk.STOCK_REMOVE, self.on_removemedication_clicked, None)]

            menus.popup_menu(event, entries)

    def on_tvMedicationSelect_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        path, col, cellx, celly = pthinfo
        pindex = treeview.get_model()[path][2]

        if event.button == 3:
            entries = [
                (gtk.STOCK_INFO, self.show_pigeon_details, (pindex,))
                ]

            menus.popup_menu(event, entries)

    def on_addmedication_clicked(self, widget):
        self.meddialog_expanded = False
        self.clear_medicationdialog_fields()
        self.fill_medicationselect_treeview()
        comboboxes.fill_combobox(self.cbMedicationLoft,
                                 self.database.select_from_table(
                                                        self.database.LOFTS))
        self.medicationDialogMode = const.ADD
        self.medicationdialog.show()
        self.entry_meddialog_date.grab_focus()
        self.entry_meddialog_date.set_position(10)

    def on_removemedication_clicked(self, widget):
        path, focus = self.tvMedication.get_cursor()
        model, treeiter = self.selMedication.get_selected()
        pindex, ring, year = self.get_main_ring()
        medid = model[treeiter][0]

        multiple = False
        if self.database.count_medication_entries(medid) > 1:
            multiple = True
        dialog = dialogs.MedicationRemoveDialog(self.mainwindow, multiple)
        dialog.check.set_active(multiple)
        resp = dialog.run()
        if resp == gtk.RESPONSE_NO or resp == gtk.RESPONSE_DELETE_EVENT:
            dialog.destroy()
            return

        if dialog.check.get_active():
            self.database.delete_from_table(self.database.MED, medid)
        else:
            self.database.delete_medication_from_id_pindex(medid, pindex)
        dialog.destroy()

        self.lsMedication.remove(treeiter)
        if len(self.lsMedication) > 0:
            self.tvMedication.set_cursor(path)

    def on_editmedication_clicked(self, widget):
        self.meddialog_expanded = False
        self.fill_medicationselect_treeview()
        comboboxes.fill_combobox(self.cbMedicationLoft,
                                 self.database.select_from_table(
                                                        self.database.LOFTS))

        med = self.get_selected_medication()
        self.entry_meddialog_date.set_text(med[3])
        self.entry_meddialog_desc.set_text(med[4])
        self.entry_meddialog_by.set_text(med[5])
        self.entry_meddialog_med.set_text(med[6])
        self.entry_meddialog_dos.set_text(med[7])
        self.entry_meddialog_comment.set_text(med[8])
        self.chkVaccination.set_active(med[9])

        for row in self.lsMedicationSelect:
            if not row[0]: continue
            if row[2] in self.database.get_pigeons_from_medid(med[1]):
                row[1] = True

        self.medicationDialogMode = const.EDIT
        self.medicationdialog.show()
        self.entry_meddialog_date.grab_focus()
        self.entry_meddialog_date.set_position(10)

    def on_medicationdialogsave_clicked(self, widget):
        try:
            mainpindex, ring, year = self.get_main_ring()
        except TypeError:
            return

        try:
            data = self.get_medicationdata()
        except TypeError:
            return

        pigeons = [row[2] for row in self.lsMedicationSelect if row[1]]
        if self.medicationDialogMode == const.ADD:
            medid = data[0] + common.get_random_number(10)
            for pindex in pigeons:
                self.database.insert_into_table(self.database.MED,
                                                (medid, pindex, ) + data)
                # Only fill med treeview on current pigeon
                if not pindex == mainpindex: continue
                rowiter = self.lsMedication.insert(0, [medid,
                                                       data[0],
                                                       data[1]])
                self.selMedication.select_iter(rowiter)
                path = self.lsMedication.get_path(rowiter)
                self.tvMedication.scroll_to_cell(path)
        elif self.medicationDialogMode == const.EDIT:
            selection = self.tvMedication.get_selection()
            model, node = selection.get_selected()
            self.lsMedication.set(node, 1, data[0], 2, data[1])
            medid = model[node][0]

            pigeons_current = self.database.get_pigeons_from_medid(medid)
            for pindex in [pindex for pindex in pigeons
                           if pindex not in pigeons_current]:
                self.database.insert_into_table(self.database.MED,
                                                (medid, pindex, ) + data)
            for pindex in [pindex for pindex in pigeons_current
                           if pindex not in pigeons]:
                self.database.delete_medication_from_id_pindex(medid, pindex)

            data += (medid, )
            self.database.update_table(self.database.MED, data, 3, 1)

            selection.unselect_iter(node)
            selection.select_iter(node)

        self.hide_medication_dialog()

    def on_medicationdialogcancel_clicked(self, widget):
        self.hide_medication_dialog()

    def hide_medication_dialog(self, widget=None, event=None):
        self.medicationdialog.hide()
        self.meddialog_list_hide()
        return True

    def clear_medicationdialog_fields(self):
        for entry in self.get_objects_from_prefix('entry_meddialog_'):
            entry.set_text('')
        self.entry_meddialog_date.set_text(self.today)
        self.chkVaccination.set_active(False)

    def select_loft(self):
        loft = self.cbMedicationLoft.get_active_text()
        for row in self.lsMedicationSelect:
            if not row[0]: continue
            if self.parser.pigeons[row[2]].loft == loft:
                row[1] = True
            else:
                row[1] = False

    def on_chkMedicationLoft_toggled(self, widget):
        if widget.get_active():
            self.select_loft()
        else:
            for row in self.lsMedicationSelect:
                if not row[0]: continue
                row[1] = False

    def on_cbMedicationLoft_changed(self, widget):
        if self.chkMedicationLoft.get_active():
            self.select_loft()

    def on_celltoggle_toggled(self, cell, path):
        self.lsMedicationSelect[path][1] = not self.lsMedicationSelect[path][1]

    def fill_medicationselect_treeview(self):
        mainpindex, ring, year = self.get_main_ring()

        self.lsMedicationSelect.clear()

        for pindex in self.parser.pigeons:
            if not self.parser.pigeons[pindex].show:
                continue
            active = True
            if mainpindex == pindex:
                active = False

            self.lsMedicationSelect.insert(0, [active, not active, pindex,
                   self.parser.pigeons[pindex].ring,
                   self.parser.pigeons[pindex].year])

        self.lsMedicationSelect.set_sort_column_id(3, gtk.SORT_ASCENDING)
        self.lsMedicationSelect.set_sort_column_id(4, gtk.SORT_ASCENDING)

    def on_meddialogexpand_clicked(self, widget):
        if self.meddialog_expanded:
            self.meddialog_list_hide()
        else:
            self.meddialog_list_show()

    def meddialog_list_show(self):
        self.meddialog_expanded = True
        self.set_multiple_visible([self.medsep, self.medvbox], True)
        self.meddialogexpandimg.set_from_stock(gtk.STOCK_GO_BACK,
                                               gtk.ICON_SIZE_BUTTON)

    def meddialog_list_hide(self):
        self.meddialog_expanded = False
        self.set_multiple_visible([self.medsep, self.medvbox], False)
        self.meddialogexpandimg.set_from_stock(gtk.STOCK_GO_FORWARD,
                                               gtk.ICON_SIZE_BUTTON)

    # Find parent callbacks
    def on_findsire_clicked(self, widget):
        self.fill_find_treeview(const.SIRE, self.entryRing1.get_text(),
                                self.entryYear1.get_text())

    def on_finddam_clicked(self, widget):
        self.fill_find_treeview(const.DAM, self.entryRing1.get_text(),
                                self.entryYear1.get_text())

    def on_findadd_clicked(self, widget):
        model, path = self.selectionfind.get_selected()
        if not path: return

        pindex = model[path][0]
        ring = model[path][1]
        year = model[path][2]

        if int(self.parser.pigeons[pindex].sex) == const.SIRE:
            self.entrySireEdit.set_text(ring)
            self.entryYearSireEdit.set_text(year)
        else:
            self.entryDamEdit.set_text(ring)
            self.entryYearDamEdit.set_text(year)

        self.finddialog.hide()

    def on_findcancel_clicked(self, widget):
        self.finddialog.hide()

    # Calendar callbacks
    def on_calicon_press(self, widget, icon, event):
        date.CalendarPopup(widget)

    # Details dialog
    def show_pigeon_details(self, widget, pindex):
        if not pindex in self.parser.pigeons:
            return

        band, year = common.get_band_from_pindex(pindex)
        self.detailsdialog.set_title(_("Details of %s/%s") %(band, year))

        self.entryRingDet.set_text(band)
        self.entryYearDet.set_text(year)
        self.entrySexDet.set_text(self.sexDic[self.parser.pigeons[pindex].sex])
        self.entryStrainDet.set_text(self.parser.pigeons[pindex].strain)
        self.entryLoftDet.set_text(self.parser.pigeons[pindex].loft)
        self.entryColourDet.set_text(self.parser.pigeons[pindex].colour)
        self.entryNameDet.set_text(self.parser.pigeons[pindex].name)
        self.entryExtraDet1.set_text(self.parser.pigeons[pindex].extra1)
        self.entryExtraDet2.set_text(self.parser.pigeons[pindex].extra2)
        self.entryExtraDet3.set_text(self.parser.pigeons[pindex].extra3)
        self.entryExtraDet4.set_text(self.parser.pigeons[pindex].extra4)
        self.entryExtraDet5.set_text(self.parser.pigeons[pindex].extra5)
        self.entryExtraDet6.set_text(self.parser.pigeons[pindex].extra6)
        self.entrySireDet.set_text(self.parser.pigeons[pindex].sire)
        self.entryDamDet.set_text(self.parser.pigeons[pindex].dam)
        self.entryYearSireDet.set_text(self.parser.pigeons[pindex].yearsire)
        self.entryYearDamDet.set_text(self.parser.pigeons[pindex].yeardam)

        image = self.parser.pigeons[pindex].image
        if image:
            pixbuf = self.get_pigeon_thumbnail(image)
        else:
            pixbuf = self.logoPixbuf
        self.imagePigeonDet.set_from_pixbuf(pixbuf)

        status = self.parser.pigeons[pindex].active
        self.imageStatusDet.set_from_file(os.path.join(const.IMAGEDIR,
                                '%s.png' %self.pigeonStatus[status].lower()))

        self.detailsdialog.show()

    def on_closedetailsdialog_clicked(self, widget):
        self.detailsdialog.hide()

    # Statusdialog
    def on_btnStatus_clicked(self, widget):
        try:
            pindex, ring, year = self.get_main_ring()
        except TypeError:
            return

        status = self.parser.pigeons[pindex].active
        self.labelStatus.set_markup("<b>%s</b>" %_(self.pigeonStatus[status]))
        self.notebookStatus.set_current_page(status)
        self.set_status_editable(False)
        self.set_statusentry_icon(False)
        self.hboxStatus.hide()
        self.hboxStatus2.show()
        self.statusdialog.show()

    def on_btnStatus1_clicked(self, widget):
        self.set_status_editable(True)
        self.set_statusentry_icon(True)
        self.hboxStatus.show()
        self.hboxStatus2.hide()
        self.statusdialog.show()

    def on_closestatusdialog_clicked(self, widget):
        self.statusdialog.hide()

    def on_cbStatus_changed(self, widget):
        status = widget.get_active()
        self.notebookStatus.set_current_page(status)
        self.imageStatus1.set_from_file(os.path.join(const.IMAGEDIR,
                                '%s.png' %self.pigeonStatus[status].lower()))


    #
    # End of callbacks
    ##################

    def build_menubar(self):
        """
        Build menu and toolbar from the xml UI string
        """

        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_mainwindow)
        uimanager.insert_action_group(self.create_action_group(), 0)
        self.accelgroup = uimanager.get_accel_group()
        self.mainwindow.add_accel_group(self.accelgroup)

        uimanager.connect('connect-proxy', self.uimanager_connect_proxy)

        self.menubar = uimanager.get_widget('/MenuBar')
        self.toolbar = uimanager.get_widget('/Toolbar')
        widgetDic = {
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

        for key, value in widgetDic.items():
            setattr(self, key, value)

        self.set_multiple_sensitive([self.MenuEdit, self.MenuRemove,
                                     self.MenuPedigree, self.MenuAddresult,
                                     self.ToolEdit, self.ToolRemove,
                                     self.ToolPedigree], False)

        self.vbox.pack_start(self.menubar, False, False)
        self.vbox.reorder_child(self.menubar, 0)
        self.vbox.pack_start(self.toolbar, False, False)
        self.vbox.reorder_child(self.toolbar, 1)

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

    def create_action_group(self):
        """
        Create the action group for our menu and toolbar
        """

        # Custom about description for Mac OS X
        about = _("About Pigeon Planner")

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
            ("Tools", gtk.STOCK_EXECUTE, _("_Tools"), "<control>T",
                    _("Various tools"), self.menutools_activate),
            ("Preferences", gtk.STOCK_PREFERENCES, None, "<control>P",
                    _("Configure the application"), self.menupref_activate),
            ("Filter", None, _("_Filter..."), None,
                    _("Set filter options"), self.menufilter_activate),
            ("Album", None, _("_Photo Album"), None,
                    _("View the images of your pigeons"),
                    self.menualbum_activate),
            ("Addresses", None, _("Address book"), None,
                    _("View the address book"),  self.menuaddresses_activate),
            ("Calendar", None, _("Calendar"), None,
                    _("View the calendar"),  self.menucalendar_activate),
            ("Home", gtk.STOCK_HOME, _("_Website"), None,
                    _("Go to the website for more information"),
                    self.menuhome_activate),
            ("Forum", gtk.STOCK_INFO, _("Forum"), None,
                    _("Go to the forum for online help"),
                    self.menuforum_activate),
            ("Update", gtk.STOCK_CONNECT, _("Search for updates..."), None,
                    _("Search online for program updates"),
                    self.menuupdate_activate),
            ("About", gtk.STOCK_ABOUT, about if const.OSX else None, None,
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

    def uimanager_connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_property('tooltip')
        if isinstance(widget, gtk.MenuItem) and tooltip:
            widget.connect('select', self.menu_item_select, tooltip)
            widget.connect('deselect', self.menu_item_deselect)

    def menu_item_select(self, menuitem, tooltip):
        self.statusbar.push(-1, tooltip)

    def menu_item_deselect(self, menuitem):
        self.statusbar.pop(-1)

    def build_treeview(self):
        """
        Build the main treeview
        """

        self.selection = self.treeview.get_selection()
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.selection_changed_id = self.selection.connect('changed',
                                                           self.selection_changed)
        self.set_treeview_columns()

    def set_treeview_columns(self):
        self.columns = {2: self.options.optionList.colname,
                        3: self.options.optionList.colcolour,
                        4: self.options.optionList.colsex,
                        5: self.options.optionList.colloft,
                        6: self.options.optionList.colstrain}

        for key, value in self.columns.items():
            self.treeview.get_column(key).set_visible(value)

    def build_treeviews(self):
        """
        Build the remaining treeviews
        """

        self.selectionfind = self.tvFind.get_selection()
        self.selBrothers = self.tvBrothers.get_selection()
        self.selHalfBrothers = self.tvHalfBrothers.get_selection()
        self.selOffspring = self.tvOffspring.get_selection()
        self.selMedication = self.tvMedication.get_selection()
        self.selMedication.connect('changed', self.selectionmedication_changed)
        self.selResults = self.tvResults.get_selection()
        self.selResults.connect('changed', self.selectionresult_changed)

    def pigeon_filter(self, pindex):
        if self.chkFilterSex.get_active():
            if not self.parser.pigeons[pindex].sex == \
                   self.cbFilterSex.get_active_text():
                return False

        if self.chkFilterColours.get_active():
            if not self.parser.pigeons[pindex].colour == \
                   self.cbFilterColour.get_active_text():
                return False

        if self.chkFilterStrains.get_active():
            if not self.parser.pigeons[pindex].strain == \
                   self.cbFilterStrain.get_active_text():
                return False

        if self.chkFilterLofts.get_active():
            if not self.parser.pigeons[pindex].loft == \
                   self.cbFilterLoft.get_active_text():
                return False

        if self.chkFilterStatus.get_active():
            if not self.parser.pigeons[pindex].active == \
                   self.cbFilterStatus.get_active():
                return False

        return True

    def fill_treeview(self, path=0, search_results=None, filter_active=False):
        """
        Fill the main treeview with pigeons.

        @param path: The path to set the cursor
        @param search_results: A pigeonlist to show
        @param filter_active: If the filter is active
        """

        self.liststore.clear()

        for pindex in search_results if search_results is not None \
                                     else self.parser.pigeons:
            if not self.parser.pigeons[pindex].show: continue
            if filter_active and not self.pigeon_filter(pindex): continue

            self.liststore.insert(0, [pindex,
                   self.parser.pigeons[pindex].ring,
                   self.parser.pigeons[pindex].year,
                   self.parser.pigeons[pindex].name,
                   self.parser.pigeons[pindex].colour,
                   self.sexDic[self.parser.pigeons[pindex].sex],
                   self.parser.pigeons[pindex].loft,
                   self.parser.pigeons[pindex].strain])

        if len(self.liststore) > 0:
            self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
            self.liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)
            if not path:
                path = 0
            self.selection.select_path(path)
            self.treeview.grab_focus()
        else:
            self.imagePigeon.set_from_pixbuf(self.logoPixbuf)
            self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)
            self.labelImgPath.set_text('')

    def selectionresult_changed(self, selection):
        """
        Set the remove and edit buttons sensitive or insensitive 
        depending wether a result is selected or not.
        """

        model, path = selection.get_selected()

        widgets = [self.removeresult, self.editresult]
        if path:
            self.set_multiple_sensitive(widgets, True)
        else:
            self.set_multiple_sensitive(widgets, False)

    def selectionmedication_changed(self, selection):
        model, path = selection.get_selected()

        widgets = [self.removemedication, self.editmedication]
        if path:
            self.set_multiple_sensitive(widgets, True)
        else:
            self.set_multiple_sensitive(widgets, False)

            for entry in self.get_objects_from_prefix('entry_med_'):
                entry.set_text('')
            self.check_vaccination.set_active(False)
            return

        data = self.get_selected_medication()
        self.entry_med_date.set_text(data[3])
        self.entry_med_desc.set_text(data[4])
        self.entry_med_by.set_text(data[5])
        self.entry_med_med.set_text(data[6])
        self.entry_med_dosage.set_text(data[7])
        self.entry_med_comment.set_text(data[8])
        self.check_vaccination.set_active(data[9])

    def clear_pigeon_data(self, widgets):
        self.set_multiple_sensitive(widgets, False)
        self.imageStatus.clear()
        self.imageStatus1.clear()
        self.imagePigeon.set_from_pixbuf(self.logoPixbuf)
        self.labelImgPath.set_text('')
        self.draw_empty_pedigree()
        self.lsMedication.clear()
        self.lsResult.clear()

    def selection_changed(self, selection):
        """
        Get all the data/info from the selected pigeon
        """

        n_rows_selected = selection.count_selected_rows()
        model, tree_iters = selection.get_selected_rows()

        self.empty_entryboxes()

        widgets = [self.ToolEdit, self.ToolPedigree, self.MenuEdit,
                   self.MenuPedigree, self.MenuAddresult, self.addresult,
                   self.ToolRemove, self.MenuRemove]
        if n_rows_selected == 1:
            tree_iter = self.liststore.get_iter(tree_iters[0])
            self.set_multiple_sensitive(widgets, True)
        elif n_rows_selected == 0:
            self.clear_pigeon_data(widgets)
            return
        elif n_rows_selected > 1:
            # Disable everything except th remove buttons
            self.clear_pigeon_data(widgets[:-2])
            return

        pindex = model.get_value(tree_iter, 0)

        ring     = self.parser.pigeons[pindex].ring
        year     = self.parser.pigeons[pindex].year
        sex      = self.parser.pigeons[pindex].sex
        strain   = self.parser.pigeons[pindex].strain
        loft     = self.parser.pigeons[pindex].loft
        extra1   = self.parser.pigeons[pindex].extra1
        extra2   = self.parser.pigeons[pindex].extra2
        extra3   = self.parser.pigeons[pindex].extra3
        extra4   = self.parser.pigeons[pindex].extra4
        extra5   = self.parser.pigeons[pindex].extra5
        extra6   = self.parser.pigeons[pindex].extra6
        colour   = self.parser.pigeons[pindex].colour
        name     = self.parser.pigeons[pindex].name
        sire     = self.parser.pigeons[pindex].sire
        yearsire = self.parser.pigeons[pindex].yearsire
        dam      = self.parser.pigeons[pindex].dam
        yeardam  = self.parser.pigeons[pindex].yeardam
        status   = self.parser.pigeons[pindex].active
        image    = self.parser.pigeons[pindex].image

        self.entryRing.set_text(ring)
        self.entryYear.set_text(year)
        self.entrySexKey.set_text(sex)
        self.entrySex.set_text(self.sexDic[sex])
        self.entryStrain.set_text(strain)
        self.entryLoft.set_text(loft)
        self.entryColour.set_text(colour)
        self.entryName.set_text(name)
        self.entryExtra1.set_text(extra1)
        self.entryExtra2.set_text(extra2)
        self.entryExtra3.set_text(extra3)
        self.entryExtra4.set_text(extra4)
        self.entryExtra5.set_text(extra5)
        self.entryExtra6.set_text(extra6)
        self.entrySire.set_text(sire)
        self.entryDam.set_text(dam)
        self.entryYearSire.set_text(yearsire)
        self.entryYearDam.set_text(yeardam)

        if image:
            pixbuf = self.get_pigeon_thumbnail(image)
        else:
            pixbuf = self.logoPixbuf
            self.labelImgPath.set_text('')

        self.imagePigeon.set_from_pixbuf(pixbuf)
        self.imagePigeon1.set_from_pixbuf(pixbuf)

        self.imageStatus.set_from_file(os.path.join(const.IMAGEDIR,
                                '%s.png' %self.pigeonStatus[status].lower()))
        self.imageStatus1.set_from_file(os.path.join(const.IMAGEDIR,
                                '%s.png' %self.pigeonStatus[status].lower()))

        self.pedigree.draw_pedigree(self.parser.pigeons,
                                    [self.tableSire, self.tableDam], pindex)

        self.find_direct_relatives(pindex, sire, dam)
        self.find_half_relatives(pindex, sire, yearsire, dam, yeardam)
        self.find_offspring(pindex, sire, dam)

        self.get_results(pindex)
        self.labelPigeonResult.set_text("%s / %s" %(ring, year))

        self.get_medication(pindex)

        self.fill_status(pindex, status)

    def fill_status(self, pindex, status):
        """
        Fill the correct statusdetails for the selected pigeon

        @param pindex: the selected pigeon
        @param status: the status
        """

        if status == const.ACTIVE:
            return
        elif status == const.DEAD:
            data = self.database.get_dead_data(pindex)
            if data:
                self.entryDeadDate.set_text(data[0])
                self.textDeadInfo.get_buffer().set_text(data[1])
        elif status == const.SOLD:
            data = self.database.get_sold_data(pindex)
            if data:
                self.entrySoldDate.set_text(data[1])
                self.entrySoldBuyer.set_text(data[0])
                self.textSoldInfo.get_buffer().set_text(data[2])
        elif status == const.LOST:
            data = self.database.get_lost_data(pindex)
            if data:
                self.entryLostDate.set_text(data[1])
                self.entryLostPoint.set_text(data[0])
                self.textLostInfo.get_buffer().set_text(data[2])

    def get_results(self, pindex):
        """
        Get all results of selected pigeon

        @param pindex: the selected pigeon
        """

        self.tvResults.freeze_child_notify()
        self.tvResults.set_model(None)

        self.lsResult.set_default_sort_func(lambda *args: -1) 
        self.lsResult.set_sort_column_id(-1, gtk.SORT_ASCENDING)

        self.lsResult.clear()

        for result in self.database.get_pigeon_results(pindex):
            place = result[4]
            out = result[5]
            cof = common.calculate_coefficient(place, out)

            self.lsResult.insert(0, [result[0], result[2], result[3],
                                    place, out, cof,
                                    result[6], result[7], result[8],
                                    result[9], result[10], result[15]])

        self.lsResult.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.tvResults.set_model(self.lsResult)
        self.tvResults.thaw_child_notify()

    def get_medication(self, pindex):
        self.lsMedication.clear()

        for med in self.database.get_pigeon_medication(pindex):
            self.lsMedication.insert(0, [med[1], med[3], med[4]])

        self.lsMedication.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def find_direct_relatives(self, pindex, sire, dam):
        """
        Search all brothers and sisters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        """

        self.lsBrothers.clear()

        if not sire or not dam: return

        for pigeon in self.parser.pigeons:
            if sire == self.parser.pigeons[pigeon].sire and\
               dam == self.parser.pigeons[pigeon].dam and not\
               pigeon == pindex:

                sex = self.parser.pigeons[pigeon].sex
                self.lsBrothers.insert(0, [pigeon,
                                           self.parser.pigeons[pigeon].ring,
                                           self.parser.pigeons[pigeon].year,
                                           sex, self.sexImgs[sex]])

        self.lsBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsBrothers.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def find_half_relatives(self, pindex, sire, yearsire, dam, yeardam):
        """
        Search all halfbrothers and sisters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param yearsire: year of the sire of selected pigeon
        @param dam: dam of selected pigeon
        @param yeardam: year of the dam of selected pigeon
        """

        self.lsHalfBrothers.clear()

        for pigeon in self.parser.pigeons:
            sex = self.parser.pigeons[pigeon].sex
            if sire:
                if sire == self.parser.pigeons[pigeon].sire\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.insert(0, [pigeon,
                                            self.parser.pigeons[pigeon].ring,
                                            self.parser.pigeons[pigeon].year,
                                            sire+'/'+yearsire[2:],
                                            sex, self.sexImgs[sex]])

            if dam:
                if dam == self.parser.pigeons[pigeon].dam\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.insert(0, [pigeon,
                                            self.parser.pigeons[pigeon].ring,
                                            self.parser.pigeons[pigeon].year,
                                            dam+'/'+yeardam[2:],
                                            sex, self.sexImgs[sex]])

        self.lsHalfBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsHalfBrothers.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def find_offspring(self, pindex, sire, dam):
        """
        Find all youngsters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        """

        self.lsOffspring.clear()

        for pigeon in self.parser.pigeons:
            ring = self.parser.pigeons[pindex].ring
            if self.parser.pigeons[pigeon].sire == ring or \
               self.parser.pigeons[pigeon].dam == ring:

                sex = self.parser.pigeons[pigeon].sex
                self.lsOffspring.insert(0, [pigeon,
                                            self.parser.pigeons[pigeon].ring,
                                            self.parser.pigeons[pigeon].year,
                                            sex, self.sexImgs[sex]])

        self.lsOffspring.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsOffspring.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def add_edit_start(self, operation):
        """
        Do all the necessary things to start editing or adding.

        @param operation: One of the ADD or EDIT constants
        """

        if operation == const.ADD:
            # Clear the pedigree
            self.draw_empty_pedigree()

        self.operation = operation

        self.set_multiple_sensitive([self.toolbar, self.notebook,
                                     self.treeview, self.vboxButtons], False)
        self.detailbook.set_current_page(1)
        self.mainwindow.remove_accel_group(self.accelgroup)
        self.mainwindow.add_accel_group(self.cancelEscAG)

        self.entryRing1.grab_focus()
        self.entryRing1.set_position(-1)
        self.save.grab_default()

    def add_edit_finish(self, *args):
        """
        Do all the necessary things to finish editing or adding.
        """

        self.parser.get_pigeons()
        self.count_active_pigeons()
        if self.changedRowIter and self.operation == const.ADD:
            self.selection.unselect_all()
            self.selection.select_iter(self.changedRowIter)
            path = self.liststore.get_path(self.changedRowIter)
            self.treeview.scroll_to_cell(path)
        if self.operation == const.EDIT:
            self.selection.emit('changed')

        self.set_multiple_sensitive([self.toolbar, self.notebook,
                                     self.treeview, self.vboxButtons], True)
        self.detailbook.set_current_page(0)
        self.mainwindow.remove_accel_group(self.cancelEscAG)
        self.mainwindow.add_accel_group(self.accelgroup)
        self.treeview.grab_focus()

    def get_add_edit_info(self):
        """
        Return a tuple containig info about the editable widgets.
        """

        infoTuple = (self.entryRing1.get_text(),
                     self.entryYear1.get_text(),
                     self.cbsex.get_active_text(),
                     1,
                     self.cbStatus.get_active(),
                     self.cbColour.child.get_text(),
                     self.entryName1.get_text(),
                     self.cbStrain.child.get_text(),
                     self.cbLoft.child.get_text(),
                     self.labelImgPath.get_text(),
                     self.entrySireEdit.get_text(),
                     self.entryYearSireEdit.get_text(),
                     self.entryDamEdit.get_text(),
                     self.entryYearDamEdit.get_text(),
                     self.entryExtra11.get_text(),
                     self.entryExtra21.get_text(),
                     self.entryExtra31.get_text(),
                     self.entryExtra41.get_text(),
                     self.entryExtra51.get_text(),
                     self.entryExtra61.get_text())

        return infoTuple

    def get_status_info(self):
        bffr = self.textDeadInfo.get_buffer()
        dead = (self.entryDeadDate.get_text(),
                bffr.get_text(*bffr.get_bounds()))

        bffr = self.textSoldInfo.get_buffer()
        sold = (self.entrySoldBuyer.get_text(),
                self.entrySoldDate.get_text(),
                bffr.get_text(*bffr.get_bounds()))

        bffr = self.textLostInfo.get_buffer()
        lost = (self.entryLostPoint.get_text(),
                self.entryLostDate.get_text(),
                bffr.get_text(*bffr.get_bounds()))

        return dead, sold, lost

    def write_new_data(self):
        """
        Write new data to the pigeon
        """

        pindex, ring, year = self.get_main_ring()
        ptuple = (pindex,)
        infoTuple = self.get_add_edit_info()
        pindex_new = infoTuple[0] + infoTuple[1]
        data = (pindex_new, ) + infoTuple + ptuple

        if self.database.has_results(pindex):
            self.database.update_table(self.database.RESULTS,
                                       (pindex_new, pindex), 1, 1)
        if self.database.has_medication(pindex):
            self.database.update_table(self.database.MED,
                                       (pindex_new, pindex), 2, 2)

        self.database.update_table(self.database.PIGEONS, data, 1, 1)

        image = infoTuple[9]
        if image != self.preEditImage:
            if self.preEditImage:
                os.remove(common.get_thumb_path(self.preEditImage))
            if image:
                common.image_to_thumb(image)

        status = self.cbStatus.get_active()
        old_status = self.parser.pigeons[pindex].active
        if status != old_status:
            if old_status != const.ACTIVE:
                self.database.delete_from_table(self.pigeonStatus[old_status],
                                                pindex)

            if status == const.DEAD:
                self.database.insert_into_table(self.database.DEAD,
                                        ptuple + self.get_status_info()[0])
            elif status == const.SOLD:
                self.database.insert_into_table(self.database.SOLD,
                                        ptuple + self.get_status_info()[1])
            elif status == const.LOST:
                self.database.insert_into_table(self.database.LOST,
                                        ptuple + self.get_status_info()[2])
        else:
            if status == const.DEAD:
                self.database.update_table(self.database.DEAD,
                                           self.get_status_info()[0] + ptuple,
                                           2, 1)
            elif status == const.SOLD:
                self.database.update_table(self.database.SOLD,
                                           self.get_status_info()[1] + ptuple,
                                           2, 1)
            elif status == const.LOST:
                self.database.update_table(self.database.LOST,
                                           self.get_status_info()[2] + ptuple,
                                           2, 1)

        self.update_data(infoTuple)
        self.liststore.set(self.treeIterEdit,
                                0, pindex_new,
                                1, infoTuple[0],
                                2, infoTuple[1],
                                3, infoTuple[6],
                                4, infoTuple[5],
                                5, self.sexDic[infoTuple[2]],
                                6, infoTuple[8],
                                7, infoTuple[7])

    def write_new_pigeon(self):
        """
        Write the new pigeon to the database
        """

        infoTuple = self.get_add_edit_info()
        pindex = infoTuple[0] + infoTuple[1]
        pindexTuple = (pindex,)
        pindexTuple += infoTuple

        newAdd = True
        if self.database.has_pigeon(pindex):
            if self.parser.pigeons[pindex].show == 1:
                d = dialogs.MessageDialog(const.WARNING,
                                          messages.MSG_OVERWRITE_PIGEON,
                                          self.mainwindow)
                if not d.yes:
                    return
            else:
                d = dialogs.MessageDialog(const.WARNING,
                                          messages.MSG_SHOW_PIGEON,
                                          self.mainwindow)
                if d.yes:
                    self.database.update_table(self.database.PIGEONS,
                                               (1, pindex), 5, 1)
                    newAdd = False
                else:
                    return

        if newAdd:
            self.database.insert_into_table(self.database.PIGEONS, pindexTuple)

            if infoTuple[9]:
                common.image_to_thumb(infoTuple[9])

            status = self.cbStatus.get_active()
            if status == const.DEAD:
                self.database.insert_into_table(self.database.DEAD,
                                        (pindex,) + self.get_status_info()[0])
            elif status == const.SOLD:
                self.database.insert_into_table(self.database.SOLD,
                                        (pindex,) + self.get_status_info()[1])
            elif status == const.LOST:
                self.database.insert_into_table(self.database.LOST,
                                        (pindex,) + self.get_status_info()[2])

            self.update_data(infoTuple)

        self.changedRowIter = self.liststore.insert(0, [pindex,
                                                     infoTuple[0],
                                                     infoTuple[1],
                                                     infoTuple[6],
                                                     infoTuple[5],
                                                     self.sexDic[infoTuple[2]],
                                                     infoTuple[8],
                                                     infoTuple[7]])

        common.add_statusbar_message(self.statusbar,
                _("Pigeon %s/%s has been added") %(infoTuple[0], infoTuple[1]))

    def update_data(self, infoTuple):
        """
        Update the data
        """

        colour = infoTuple[5]
        if colour:
            self.database.insert_into_table(self.database.COLOURS, (colour, ))
            comboboxes.fill_combobox(self.cbColour,
                                     self.database.select_from_table(
                                                        self.database.COLOURS))

        strain = infoTuple[7]
        if strain:
            self.database.insert_into_table(self.database.STRAINS, (strain, ))
            comboboxes.fill_combobox(self.cbStrain,
                                     self.database.select_from_table(
                                                        self.database.STRAINS))

        loft = infoTuple[8]
        if loft:
            self.database.insert_into_table(self.database.LOFTS, (loft, ))
            comboboxes.fill_combobox(self.cbLoft,
                                     self.database.select_from_table(
                                                        self.database.LOFTS))

    def draw_empty_pedigree(self):
        self.pedigree.draw_pedigree(self.parser.pigeons,
                                    [self.tableSire, self.tableDam])

    def empty_entryboxes(self):
        """
        Empty all entryboxes and textviews
        """

        for widget in self.get_objects_from_prefix("entry"):
            if not self.get_object_name(widget) == 'entryDate':
                widget.set_text('')

        for widget in self.get_objects_from_prefix("text"):
            widget.get_buffer().set_text('')

    def set_status_editable(self, value):
        self.entryDeadDate.set_editable(value)
        self.textDeadInfo.set_editable(value)

        self.entrySoldDate.set_editable(value)
        self.entrySoldBuyer.set_editable(value)
        self.textSoldInfo.set_editable(value)

        self.entryLostDate.set_editable(value)
        self.entryLostPoint.set_editable(value)
        self.textLostInfo.set_editable(value)

    def set_statusentry_icon(self, value):
        if value:
            pb = gtk.gdk.pixbuf_new_from_file(os.path.join(const.IMAGEDIR,
                                                       'icon_calendar.png'))
        else:
            pb = None

        self.entryDeadDate.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pb)
        self.entrySoldDate.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pb)
        self.entryLostDate.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pb)

    def set_default_image(self, widget=None):
        self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)
        self.labelImgPath.set_text('')

    def open_filedialog(self, widget=None):
        """
        Set a preview image and show the Filechooser dialog
        """

        preview = gtk.Image()
        self.filedialog.set_preview_widget(preview)
        self.filedialog.add_filter(filefilters.ImageFilter())
        image_folder = glib.get_user_special_dir(glib.USER_DIRECTORY_PICTURES)
        self.filedialog.set_current_folder(image_folder)
        self.filedialog.show()

    def get_pigeoninfo(self):
        """
        Get a dictionary of the current pigeons details
        """

        pindex, ring, year = self.get_main_ring()

        pigeoninfo = {}
        pigeoninfo['pindex'] = pindex
        pigeoninfo['ring'] = ring
        pigeoninfo['year'] = year
        pigeoninfo['sex'] = self.sexDic[self.parser.pigeons[pindex].sex]
        pigeoninfo['colour'] = self.parser.pigeons[pindex].colour
        pigeoninfo['name'] = self.parser.pigeons[pindex].name
        pigeoninfo['image'] = self.parser.pigeons[pindex].image
        pigeoninfo['extra1'] = self.parser.pigeons[pindex].extra1
        pigeoninfo['extra2'] = self.parser.pigeons[pindex].extra2
        pigeoninfo['extra3'] = self.parser.pigeons[pindex].extra3
        pigeoninfo['extra4'] = self.parser.pigeons[pindex].extra4
        pigeoninfo['extra5'] = self.parser.pigeons[pindex].extra5
        pigeoninfo['extra6'] = self.parser.pigeons[pindex].extra6

        return pigeoninfo

    def get_main_ring(self):
        """
        Return the pindex, ring and year of selected pigeon
        """

        model, paths = self.selection.get_selected_rows()
        if len(paths) < 1:
            return
        elif len(paths) == 1:
            path = paths[0]
            return model[path][0], model[path][1], model[path][2]
        elif len(paths) > 1:
            return [(model[path][0], model[path][1], model[path][2])
                    for path in paths]

    def search_pigeon(self, widget, pindex):
        """
        Set the cursor on the given pigeon

        @param widget: Only given when selected through menu
        @param pindex: The index of the pigeon to search
        """

        for item in self.liststore:
            if self.liststore.get_value(item.iter, 0) == pindex:
                self.treeview.set_cursor(item.path)
                return True

        return False

    def get_resultdata(self):
        """
        Get the values from the result widgets
        """

        date = self.entryDate.get_text()
        point = self.cbRacepoint.child.get_text()
        place = self.spinPlaced.get_value_as_int()
        out = self.spinOutof.get_value_as_int()
        sector = self.cbSector.child.get_text()
        ftype = self.cbType.child.get_text()
        category = self.cbCategory.child.get_text()
        weather = self.cbWeather.child.get_text()
        wind = self.cbWind.child.get_text()
        comment = self.entryComment.get_text()

        if not date or not point or not place or not out:
            dialogs.MessageDialog(const.ERROR, messages.MSG_EMPTY_DATA,
                                  self.resultdialog)
            return False

        try:
            datetime.datetime.strptime(date, const.DATE_FORMAT)
        except ValueError:
            dialogs.MessageDialog(const.ERROR, messages.MSG_INVALID_FORMAT,
                                  self.resultdialog)
            return False

        return (date, point, place, out, sector, ftype, category,
                weather, wind, comment)

    def get_selected_result(self):
        """
        Return the data from the selected result
        """

        model, tIter = self.selResults.get_selected()
        if not tIter: return
        
        return list(model[tIter])

    def get_selected_medication(self):
        model, tIter = self.selMedication.get_selected()
        if not tIter: return

        return self.database.get_medication_from_id(model[tIter][0])

    def get_medicationdata(self):
        return (
            self.entry_meddialog_date.get_text(),
            self.entry_meddialog_desc.get_text(),
            self.entry_meddialog_by.get_text(),
            self.entry_meddialog_med.get_text(),
            self.entry_meddialog_dos.get_text(),
            self.entry_meddialog_comment.get_text(),
            int(self.chkVaccination.get_active())
                )

    def fill_find_treeview(self, sex, band, year):
        """
        Fill the 'find'-treeview with pigeons of the wanted sex

        @param sex: sex of the pigeons
        @param band: band of the pigeon
        @param year: year of the pigeon
        """

        self.lsFind.clear()

        for pigeon in self.parser.pigeons:
            if str(sex) == self.parser.pigeons[pigeon].sex and \
               band != self.parser.pigeons[pigeon].ring and \
               year >= self.parser.pigeons[pigeon].year:
                self.lsFind.insert(0, [pigeon,
                                    self.parser.pigeons[pigeon].ring,
                                    self.parser.pigeons[pigeon].year,
                                    self.parser.pigeons[pigeon].name])

        if len(self.lsFind) > 0:
            self.lsFind.set_sort_column_id(1, gtk.SORT_ASCENDING)
            self.lsFind.set_sort_column_id(2, gtk.SORT_ASCENDING)
            self.tvFind.set_cursor(0)

        self.finddialog.show()

    def count_active_pigeons(self):
        """
        Count all active pigeons and set the statistics labels
        """

        total, cocks, hens, ybirds = common.count_active_pigeons(self.database)

        self.labelStatTotal.set_markup("<b>%i</b>" %total)
        self.labelStatCocks.set_markup("<b>%i</b>" %cocks)
        self.labelStatHens.set_markup("<b>%i</b>" %hens)
        self.labelStatYoung.set_markup("<b>%i</b>" %ybirds)

    def build_thumbnails(self):
        for pigeon in self.parser.pigeons:
            img_path = self.parser.pigeons[pigeon].image
            if img_path != '':
                common.image_to_thumb(img_path)

    def get_pigeon_thumbnail(self, image):
        try:
            thumb = common.get_thumb_path(image)
            pixbuf = gtk.gdk.pixbuf_new_from_file(thumb)
            self.labelImgPath.set_text(image)
        except gobject.GError:
            # Something went wrong with the thumbnail filenames.
            # Delete all and rebuild.
            logger.warning("Thumb not found, rebuild complete list.")
            for img_thumb in os.listdir(const.THUMBDIR):
                os.remove(os.path.join(const.THUMBDIR, img_thumb))
            self.build_thumbnails()
            pixbuf = self.get_pigeon_thumbnail(image)

        return pixbuf

