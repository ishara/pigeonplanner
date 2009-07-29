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
import datetime
import webbrowser

import gtk
import gtk.glade

import Const
import Widgets
import Options
import Database
import ToolsWindow
import PigeonParser
import ResultWindow
import PedigreeWindow
import Checks as check
from Pedigree import DrawPedigree


class MainWindow:

    def __init__(self):

        self.gladefile = Const.GLADEDIR + "MainWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_save_clicked'          : self.save_clicked,
                      'on_cancel_clicked'        : self.cancel_clicked,
                      'on_btnadd_clicked'        : self.btnadd_clicked,
                      'on_sbdetail_clicked'      : self.sbdetail_clicked,
                      'on_goto_clicked'          : self.goto_clicked,
                      'on_addresult_clicked'     : self.addresult_clicked,
                      'on_removeresult_clicked'  : self.removeresult_clicked,
                      'on_editresult_clicked'    : self.editresult_clicked,
                      'on_editapply_clicked'     : self.editapply_clicked,
                      'on_resultcancel_clicked'  : self.resultcancel_clicked,
                      'on_allresults_clicked'    : self.allresults_clicked,
                      'on_filedialog_selection'  : self.filedialog_selection,
                      'on_fcopen_clicked'        : self.fcopen_clicked,
                      'on_fccancel_clicked'      : self.fccancel_clicked,
                      'on_rangeadd_clicked'      : self.rangeadd_clicked,
                      'on_rangecancel_clicked'   : self.rangecancel_clicked,
                      'on_eventbox_press'        : self.eventbox_press,
                      'on_eventimage_press'      : self.eventimage_press,
                      'on_treeview_press'        : self.treeview_press,
                      'on_tvResults_press'       : self.tvResults_press,
                      'on_tvBrothers_press'      : self.tvBrothers_press,
                      'on_tvHalfBrothers_press'  : self.tvHalfBrothers_press,
                      'on_tvOffspring_press'     : self.tvOffspring_press,
                      'on_findsire_clicked'      : self.findsire_clicked,
                      'on_finddam_clicked'       : self.finddam_clicked,
                      'on_findcancel_clicked'    : self.findcancel_clicked,
                      'on_findadd_clicked'       : self.findadd_clicked,
                      'on_calbutton_clicked'     : self.calbutton_clicked,
                      'on_day_selected'          : self.day_selected,
                      'on_day_double_clicked'    : self.day_double_clicked,
                      'on_button_top_clicked'    : self.button_top_clicked,
                      'on_button_up_clicked'     : self.button_up_clicked,
                      'on_button_down_clicked'   : self.button_down_clicked,
                      'on_button_bottom_clicked' : self.button_bottom_clicked,
                      'on_spinPlaced_changed'    : self.spinPlaced_changed,
                      'on_rangedialog_delete'    : self.dialog_delete,
                      'on_finddialog_delete'     : self.dialog_delete,
                      'on_removedialog_delete'   : self.dialog_delete,
                      'on_filedialog_delete'     : self.dialog_delete,
                      'on_main_destroy'          : self.quit_program}
        self.wTree.signal_autoconnect(signalDic)

        for widget in self.wTree.get_widget_prefix(''):
            name = widget.get_name()
            setattr(self, name, widget)

        self.main.set_title("%s %s" %(Const.NAME, Const.VERSION))

        self.date_format = '%Y-%m-%d'
        self.imageToAdd = ''
        self.imageDeleted = False
        self.beforeEditPath = 0
        self.blockMenuCallback = False
        self.editResultMode = False
        self.columnValueDic = {'0': _("Colour"), '1': _("Sex")}
        self.sexDic = {'0': _('cock'), '1': _('hen'), '2': _('young bird')}
        self.entrysToCheck = { 'ring': self.entryRing1, 'year': self.entryYear1,
                               'sire': self.entrySireEdit, 'yearsire': self.entryYearSireEdit,
                               'dam': self.entryDamEdit, 'yeardam': self.entryYearDamEdit}

        self.entrySexKey = gtk.Entry()
        self.hbox4.pack_start(self.entrySexKey)

        self.options = Options.GetOptions()
        self.database = Database.DatabaseOperations()
        self.parser = PigeonParser.PigeonParser()
        self.parser.get_pigeons()
        self.pedigree = DrawPedigree([self.tableSire, self.tableDam],
                                      button=self.goto, pigeons=self.parser.pigeons)
        self.pedigree.draw_pedigree()
        self.build_menubar()
        self.build_treeview()
        self.build_treeviews()
        self.fill_treeview()
        self.create_sexcombos()
        self.set_filefilter()
        for item in [self.cbRacepoint, self.cbSector, self.cbColour, self.cbStrain, self.cbLoft]:
            Widgets.set_completion(item)

        if self.options.optionList.arrows:
            self.alignarrows.show()

            self.blockMenuCallback = True
            self.MenuArrows.set_active(True)
            self.blockMenuCallback = False

        if self.options.optionList.toolbar:
            self.toolbar.show()

            self.blockMenuCallback = True
            self.MenuToolbar.set_active(True)
            self.blockMenuCallback = False

        if self.options.optionList.statusbar:
            self.statusbar.show()

            self.blockMenuCallback = True
            self.MenuStatusbar.set_active(True)
            self.blockMenuCallback = False

        self.listdata = {self.cbSector: self.database.get_all_sectors(), \
                         self.cbRacepoint: self.database.get_all_racepoints(), \
                         self.cbColour: self.database.get_all_colours(), \
                         self.cbStrain: self.database.get_all_strains(), \
                         self.cbLoft: self.database.get_all_lofts()}
        for key in self.listdata.keys():
            Widgets.fill_list(key, self.listdata[key])

        self.logoPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(Const.IMAGEDIR + 'icon_logo.png', 75, 75)

        gtk.about_dialog_set_url_hook(self.url_hook)
        gtk.about_dialog_set_email_hook(self.email_hook)

    def quit_program(self, widget=None, event=None):
        gtk.main_quit()

    def dialog_delete(self, widget, event):
        widget.hide()
        return True

    # Menu callbacks
    def menuclose_activate(self, widget):
        self.quit_program()

    def menuadd_activate(self, widget):
        self.empty_entryboxes()
        self.cbColour.child.set_text('')
        self.cbStrain.child.set_text('')
        self.cbLoft.child.set_text('')
        self.cbsex.set_active(0)

        self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)

        self.add_edit_start('add')

    def menuaddrange_activate(self, widget):
        self.entryRangeFrom.set_text('')
        self.entryRangeTo.set_text('')
        self.entryRangeYear.set_text('')
        self.cbRangeSex.set_active(2)
        self.rangedialog.show()

    def menuedit_activate(self, widget):
        self.entryRing1.set_text(self.entryRing.get_text())
        self.entryYear1.set_text(self.entryYear.get_text())
        self.entryName1.set_text(self.entryName.get_text())
        self.extra11.set_text(self.extra1.get_text())
        self.extra21.set_text(self.extra2.get_text())
        self.extra31.set_text(self.extra3.get_text())
        self.extra41.set_text(self.extra4.get_text())
        self.extra51.set_text(self.extra5.get_text())
        self.extra61.set_text(self.extra6.get_text())
        self.cbColour.child.set_text(self.entryColour.get_text())
        self.cbStrain.child.set_text(self.entryStrain.get_text())
        self.cbLoft.child.set_text(self.entryLoft.get_text())
        self.entrySireEdit.set_text(self.entrySire.get_text())
        self.entryYearSireEdit.set_text(self.entryYearSire.get_text())
        self.entryDamEdit.set_text(self.entryDam.get_text())
        self.entryYearDamEdit.set_text(self.entryYearDam.get_text())

        self.cbsex.set_active(int(self.entrySexKey.get_text()))

        self.add_edit_start('edit')

    def menuremove_activate(self, widget):
        pindex, ring, year = self.get_main_ring()

        model, tIter = self.selection.get_selected()
        path, focus = self.treeview.get_cursor()

        wTree = gtk.glade.XML(self.gladefile, 'removedialog')
        dialog = wTree.get_widget('removedialog')
        label = wTree.get_widget('labelPigeon')
        chkKeep = wTree.get_widget('chkKeep')
        chkResults = wTree.get_widget('chkResults')
        dialog.set_transient_for(self.main)
        label.set_text(ring + ' / ' + year)
        answer = dialog.run()
        if answer == 2:
            if chkKeep.get_active():
                self.database.show_pigeon(pindex, 0)
            else:
                self.database.delete_pigeon(pindex)
                self.parser.get_pigeons()

            if not chkResults.get_active():
                self.database.delete_result_from_band(pindex)

            self.liststore.remove(tIter)

        dialog.destroy()

        if len(self.liststore) > 0:
            self.treeview.set_cursor(path)

    def menupedigree_activate(self, widget):
        self.sbdetail_clicked(None)

    def menuaddresult_activate(self, widget):
        self.notebook.set_current_page(2)

    def menufilter_action(self, action, widget):
        value = widget.get_current_value()

        if value == 0:
            self.fill_treeview()
        elif value == 1:
            self.fill_treeview('0')
        elif value == 2:
            self.fill_treeview('1')
        elif value == 3:
            self.fill_treeview('2')

    def menutools_activate(self, widget):
        ToolsWindow.ToolsWindow(self)

    def menupref_activate(self, widget):
        Options.OptionsDialog(self)

    def menuarrows_toggled(self, widget):
        if self.blockMenuCallback: return

        if widget.get_active():
            self.alignarrows.show()
            self.options.set_option('Options', 'arrows', 'True')
        else:
            self.alignarrows.hide()
            self.options.set_option('Options', 'arrows', 'False')

    def menutoolbar_toggled(self, widget):
        if self.blockMenuCallback: return

        if widget.get_active():
            self.toolbar.show()
            self.options.set_option('Options', 'toolbar', 'True')
        else:
            self.toolbar.hide()
            self.options.set_option('Options', 'toolbar', 'False')

    def menustatusbar_toggled(self, widget):
        if self.blockMenuCallback: return

        if widget.get_active():
            self.statusbar.show()
            self.options.set_option('Options', 'statusbar', 'True')
        else:
            self.statusbar.hide()
            self.options.set_option('Options', 'statusbar', 'False')

    def menuhome_activate(self, widget):
        webbrowser.open(Const.WEBSITE)

    def menuforum_activate(self, widget):
        webbrowser.open(Const.FORUMURL)

    def menuabout_activate(self, widget):
        Widgets.about_dialog(self.main)

    # range callbacks
    def rangeadd_clicked(self, widget):
        rangefrom = self.entryRangeFrom.get_text()
        rangeto = self.entryRangeTo.get_text()
        rangeyear = self.entryRangeYear.get_text()
        rangesex = self.cbRangeSex.get_active_text()

        check1 = check.check_ring_entry(self.main, rangefrom, rangeyear)
        if not check1: return

        check2 = check.check_ring_entry(self.main, rangeto, rangeyear)
        if not check2: return

        if not rangefrom.isdigit() or not rangeto.isdigit():
            Widgets.message_dialog('error', Const.MSG_INVALID_RANGE, self.main)
            return

        bandList = []
        value = int(rangefrom)

        while value <= int(rangeto):
            bandList.append(str(value))
            value += 1

        for band in bandList:
            pindex = band + rangeyear

            if self.database.has_pigeon(pindex):
                overwrite = Widgets.message_dialog('warning', Const.MSG_OVERWRITE_PIGEON, self.main)
                if not overwrite:
                    continue

            data = (pindex, band, rangeyear, rangesex, 1, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
            self.database.insert_pigeon(data)

        self.parser.get_pigeons()

        self.fill_treeview()

        self.rangedialog.hide()

    def rangecancel_clicked(self, widget):
        self.rangedialog.hide()

    # Main treeview callbacks
    def column1_clicked(self, column):
        treeview = column.get_tree_view()
        liststore = treeview.get_model()
        if column.get_sort_order() == gtk.SORT_ASCENDING:
            liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
            liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        else:
            liststore.set_sort_column_id(1, gtk.SORT_DESCENDING)
            liststore.set_sort_column_id(0, gtk.SORT_DESCENDING)

    def column2_clicked(self, column):
        treeview = column.get_tree_view()
        liststore = treeview.get_model()
        if column.get_sort_order() == gtk.SORT_ASCENDING:
            liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
            liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
        else:
            liststore.set_sort_column_id(0, gtk.SORT_DESCENDING)
            liststore.set_sort_column_id(1, gtk.SORT_DESCENDING)

    def treeview_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.menuedit_activate, None),
                (gtk.STOCK_REMOVE, self.menuremove_activate, None)]

            Widgets.popup_menu(event, entries)

    # Navigation arrows callbacks
    def button_top_clicked(self, widget):
        if len(self.liststore) > 0:
            path = (0,)
            self.treeview.set_cursor(path)

    def button_up_clicked(self, widget):
        path, focus = self.treeview.get_cursor()

        try:
            temp = path[0]
            if not temp == 0:
                new_path = (temp-1,)
                self.treeview.set_cursor(new_path)
        except TypeError:
            pass

    def button_down_clicked(self, widget):
        path, focus = self.treeview.get_cursor()

        try:
            temp = path[0]
            if not temp == len(self.liststore)-1:
                new_path = (temp+1,)
                self.treeview.set_cursor(new_path)
        except TypeError:
            pass

    def button_bottom_clicked(self, widget):
        if len(self.liststore) > 0:
            path = (len(self.liststore)-1,)
            self.treeview.set_cursor(path)

    # Add/Edit callbacks
    def save_clicked(self, widget):
        if not check.check_entrys(self.entrysToCheck): return

        self.write_new_data()

        self.add_edit_finish()

    def btnadd_clicked(self, widget):
        if not check.check_entrys(self.entrysToCheck): return

        self.write_new_pigeon()

        self.add_edit_finish()

    def cancel_clicked(self, widget):
        self.add_edit_finish()

    # Image callbacks
    def eventbox_press(self, widget, event):
        pindex, ring, year = self.get_main_ring()
        image = self.parser.pigeons[pindex].image
        if image:
            Widgets.ImageWindow(image, self.main)

    def eventimage_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_ADD, self.open_filedialog, None),
                (gtk.STOCK_REMOVE, self.set_default_image, None)]

            Widgets.popup_menu(event, entries)
        else:
            self.open_filedialog()

    def fcopen_clicked(self, widget):
        self.imageToAdd = None
        filename = self.filedialog.get_filename()
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 200, 200)
            self.imagePigeon.set_from_pixbuf(pixbuf)
            self.imagePigeon1.set_from_pixbuf(pixbuf)
            self.imageToAdd = filename
        except:
            Widgets.message_dialog('error', Const.MSG_INVALID_IMAGE, self.main)

        self.filedialog.hide()

    def fccancel_clicked(self, widget):
        self.filedialog.hide()

    # Pedigree callbacks
    def sbdetail_clicked(self, widget):
        pindex, ring, year = self.get_main_ring()

        name = self.parser.pigeons[pindex].name
        sex = self.sexDic[self.parser.pigeons[pindex].sex]
        colour = self.parser.pigeons[pindex].colour
        PedigreeWindow.PedigreeWindow(self, pindex, ring, year, name, colour, sex)

    def goto_clicked(self, widget):
        ring = ''
        year = ''

        children = []
        children.extend(self.tableSire.get_children())
        children.extend(self.tableDam.get_children())

        for child in children:
            if child.is_focus():
                text = child.textlayout.get_text()
                if text:
                    ring = text.split(' / ')[0]
                    year = text.split(' / ')[1]
                    if child.get_parent().get_name() == 'tableSire':
                        sex = '0'
                    else:
                        sex = '1'

        if ring:
            pigeon = self.search_pigeon(None, ring+year)
            if pigeon: return

            answer = Widgets.message_dialog('question', Const.MSG_ADD_PIGEON, self.main)
            if not answer:
                return
            else:
                self.add_clicked(None)
                self.entryRing1.set_text(ring)
                self.entryYear1.set_text(year)
                self.cbsex.set_active(int(sex))

    # Relatives callbacks
    def tvBrothers_press(self, widget, event):
        pindex = self.get_treeview_pindex(self.selBrothers)
        if not pindex: return

        if event.button == 3:
            entries = [(gtk.STOCK_JUMP_TO, self.search_pigeon, pindex)]

            Widgets.popup_menu(event, entries)
        elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.search_pigeon(None, pindex)

    def tvHalfBrothers_press(self, widget, event):
        pindex = self.get_treeview_pindex(self.selHalfBrothers)
        if not pindex: return

        if event.button == 3:
            entries = [(gtk.STOCK_JUMP_TO, self.search_pigeon, pindex)]

            Widgets.popup_menu(event, entries)
        elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.search_pigeon(None, pindex)

    def tvOffspring_press(self, widget, event):
        pindex = self.get_treeview_pindex(self.selOffspring)
        if not pindex: return

        if event.button == 3:
            entries = [(gtk.STOCK_JUMP_TO, self.search_pigeon, pindex)]

            Widgets.popup_menu(event, entries)
        elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.search_pigeon(None, pindex)

    # Result callbacks
    def tvResults_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.editresult_clicked, None),
                (gtk.STOCK_REMOVE, self.removeresult_clicked, None)]

            Widgets.popup_menu(event, entries)

    def addresult_clicked(self, widget):
        pindex, ring, year = self.get_main_ring()
        try:
            date, point, place, out, sector = self.get_resultdata()
        except TypeError:
            return

        results = self.database.get_pigeon_results(pindex)
        for result in results:
            if result[2] == date and \
               result[3] == point and \
               result[4] == place and \
               result[5] == out:
                Widgets.message_dialog('error', Const.MSG_RESULT_EXISTS, self.main)
                return

        cof = (float(place)/float(out))*100

        data = (ring, date, point, place, out, sector)
        self.database.insert_result(data)

        self.database.insert_racepoint((point, ))
        Widgets.fill_list(self.cbRacepoint, self.database.get_all_racepoints())

        if sector:
            self.database.insert_sector((sector, ))
            Widgets.fill_list(self.cbSector, self.database.get_all_sectors())

        self.lsResult.append([date, point, place, out, cof, sector])

    def removeresult_clicked(self, widget):
        path, focus = self.tvResults.get_cursor()
        model, tIter = self.selResults.get_selected()
        pindex, ring, year = self.get_main_ring()

        ID = self.get_result_id(ring, self.get_selected_result())

        self.database.delete_result_from_id(ID)

        self.lsResult.remove(tIter)

        if len(self.lsResult) > 0:
            self.tvResults.set_cursor(path)

    def editresult_clicked(self, widget):
        date, point, place, out, sector = self.get_selected_result()
        self.entryDate.set_text(date)
        self.cbRacepoint.child.set_text(point)
        self.spinPlaced.set_value(place)
        self.spinOutof.set_value(out)
        self.cbSector.child.set_text(sector)

        Widgets.set_multiple_visible({self.addresult: False, self.editapply: True, self.resultcancel: True})
        self.labeladdresult.set_markup(_("<b>Edit this result</b>"))

        self.editResultMode = True

    def editapply_clicked(self, widget):
        pindex, ring, year = self.get_main_ring()
        try:
            date, point, place, out, sector = self.get_resultdata()
        except TypeError:
            return

        ID = self.get_result_id(ring, self.get_selected_result())

        self.database.update_result((date, point, place, out, sector, ID))

        self.get_results(ring)
        self.resultcancel_clicked(None)

    def resultcancel_clicked(self, widget):
        self.entryDate.set_text('')
        self.cbRacepoint.child.set_text('')
        self.spinPlaced.set_value(1)
        self.spinOutof.set_value(1)
        self.cbSector.child.set_text('')

        Widgets.set_multiple_visible({self.addresult: True, self.editapply: False, self.resultcancel: False})
        self.labeladdresult.set_markup(_("<b>Add a new result</b>"))

        self.editResultMode = False

    def allresults_clicked(self, widget):
        ResultWindow.ResultWindow(self, self.parser.pigeons, self.database)

    def spinPlaced_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]

        self.spinOutof.set_range(spinmin, spinmax)

    # Find parent callbacks
    def findsire_clicked(self, widget):
        self.search = 'sire'
        self.fill_find_treeview('0')

    def finddam_clicked(self, widget):
        self.search = 'dam'
        self.fill_find_treeview('1')

    def findadd_clicked(self, widget):
        model, path = self.selectionfind.get_selected()
        if not path: return

        pindex = model[path][0]
        ring = model[path][1]
        year = model[path][2]

        if self.search == 'sire':
            self.entrySireEdit.set_text(ring)
            self.entryYearSireEdit.set_text(year)
        else:
            self.entryDamEdit.set_text(ring)
            self.entryYearDamEdit.set_text(year)

        self.finddialog.hide()

    def findcancel_clicked(self, widget):
        self.finddialog.hide()

    # Calendar callbacks
    def calbutton_clicked(self, widget):
        self.position_popup()

        date = datetime.date.today()
        self.calendar.select_month(date.month-1, date.year)
        self.calendar.select_day(date.day)

        self.calpopup.grab_add()
        self.calpopup.show()
        self.calpopup.grab_focus()

    def day_selected(self, widget):
        year, month, day = self.calendar.get_date()
        month += 1        
        the_date = datetime.date(year, month, day)

        if the_date:
            self.entryDate.set_text(the_date.strftime(self.date_format))
        else:
            self.entryDate.set_text('')

    def day_double_clicked(self, widget, data=None):
        self.hide_popup()

    #
    # End of callbacks
    ##################

    def build_menubar(self):
        '''
        Build menu and toolbar from the xml UI string
        '''

        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(Widgets.uistring)
        uimanager.insert_action_group(self.create_action_group(), 0)
        self.main.add_accel_group(uimanager.get_accel_group())

        uimanager.connect('connect-proxy', self.uimanager_connect_proxy)

        menubar = uimanager.get_widget('/MenuBar')
        self.toolbar = uimanager.get_widget('/Toolbar')
        widgetDic = {"MenuArrows": uimanager.get_widget('/MenuBar/ViewMenu/Arrows'),
                     "MenuToolbar": uimanager.get_widget('/MenuBar/ViewMenu/Toolbar'),
                     "MenuStatusbar": uimanager.get_widget('/MenuBar/ViewMenu/Statusbar'),
                     "Filtermenu": uimanager.get_widget('/MenuBar/ViewMenu/FilterMenu'),
                     "MenuEdit": uimanager.get_widget('/MenuBar/PigeonMenu/Edit'),
                     "MenuRemove": uimanager.get_widget('/MenuBar/PigeonMenu/Remove'),
                     "MenuPedigree": uimanager.get_widget('/MenuBar/PigeonMenu/Pedigree'),
                     "MenuAddresult": uimanager.get_widget('/MenuBar/PigeonMenu/Addresult'),
                     "ToolEdit": uimanager.get_widget('/Toolbar/Edit'),
                     "ToolRemove": uimanager.get_widget('/Toolbar/Remove')
                    }

        for key, value in widgetDic.items():
            setattr(self, key, value)

        Widgets.set_multiple_sensitive({self.MenuEdit: False, self.MenuRemove: False,
                                        self.MenuPedigree: False, self.MenuAddresult: False})

        self.vbox.pack_start(menubar, False, False)
        self.vbox.reorder_child(menubar, 0)
        self.vbox.pack_start(self.toolbar, False, False)
        self.vbox.reorder_child(self.toolbar, 1)

    def create_action_group(self):
        '''
        Create the action group for our menu and toolbar
        '''

        entries = (
            ("FileMenu", None, _("_File")),
            ("PigeonMenu", None, _("_Pigeon")),
            ("EditMenu", None, _("_Edit")),
            ("ViewMenu", None, _("_View")),
            ("FilterMenu", None, _("_Filter pigeons")),
            ("HelpMenu", None, _("_Help")),
            ("Quit", gtk.STOCK_QUIT, _("_Quit"), "<control>Q",
                    _("Quit the program"), self.quit_program),
            ("Add", gtk.STOCK_ADD, _("_Add"), "<control>A",
                    _("Add a new pigeon"), self.menuadd_activate),
            ("Addrange", gtk.STOCK_ADD, _("Add ran_ge"), "<control><shift>A",
                    _("Add a range of pigeons"), self.menuaddrange_activate),
            ("Edit", gtk.STOCK_EDIT, _("_Edit"), "<control>E",
                    _("Edit the selected pigeon"), self.menuedit_activate),
            ("Remove", gtk.STOCK_REMOVE, _("_Remove"), "<control>R",
                    _("Remove the selected pigeon"), self.menuremove_activate),
            ("Pedigree", gtk.STOCK_FIND, _("_Pedigree"), None,
                    _("View the detailed pedigree of this pigeon"), self.menupedigree_activate),
            ("Addresult", gtk.STOCK_ADD, _("Add resul_t"), None,
                    _("Add a new result for this pigeon"), self.menuaddresult_activate),
            ("Tools", gtk.STOCK_EXECUTE, _("_Tools"), "<control>T",
                    _("Various tools"), self.menutools_activate),
            ("Preferences", gtk.STOCK_PREFERENCES, _("_Preferences"), "<control>P",
                    _("Configure the application"), self.menupref_activate),
            ("Home", gtk.STOCK_HOME, _("_Website"), None,
                    _("Go to the website for more information"), self.menuhome_activate),
            ("Forum", gtk.STOCK_INFO, _("Forum"), None,
                    _("Go to the forum for online help"), self.menuforum_activate),
            ("About", gtk.STOCK_ABOUT, _("_About"), None,
                    _("About this application"), self.menuabout_activate)
           )

        toggle_entries = (
            ("Arrows",  None, _("Navigation arrows"), None,
                    _("Show or hide the navigation arrows"), self.menuarrows_toggled, False),
            ("Toolbar",  None, _("Toolbar"), None,
                    _("Show or hide the toolbar"), self.menutoolbar_toggled, False),
            ("Statusbar",  None, _("Statusbar"), None,
                    _("Show or hide the statusbar"), self.menustatusbar_toggled, False)
           )

        filter_entries = (
            ( "All", None, _("_All"), None,
                    _("Show all pigeons"), 0),
            ( "Cocks", None, _("_Cocks"), None,
                    _("Only show cocks"), 1),
            ( "Hens", None, _("_Hens"), None,
                    _("Only show hens"), 2),
            ( "Young", None, _("_Young birds"), None,
                    _("Only show young birds"), 3)
           )

        action_group = gtk.ActionGroup("MainWindowActions")
        action_group.add_actions(entries)
        action_group.add_toggle_actions(toggle_entries)
        action_group.add_radio_actions(filter_entries, 0, self.menufilter_action)

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
        '''
        Build the main treeview
        '''

        for column in self.treeview.get_columns():
            self.treeview.remove_column(column)

        columns = [_("Band no."), _("Year"), _("Name")]
        if self.options.optionList.column:
            columns.insert(self.options.optionList.columnposition,
                           _(self.columnValueDic[self.options.optionList.columntype]))
        types = [str, str, str, str, str]
        self.liststore, self.selection = Widgets.setup_treeview(self.treeview, columns, types, self.selection_changed, True, True, True)

    def build_treeviews(self):
        '''
        Build the remaining treeviews
        '''

        # Find sire/dam treeview
        columns = [_("Band no."), _("Year"), _("Name")]
        types = [str, str, str, str]
        self.lsFind, self.selectionfind = Widgets.setup_treeview(self.tvFind, columns, types, None, True, True, True)

        # Brothers & sisters treeview
        columns = [_("Band no."), _("Year")]
        types = [str, str, str]
        self.lsBrothers, self.selBrothers = Widgets.setup_treeview(self.tvBrothers, columns, types, None, True, True, True)

        # Halfbrothers & sisters treeview
        columns = [_("Band no."), _("Year"), _("Common parent")]
        types = [str, str, str, str]
        self.lsHalfBrothers, self.selHalfBrothers = Widgets.setup_treeview(self.tvHalfBrothers, columns, types, None, True, True, True)

        # Offspring treeview
        columns = [_("Band no."), _("Year")]
        types = [str, str, str]
        self.lsOffspring, self.selOffspring = Widgets.setup_treeview(self.tvOffspring, columns, types, None, True, True, True)

        # Results treeview
        columns = [_("Date"), _("Racepoint"), _("Placed"), _("Out of"), _("Coefficient"), _("Sector")]
        types = [str, str, int, int, float, str]
        self.lsResult, self.selResults = Widgets.setup_treeview(self.tvResults, columns, types, self.selectionresult_changed, True, True)

    def fill_treeview(self, pigeonType='all', path=0):
        '''
        Fill the main treeview with pigeons.

        @param pigeonType: The gender of pigeons to show
        @param path: The path to set the cursor
        '''

        self.liststore.clear()

        for pindex in self.parser.pigeons:
            if not self.parser.pigeons[pindex].show: continue

            if pigeonType == self.parser.pigeons[pindex].sex or pigeonType == 'all':
                row = [pindex,
                       self.parser.pigeons[pindex].ring,
                       self.parser.pigeons[pindex].year,
                       self.parser.pigeons[pindex].name]

                if self.options.optionList.column:
                    if self.options.optionList.columntype == '0':
                        extra = self.parser.pigeons[pindex].colour
                    elif self.options.optionList.columntype == '1':
                        extra = self.sexDic[self.parser.pigeons[pindex].sex]

                    row.insert(self.options.optionList.columnposition+1, extra)
                else:
                    row.insert(4, None)

                self.liststore.append(row)

        if len(self.liststore) > 0:
            self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
            self.liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)
            self.treeview.set_cursor(path)
            self.treeview.set_property('has-focus', True)
        else:
            self.imagePigeon.set_from_pixbuf(self.logoPixbuf)
            self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)

    def selectionresult_changed(self, selection):
        '''
        Set the remove and edit result buttons sensitive when there is a result selected
        '''

        model, path = selection.get_selected()

        if path:
            Widgets.set_multiple_sensitive({self.removeresult: True, self.editresult: True})
        else:
            Widgets.set_multiple_sensitive({self.removeresult: False, self.editresult: False})

    def selection_changed(self, selection):
        '''
        Get all the data/info from the selected pigeon
        '''

        model, path = selection.get_selected()

        if path:
            if self.editResultMode:
                self.resultcancel_clicked(None)

            Widgets.set_multiple_sensitive({self.ToolEdit: True, self.ToolRemove: True,
                                            self.sbdetail: True, self.MenuEdit: True,
                                            self.MenuRemove: True, self.MenuPedigree: True,
                                            self.MenuAddresult: True, self.addresult: True})
        else:
            Widgets.set_multiple_sensitive({self.ToolEdit: False, self.ToolRemove: False,
                                            self.sbdetail: False, self.MenuEdit: False,
                                            self.MenuRemove: False, self.MenuPedigree: False,
                                            self.MenuAddresult: False, self.addresult: False})
            self.empty_entryboxes()
            return

        self.empty_entryboxes()

        pindex = model[path][0]

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

        self.entryRing.set_text(ring)
        self.entryYear.set_text(year)
        self.entrySexKey.set_text(sex)
        self.entrySex.set_text(self.sexDic[sex])
        self.entryStrain.set_text(strain)
        self.entryLoft.set_text(loft)
        self.entryColour.set_text(colour)
        self.entryName.set_text(name)
        self.extra1.set_text(extra1)
        self.extra2.set_text(extra2)
        self.extra3.set_text(extra3)
        self.extra4.set_text(extra4)
        self.extra5.set_text(extra5)
        self.extra6.set_text(extra6)
        self.entrySire.set_text(sire)
        self.entryDam.set_text(dam)
        self.entryYearSire.set_text(yearsire)
        self.entryYearDam.set_text(yeardam)

        if self.parser.pigeons[pindex].image:
            image = self.parser.pigeons[pindex].image
            width = height = 200
        else:
            image = Const.IMAGEDIR + 'icon_logo.png'
            width = height = 75

        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(image, width, height)
            self.imagePigeon.set_from_pixbuf(pixbuf)
            self.imagePigeon1.set_from_pixbuf(pixbuf)
        except:
            Widgets.message_dialog('error', Const.MSG_IMAGE_MISSING, self.main)

        dp = DrawPedigree([self.tableSire, self.tableDam], pindex,
                           button=self.goto, pigeons=self.parser.pigeons)
        dp.draw_pedigree()

        self.find_direct_relatives(pindex, sire, dam)
        self.find_half_relatives(pindex, sire, yearsire, dam, yeardam)
        self.find_offspring(pindex, sire, dam)

        self.get_results(pindex)

    def get_results(self, pindex):
        '''
        Get all results of selected pigeon

        @param pindex: the selected pigeon
        '''

        self.lsResult.clear()

        for result in self.database.get_pigeon_results(pindex):
            date = result[2]
            point = result[3]
            place = result[4]
            out = result[5]
            sector = result[6]

            cof = (float(place)/float(out))*100

            self.lsResult.append([date, point, place, out, cof, sector])

        self.lsResult.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def find_direct_relatives(self, pindex, sire, dam):
        '''
        Search all brothers and sisters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        '''

        self.lsBrothers.clear()

        if not sire or not dam: return

        for pigeon in self.parser.pigeons:
            if sire == self.parser.pigeons[pigeon].sire and\
               dam == self.parser.pigeons[pigeon].dam and not\
               pigeon == pindex:

                self.lsBrothers.append([pigeon, self.parser.pigeons[pigeon].ring,
                                        self.parser.pigeons[pigeon].year])

        self.lsBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsBrothers.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def find_half_relatives(self, pindex, sire, yearsire, dam, yeardam):
        '''
        Search all halfbrothers and sisters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param yearsire: year of the sire of selected pigeon
        @param dam: dam of selected pigeon
        @param yeardam: year of the dam of selected pigeon
        '''

        self.lsHalfBrothers.clear()

        for pigeon in self.parser.pigeons:

            if sire:
                if sire == self.parser.pigeons[pigeon].sire\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.append([pigeon, self.parser.pigeons[pigeon].ring,
                                                self.parser.pigeons[pigeon].year, sire+'/'+yearsire[2:]])

            if dam:
                if dam == self.parser.pigeons[pigeon].dam\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.append([pigeon, self.parser.pigeons[pigeon].ring,
                                                self.parser.pigeons[pigeon].year, dam+'/'+yeardam[2:]])

        self.lsHalfBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsHalfBrothers.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def find_offspring(self, pindex, sire, dam):
        '''
        Find all youngsters of the selected pigeon.

        @param pindex: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        '''

        self.lsOffspring.clear()

        for pigeon in self.parser.pigeons:
            ring = self.parser.pigeons[pindex].ring
            if self.parser.pigeons[pigeon].sire == ring or self.parser.pigeons[pigeon].dam == ring:

                self.lsOffspring.append([pigeon, self.parser.pigeons[pigeon].ring,
                                         self.parser.pigeons[pigeon].year])

        self.lsOffspring.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.lsOffspring.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def set_menuitem_sensitive(self, activated):
        '''
        Set the current selected item of the filtermenu active/inactive

        @param activated: the currently activated item
        '''

        filterList = [self.young, self.cock, self.hen, self.all]
        for item in filterList:
            if not item.get_property('sensitive'):
                item.set_property('sensitive', True)

        activated.set_property('sensitive', False)

    def add_edit_start(self, operation):
        '''
        Do all the necessary things to start editing or adding.

        @param operation: 'add' or 'edit'
        '''

        if operation == 'add':
            Widgets.set_multiple_visible({self.btnadd: True})
        elif operation == 'edit':
            Widgets.set_multiple_visible({self.save: True})
            self.beforeEditPath, focus = self.treeview.get_cursor()

        self.entryRing1.grab_focus()

        Widgets.set_multiple_visible({self.alignUnEdit: False, self.alignEdit: True})

        Widgets.set_multiple_sensitive({self.toolbar: False, self.notebook: False,
                                        self.treeview: False, self.vboxButtons: False})

    def add_edit_finish(self):
        '''
        Do all the necessary things to finish editing or adding.
        '''

        self.parser.get_pigeons()

        self.fill_treeview(path=self.beforeEditPath)

        self.beforeEditPath = 0

        Widgets.set_multiple_visible({self.alignUnEdit: True, self.alignEdit: False})

        Widgets.set_multiple_sensitive({self.toolbar: True, self.notebook: True,
                                        self.treeview: True, self.vboxButtons: True})

        Widgets.set_multiple_visible({self.btnadd: False, self.save: False})

    def get_add_edit_info(self):
        '''
        Return a tuple containig info about the editable widgets.
        '''

        imageTemp = ''

        try:
            imageTemp = self.database.get_image(self.entryRing1.get_text())
        except:
            pass

        if imageTemp and not self.imageDeleted == True:
            image = imageTemp
        else:
            image = self.imageToAdd

        self.imageDeleted = False

        infoTuple = (self.entryRing1.get_text(),\
                     self.entryYear1.get_text(),\
                     self.cbsex.get_active_text(),\
                     1,\
                     self.cbColour.child.get_text(),\
                     self.entryName1.get_text(),\
                     self.cbStrain.child.get_text(),\
                     self.cbLoft.child.get_text(),\
                     image,\
                     self.entrySireEdit.get_text(),\
                     self.entryYearSireEdit.get_text(),\
                     self.entryDamEdit.get_text(),\
                     self.entryYearDamEdit.get_text(),\
                     self.extra11.get_text(),\
                     self.extra21.get_text(),\
                     self.extra31.get_text(),\
                     self.extra41.get_text(),\
                     self.extra51.get_text(),\
                     self.extra61.get_text())

        return infoTuple

    def write_new_data(self):
        '''
        Write new data to the pigeon
        '''

        infoTuple = self.get_add_edit_info()
        infoTuple += (infoTuple[0] + infoTuple[1],) # Make the pindex and add to the tuple
        self.database.update_pigeon(infoTuple)

        self.update_data(infoTuple)

    def write_new_pigeon(self):
        '''
        Write the new pigeon to the database
        '''

        infoTuple = self.get_add_edit_info()
        pindex = infoTuple[0] + infoTuple[1]
        pindexTuple = (pindex,)
        pindexTuple += infoTuple

        if self.database.has_pigeon(pindex):
            if self.parser.pigeons[pindex].show:
                overwrite = Widgets.message_dialog('warning', Const.MSG_OVERWRITE_PIGEON, self.main)
                if not overwrite:
                    return
            else:
                overwrite = Widgets.message_dialog('warning', Const.MSG_SHOW_PIGEON, self.main)
                if not overwrite:
                    return
                else:
                    self.database.show_pigeon(pindex, 1)
                    return

        self.database.insert_pigeon(pindexTuple)

        self.update_data(infoTuple)

    def update_data(self, infoTuple):
        '''
        Update the data
        '''

        colour = infoTuple[4]
        if colour:
            self.database.insert_colour((colour, ))
            Widgets.fill_list(self.cbColour, self.database.get_all_colours())

        strain = infoTuple[6]
        if strain:
            self.database.insert_strain((strain, ))
            Widgets.fill_list(self.cbStrain, self.database.get_all_strains())

        loft = infoTuple[7]
        if loft:
            self.database.insert_loft((loft, ))
            Widgets.fill_list(self.cbLoft, self.database.get_all_lofts())

    def empty_entryboxes(self):
        '''
        Empty all entryboxes
        '''

        entryWidgets = self.wTree.get_widget_prefix("entry")
        for widget in entryWidgets:
            name = widget.get_name()
            if not name == 'entryDate':
                attr = getattr(self, name)
                attr.set_text('')

    def set_default_image(self, widget):
        self.imagePigeon1.set_from_pixbuf(self.logoPixbuf)
        self.imageToAdd = ''
        self.imageDeleted = True

    def open_filedialog(self, widget=None):
        '''
        Set a preview image and show the Filechooser dialog
        '''

        self.file_previewbox = gtk.VBox()
        self.file_previewbox.set_size_request(200, 200)
        self.file_preview = gtk.Image()
        self.file_previewlabel = gtk.Label()
        self.file_previewbox.pack_start(self.file_preview)
        self.file_previewbox.pack_start(self.file_previewlabel)
        self.filedialog.set_preview_widget(self.file_previewbox)
        self.file_previewbox.show_all()

        self.filedialog.show()

    def filedialog_selection(self, widget):
        '''
        Update the image preview in the filechooser dialog
        '''

        preview_file = self.filedialog.get_preview_filename()
        if preview_file and os.path.isfile(preview_file):
            self.filedialog.set_preview_widget_active(True)
            pixbuf = gtk.gdk.pixbuf_new_from_file(preview_file)

            new_width = width = pixbuf.get_width()
            new_height = height = pixbuf.get_height()
            max_width = 200
            max_height = 200
            if new_width > max_width or new_height > max_height:
                new_width = max_width
                new_height = max_width*height/width
                if new_height > max_height:
                    new_height = max_height
                    new_width = max_height*width/height
            pixbuf = pixbuf.scale_simple(new_width, new_height, gtk.gdk.INTERP_TILES)
            self.file_preview.set_from_pixbuf(pixbuf)
        else:
            self.filedialog.set_preview_widget_active(False)

    def url_hook(self, about, link):
        import sys
        if sys.platform.startswith("win"):
            webbrowser.open(link)

    def email_hook(self, about, email):
        webbrowser.open("mailto:%s" % email)

    def position_popup(self):
        '''
        Position the popup calendar
        '''

        req = self.calpopup.size_request()
        (x,y) = gtk.gdk.Window.get_origin(self.calbutton.window)

        x += self.calbutton.allocation.x
        y += self.calbutton.allocation.y
        bwidth = self.calbutton.allocation.width
        bheight = self.calbutton.allocation.height

        x += bwidth - req[0]
        y += bheight

        if x < 0: x = 0
        if y < 0: y = 0
        
        self.calpopup.move(x,y)

    def hide_popup(self):
        '''
        Hide the popup calendar
        '''

        self.calpopup.hide()
        self.calpopup.grab_remove()

    def get_main_ring(self):
        '''
        Return the ring and year of selected pigeon
        '''

        model, path = self.selection.get_selected()
        if not path: return
        pindex = model[path][0]
        ring = model[path][1]
        year = model[path][2]

        return pindex, ring, year

    def search_pigeon(self, widget, ring):
        '''
        Set the cursor on the given pigeon

        @param ring: The pigeon to search
        '''

        for item in self.liststore:
            number = self.treeview.get_model().get_value(item.iter, 0)
            if number == ring:
                self.treeview.set_cursor(item.path)
                return True

        return False

    def get_treeview_pindex(self, selection):
        '''
        Return the pindex of the selected row

        @param selection: the selection of the treeview
        '''

        model, path = selection.get_selected()
        if not path: return
        pindex = model[path][0]

        return pindex

    def get_resultdata(self):
        '''
        Get the values from the result widgets
        '''

        date = self.entryDate.get_text()
        point = self.cbRacepoint.child.get_text()
        place = self.spinPlaced.get_value_as_int()
        out = self.spinOutof.get_value_as_int()
        sector = self.cbSector.child.get_text()

        if not date or not point or not place or not out:
            Widgets.message_dialog('error', Const.MSG_EMPTY_DATA, self.main)
            return False

        try:
            datetime.datetime.strptime(date, self.date_format)
        except ValueError:
            Widgets.message_dialog('error', Const.MSG_INVALID_FORMAT, self.main)
            return False

        return date, point, place, out, sector

    def get_selected_result(self):
        '''
        Return the data from the selected result
        '''

        model, tIter = self.selResults.get_selected()
        if not tIter: return
        
        return model[tIter][0], model[tIter][1], model[tIter][2], model[tIter][3], model[tIter][5]

    def get_result_id(self, ring, data):
        '''
        Return the ID of the wanted result

        @param ring: the ring of the pigeon
        @param data: tuple of data to compare
        '''

        results = self.database.get_pigeon_results(ring)
        for result in results:
            if result[2] == data[0] and \
               result[3] == data[1] and \
               result[4] == data[2] and \
               result[5] == data[3]:
                    return result[0]

        return None

    def fill_find_treeview(self, pigeonType):
        '''
        Fill the 'find'-treeview with pigeons of the wanted sex

        @param pigeonType: sex of the pigeons
        '''

        self.lsFind.clear()

        for pigeon in self.parser.pigeons:
            if pigeonType == self.parser.pigeons[pigeon].sex:
                self.lsFind.append([pigeon,
                                    self.parser.pigeons[pigeon].ring,
                                    self.parser.pigeons[pigeon].year,
                                    self.parser.pigeons[pigeon].name])

        if len(self.lsFind) > 0:
            self.lsFind.set_sort_column_id(1, gtk.SORT_ASCENDING)
            self.lsFind.set_sort_column_id(2, gtk.SORT_ASCENDING)
            self.tvFind.set_cursor(0)

        self.finddialog.show()

    def create_sexcombos(self):
        '''
        Create the sexcombos and show them
        '''

        self.sexStore = gtk.ListStore(str, str)
        for key in self.sexDic.keys():
            self.sexStore.insert(int(key), [key, self.sexDic[key]])
        self.cbsex = gtk.ComboBox(self.sexStore)
        self.cbRangeSex = gtk.ComboBox(self.sexStore)
        for box in [self.cbsex, self.cbRangeSex]:
            cell = gtk.CellRendererText()
            box.pack_start(cell, True)
            box.add_attribute(cell, 'text', 1)
            box.show()

        self.table1.attach(self.cbRangeSex, 6, 7, 1, 2, gtk.SHRINK, gtk.FILL, 0, 0)
        self.table4.attach(self.cbsex, 1, 2, 1, 2, gtk.SHRINK, gtk.FILL, 0, 0)

    def set_filefilter(self):
        '''
        Set a file filter for supported image files
        '''

        fileFilter = gtk.FileFilter()
        fileFilter.set_name(_("Images"))
        fileFilter.add_pixbuf_formats()
        self.filedialog.add_filter(fileFilter)

