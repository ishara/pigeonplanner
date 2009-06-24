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


import datetime
import gobject
import ConfigParser

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

        signalDic = { 'on_add_clicked'           : self.add_clicked,
                      'on_remove_clicked'        : self.remove_clicked,
                      'on_edit_clicked'          : self.edit_clicked,
                      'on_save_clicked'          : self.save_clicked,
                      'on_cancel_clicked'        : self.cancel_clicked,
                      'on_btnadd_clicked'        : self.btnadd_clicked,
                      'on_options_clicked'       : self.options_clicked,
                      'on_tools_clicked'         : self.tools_clicked,
                      'on_help_clicked'          : self.help_clicked,
                      'on_about_clicked'         : self.about_clicked,
                      'on_sbdetail_clicked'      : self.sbdetail_clicked,
                      'on_goto_clicked'          : self.goto_clicked,
                      'on_addresult_clicked'     : self.addresult_clicked,
                      'on_removeresult_clicked'  : self.removeresult_clicked,
                      'on_editresult_clicked'    : self.editresult_clicked,
                      'on_editapply_clicked'     : self.editapply_clicked,
                      'on_resultcancel_clicked'  : self.resultcancel_clicked,
                      'on_allresults_clicked'    : self.allresults_clicked,
                      'on_filterlist_clicked'    : self.filterlist_clicked,
                      'on_fcopen_clicked'        : self.fcopen_clicked,
                      'on_fccancel_clicked'      : self.fccancel_clicked,
                      'on_young_activate'        : self.young_activate,
                      'on_cock_activate'         : self.cock_activate,
                      'on_hen_activate'          : self.hen_activate,
                      'on_all_activate'          : self.all_activate,
                      'on_single_activate'       : self.add_clicked,
                      'on_serie_activate'        : self.serie_activate,
                      'on_serieadd_clicked'      : self.serieadd_clicked,
                      'on_seriecancel_clicked'   : self.seriecancel_clicked,
                      'on_eventimage_press'      : self.eventimage_press,
                      'on_treeview_press'        : self.treeview_press,
                      'on_findsire_clicked'      : self.findsire_clicked,
                      'on_finddam_clicked'       : self.finddam_clicked,
                      'on_findcancel_clicked'    : self.findcancel_clicked,
                      'on_findadd_clicked'       : self.findadd_clicked,
                      'on_calbutton_clicked'     : self.calbutton_clicked,
                      'on_day_selected'          : self.day_selected,
                      'on_day_double_clicked'    : self.day_double_clicked,
                      'on_notebook_switch'       : self.notebook_switch,
                      'on_button_top_clicked'    : self.button_top_clicked,
                      'on_button_up_clicked'     : self.button_up_clicked,
                      'on_button_down_clicked'   : self.button_down_clicked,
                      'on_button_bottom_clicked' : self.button_bottom_clicked,
                      'on_spinPlaced_changed'    : self.spinPlaced_changed,
                      'on_seriedialog_delete'    : self.dialog_delete,
                      'on_finddialog_delete'     : self.dialog_delete,
                      'on_removedialog_delete'   : self.dialog_delete,
                      'on_filedialog_delete'     : self.dialog_delete,
                      'on_main_destroy'          : gtk.main_quit,
                      'on_quit_clicked'          : gtk.main_quit }
        self.wTree.signal_autoconnect(signalDic)

        for widget in self.wTree.get_widget_prefix(''):
            name = widget.get_name()
            setattr(self, name, widget)

        self.main.set_title("%s %s" %(Const.NAME, Const.VERSION))

        self.date_format = '%Y-%m-%d'
        self.imageToAdd = ''
        self.imageDeleted = False
        self.beforeEditPath = None
        self.sexDic = {'0': _('cock'), '1': _('hen'), '2': _('young bird')}
        self.entrysToCheck = { 'ring': self.entryRing1, 'year': self.entryYear1, 
                               'sire': self.entrySireEdit, 'yearsire': self.entryYearSireEdit, 
                               'dam': self.entryDamEdit, 'yeardam': self.entryYearDamEdit}

        self.entrySexKey = gtk.Entry()
        self.hbox4.pack_start(self.entrySexKey)

        self.database = Database.DatabaseOperations()
        self.options = Options.GetOptions()
        self.parser = PigeonParser.PigeonParser()
        self.parser.get_pigeons()
        self.pedigree = DrawPedigree([self.tableSire, self.tableDam], button=self.goto)
        self.pedigree.draw_pedigree()
        self.build_treeview()
        self.build_treeviews()
        self.fill_treeview()
        self.create_sexcombos()
        self.set_filefilter()
        for item in [self.cbRacepoint, self.cbSector, self.cbColour, self.cbStrain, self.cbLoft]:
            self.set_completion(item)

        if self.options.optionList.arrows:
            self.alignarrows.show()

        self.listdata = {self.cbSector: self.database.get_all_sectors(), \
                         self.cbRacepoint: self.database.get_all_racepoints(), \
                         self.cbColour: self.database.get_all_colours(), \
                         self.cbStrain: self.database.get_all_strains(), \
                         self.cbLoft: self.database.get_all_lofts()}
        for key in self.listdata.keys():
            self.fill_list(key, self.listdata[key])

        gtk.about_dialog_set_url_hook(self.url_hook)
        gtk.about_dialog_set_email_hook(self.email_hook)

    def dialog_delete(self, widget, event):
        widget.hide()
        return True

    def filterlist_clicked(self, widget):
        pass
        #TODO: Show menu

    def young_activate(self, widget):
        self.fill_treeview('2')
        self.set_menuitem_sensitive(widget)

    def cock_activate(self, widget):
        self.fill_treeview('0')
        self.set_menuitem_sensitive(widget)

    def hen_activate(self, widget):
        self.fill_treeview('1')
        self.set_menuitem_sensitive(widget)

    def all_activate(self, widget):
        self.fill_treeview()
        self.set_menuitem_sensitive(widget)

    def serie_activate(self, widget):
        self.entrySerieFrom.set_text('')
        self.entrySerieTo.set_text('')
        self.entrySerieYear.set_text('')
        self.cbSerieSex.set_active(2)
        self.seriedialog.show()

    def serieadd_clicked(self, widget):
        check1 = check.check_ring_entry(self.main, self.entrySerieFrom.get_text(), self.entrySerieYear.get_text(), _('pigeons'))
        if not check1: return

        check2 = check.check_ring_entry(self.main, self.entrySerieTo.get_text(), self.entrySerieYear.get_text(), _('pigeons'))
        if not check2: return

        first = self.entrySerieFrom.get_text()
        last = self.entrySerieTo.get_text()
        year = self.entrySerieYear.get_text()
        sex = self.cbSerieSex.get_active_text()

        bandList = []
        value = int(first)

        while value <= int(last):
            bandList.append(str(value))
            value += 1

        for band in bandList:
            if self.database.has_pigeon(band):
                overwrite = Widgets.message_dialog('warning', Const.MSGEXIST, self.main)
                if overwrite == 'no':
                    continue

            data = (str(band), self.calculate_year(year), sex, 1, '', '', '', '', '', '', '', '', '', '', '', '', '', '','')
            self.database.insert_pigeon(data)

        self.parser.get_pigeons()

        self.fill_treeview()

        self.seriedialog.hide()

    def seriecancel_clicked(self, widget):
        self.seriedialog.hide()

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
                (gtk.STOCK_EDIT, self.edit_clicked),
                (gtk.STOCK_REMOVE, self.remove_clicked)]

            menu = gtk.Menu()
            for stock_id, callback in entries:
                item = gtk.ImageMenuItem(stock_id)
                if callback:
                    item.connect("activate", callback)
                item.show()
                menu.append(item)
            menu.popup(None, None, None, 0, event.time)

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

    def remove_clicked(self, widget):
        ring, year = self.get_main_ring()

        model, tIter = self.selection.get_selected()
        path, focus = self.treeview.get_cursor()

        wTree = gtk.glade.XML(self.gladefile, 'removedialog')
        dialog = wTree.get_widget('removedialog')
        label = wTree.get_widget('labelPigeon')
        chkKeep = wTree.get_widget('chkKeep')
        chkResults = wTree.get_widget('chkResults')
        label.set_text(ring + '/' + year[2:])
        answer = dialog.run()
        if answer == 2:
            if chkKeep.get_active():
                self.database.show_pigeon(ring, 0)
            else:
                self.database.delete_pigeon(ring)
                self.parser.get_pigeons()

            if not chkResults.get_active():
                self.database.delete_result_from_band(ring)

            self.liststore.remove(tIter)

        dialog.destroy()

        if len(self.liststore) > 0:
            self.treeview.set_cursor(path)

    def edit_clicked(self, widget):
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

        self.cbsex.set_active(int(self.entrySexKey.get_text())) #FIXME

        self.add_edit_start('edit')

    def save_clicked(self, widget):
        if not check.check_entrys(self.entrysToCheck): return

        self.write_new_data()

        self.add_edit_finish()

    def add_clicked(self, widget):
        self.empty_entryboxes()
        self.cbColour.child.set_text('')
        self.cbStrain.child.set_text('')
        self.cbLoft.child.set_text('')
        self.cbsex.set_active(0)

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(Const.IMAGEDIR + 'icon_logo.png', 75, 75)
        self.imagePigeon1.set_from_pixbuf(pixbuf)

        self.add_edit_start('add')

    def btnadd_clicked(self, widget):
        if not check.check_entrys(self.entrysToCheck): return

        self.write_new_pigeon()

        self.add_edit_finish()

    def cancel_clicked(self, widget):
        self.add_edit_finish()

    def eventimage_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_ADD, self.open_filedialog),
                (gtk.STOCK_REMOVE, self.set_default_image)]

            menu = gtk.Menu()
            for stock_id, callback in entries:
                item = gtk.ImageMenuItem(stock_id)
                if callback:
                    item.connect("activate", callback)
                item.show()
                menu.append(item)
            menu.popup(None, None, None, 0, event.time)
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
            Widgets.message_dialog('error', Const.MSGIMG, self.main)

        self.filedialog.hide()

    def fccancel_clicked(self, widget):
        self.filedialog.hide()

    def options_clicked(self, widget):
        Options.OptionsDialog(self)

    def tools_clicked(self, widget):
        ToolsWindow.ToolsWindow(self)

    def help_clicked(self, widget):
        pass
        #TODO: Open a help screen.

    def about_clicked(self, widget):
        dialog = gtk.AboutDialog()
        dialog.set_transient_for(self.main)
        dialog.set_icon_from_file(Const.IMAGEDIR + 'icon_logo.png')
        dialog.set_modal(True)
        dialog.set_property("skip-taskbar-hint", True)

        dialog.set_name(Const.NAME)
        dialog.set_version(Const.VERSION)
        dialog.set_copyright(Const.COPYRIGHT)
        dialog.set_comments(_(Const.DESCRIPTION))
        dialog.set_website(Const.WEBSITE)
        dialog.set_website_label("Pigeon Planner website")
        dialog.set_authors(Const.AUTHORS)
        dialog.set_license(Const.LICENSE)
        dialog.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(Const.IMAGEDIR + 'icon_logo.png', 80, 80))

        result = dialog.run()
        dialog.destroy()

    def sbdetail_clicked(self, widget):
        ring, year = self.get_main_ring()

        name = self.parser.pigeons[ring].name
        sex = self.sexDic[self.parser.pigeons[ring].sex]
        colour = self.parser.pigeons[ring].colour
        PedigreeWindow.PedigreeWindow(self, ring, year[2:], name, colour, sex)

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

        if not ring == '':
            for item in self.liststore:
                number = self.treeview.get_model().get_value(item.iter, 0)
                if number == ring:
                    self.treeview.set_cursor(item.path)
                    return

            answer = Widgets.message_dialog('question', Const.MSGADD, self.main)
            if answer == 'no':
                return
            elif answer == 'yes':
                self.add_clicked(None)
                self.entryRing1.set_text(ring)
                self.entryYear1.set_text(year)
                self.cbsex.set_active(int(sex)) #FIXME

    def addresult_clicked(self, widget):
        ring, year = self.get_main_ring()
        try:
            date, point, place, out, sector = self.get_resultdata()
        except TypeError:
            return

        results = self.database.get_pigeon_results(ring)
        for result in results:
            if result[2] == date and \
               result[3] == point and \
               result[4] == place and \
               result[5] == out:
                Widgets.message_dialog('error', Const.MSGRESULT, self.main)
                return

        cof = (float(place)/float(out))*100
        ring, year = self.get_main_ring()
        data = (ring, date, point, place, out, sector)
        self.database.insert_result(data)

        self.database.insert_racepoint((point, ))
        self.fill_list(self.cbRacepoint, self.database.get_all_racepoints())

        if sector:
            self.database.insert_sector((sector, ))
            self.fill_list(self.cbSector, self.database.get_all_sectors())

        self.lsResult.append([date, point, place, out, cof, sector])

    def removeresult_clicked(self, widget):
        path, focus = self.tvResults.get_cursor()
        model, tIter = self.selResults.get_selected()
        ring, year = self.get_main_ring()

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

        self.addresult.set_property('visible', False)
        self.editapply.set_property('visible', True)
        self.resultcancel.set_property('visible', True)

    def editapply_clicked(self, widget):
        ring, year = self.get_main_ring()
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

        self.addresult.set_property('visible', True)
        self.editapply.set_property('visible', False)
        self.resultcancel.set_property('visible', False)

    def allresults_clicked(self, widget):
        ResultWindow.ResultWindow(self, self.parser.pigeons, self.database)

    def findsire_clicked(self, widget):
        self.search = 'sire'
        self.fill_find_treeview('0')

    def finddam_clicked(self, widget):
        self.search = 'dam'
        self.fill_find_treeview('1')

    def findadd_clicked(self, widget):
        model, path = self.selectionfind.get_selected()
        if not path: return

        ring = model[path][0]
        year = model[path][1]

        if self.search == 'sire':
            self.entrySireEdit.set_text(ring)
            self.entryYearSireEdit.set_text(year[2:])
        else:
            self.entryDamEdit.set_text(ring)
            self.entryYearDamEdit.set_text(year[2:])

        self.finddialog.hide()

    def findcancel_clicked(self, widget):
        self.finddialog.hide()

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

    def spinPlaced_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]

        self.spinOutof.set_range(spinmin, spinmax)

    def notebook_switch(self, widget, page, page_num):
        try:
            selected, year = self.get_main_ring()
        except TypeError:
            return

        ring     = self.parser.pigeons[selected].ring
        sire     = self.parser.pigeons[selected].sire
        yearsire = self.parser.pigeons[selected].yearsire
        dam      = self.parser.pigeons[selected].dam
        yeardam  = self.parser.pigeons[selected].yeardam

        if page_num == 0:
            dp = DrawPedigree([self.tableSire, self.tableDam], selected, button=self.goto)
            dp.draw_pedigree()
        elif page_num == 1:
            self.find_direct_relatives(ring, sire, dam)
            self.find_half_relatives(ring, sire, yearsire, dam, yeardam)
            self.find_offspring(ring, sire, dam)
        elif page_num == 2:
            self.get_results(ring)

    def build_treeview(self):
        '''
        Build the main treeview
        '''

        for column in self.treeview.get_columns():
            self.treeview.remove_column(column)

        columns = [_("Band no."), _("Year"), _("Name")]
        if self.options.optionList.column:
            columns.append(_(self.options.optionList.columntype))
        types = [str, str, str, str]
        self.liststore, self.selection = Widgets.setup_treeview(self.treeview, columns, types, self.selection_changed, True, True)

    def build_treeviews(self):
        '''
        Build the remaining treeviews
        '''

        # Find sire/dam treeview
        columns = [_("Band no."), _("Year"), _("Name")]
        types = [str, str, str]
        self.lsFind, self.selectionfind = Widgets.setup_treeview(self.tvFind, columns, types, None, True, True)

        # Brothers & sisters treeview
        columns = [_("Band no."), _("Year")]
        types = [str, str]
        self.lsBrothers, self.selBrothers = Widgets.setup_treeview(self.tvBrothers, columns, types, None, True, True)

        # Halfbrothers & sisters treeview
        columns = [_("Band no."), _("Year"), _("Common parent")]
        types = [str, str, str]
        self.lsHalfBrothers, self.selHalfBrothers = Widgets.setup_treeview(self.tvHalfBrothers, columns, types, None, True, True)

        # Offspring treeview
        columns = [_("Band no."), _("Year")]
        types = [str, str]
        self.lsOffspring, self.selOffspring = Widgets.setup_treeview(self.tvOffspring, columns, types, None, True, True)

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

        for pigeon in self.parser.pigeons:
            if not self.parser.pigeons[pigeon].show: continue
            if pigeonType == self.parser.pigeons[pigeon].sex or pigeonType == 'all':
                if self.options.optionList.column:
                    if self.options.optionList.columntype == _('Sex'):
                        extra = self.sexDic[self.parser.pigeons[pigeon].sex]
                    elif self.options.optionList.columntype == _('Colour'):
                        extra = self.parser.pigeons[pigeon].colour
                    self.liststore.append([pigeon, self.parser.pigeons[pigeon].year, self.parser.pigeons[pigeon].name, extra])
                else:
                    self.liststore.append([pigeon, self.parser.pigeons[pigeon].year, self.parser.pigeons[pigeon].name, None])

        if len(self.liststore) > 0:
            self.liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
            self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
            if path == None:
                path = 0
            self.treeview.set_cursor(path)
            self.treeview.set_property('has-focus', True)
        else:
            image = Const.IMAGEDIR + 'icon_logo.png'
            width = height = 75
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(image, width, height)
            self.imagePigeon.set_from_pixbuf(pixbuf)
            self.imagePigeon1.set_from_pixbuf(pixbuf)

    def set_multiple_sensitive(self, widgets, boolean):
        ''' 
        Set multiple widgets sensitive at once

        @param widgets: list of widgets
        @param bool: boolean 
        '''

        for item in widgets:
            attr = getattr(self, item)
            attr.set_sensitive(boolean)

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

    def selectionresult_changed(self, selection):
        '''
        Set the remove and edit result buttons sensitive when there is a result selected
        '''

        model, path = selection.get_selected()

        if path:
            self.removeresult.set_sensitive(True)
            self.editresult.set_sensitive(True)
        else:
            self.removeresult.set_sensitive(False)
            self.editresult.set_sensitive(False)

    def selection_changed(self, selection):
        '''
        Get all the data/info from the selected pigeon
        '''

        model, path = selection.get_selected()

        if path:
            self.set_multiple_sensitive(['edit', 'remove', 'sbdetail'], True)
        else:
            self.set_multiple_sensitive(['edit', 'remove', 'sbdetail'], False)
            self.empty_entryboxes()
            return

        self.empty_entryboxes()

        selected = model[path][0]

        ring     = self.parser.pigeons[selected].ring
        year     = self.parser.pigeons[selected].year[2:]
        sex      = self.parser.pigeons[selected].sex
        strain   = self.parser.pigeons[selected].strain
        loft     = self.parser.pigeons[selected].loft
        extra1   = self.parser.pigeons[selected].extra1
        extra2   = self.parser.pigeons[selected].extra2
        extra3   = self.parser.pigeons[selected].extra3
        extra4   = self.parser.pigeons[selected].extra4
        extra5   = self.parser.pigeons[selected].extra5
        extra6   = self.parser.pigeons[selected].extra6
        colour   = self.parser.pigeons[selected].colour
        name     = self.parser.pigeons[selected].name
        sire     = self.parser.pigeons[selected].sire
        yearsire = self.parser.pigeons[selected].yearsire
        dam      = self.parser.pigeons[selected].dam
        yeardam  = self.parser.pigeons[selected].yeardam

        self.entryRing.set_text(selected)
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
        self.entryYearSire.set_text(yearsire[2:])
        self.entryYearDam.set_text(yeardam[2:])

        if self.parser.pigeons[selected].image:
            image = self.parser.pigeons[selected].image
            width = height = 200
        else:
            image = Const.IMAGEDIR + 'icon_logo.png'
            width = height = 75
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(image, width, height)
            self.imagePigeon.set_from_pixbuf(pixbuf)
            self.imagePigeon1.set_from_pixbuf(pixbuf)
        except:
            print "File doesn't exist"

        if self.notebook.get_current_page() == 0:
            dp = DrawPedigree([self.tableSire, self.tableDam], selected, button=self.goto)
            dp.draw_pedigree()
        elif self.notebook.get_current_page() == 1:
            self.find_direct_relatives(ring, sire, dam)
            self.find_half_relatives(ring, sire, yearsire, dam, yeardam)
            self.find_offspring(ring, sire, dam)
        elif self.notebook.get_current_page() == 2:
            self.get_results(ring)

    def get_results(self, ring):
        '''
        Get all results of selected pigeon

        @param ring: the selected pigeon
        '''

        self.lsResult.clear()

        for result in self.database.get_pigeon_results(ring):
            date = result[2]
            point = result[3]
            place = result[4]
            out = result[5]
            sector = result[6]

            cof = (float(place)/float(out))*100

            self.lsResult.append([date, point, place, out, cof, sector])

        self.lsResult.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def find_direct_relatives(self, ring, sire, dam):
        '''
        Search all brothers and sisters of the selected pigeon.

        @param ring: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        '''

        self.lsBrothers.clear()

        if sire == '' or dam == '': return

        for pigeon in self.parser.pigeons:
            if sire == self.parser.pigeons[pigeon].sire and\
               dam == self.parser.pigeons[pigeon].dam and not\
               pigeon == ring:

                self.lsBrothers.append([pigeon, self.parser.pigeons[pigeon].year])

        self.lsBrothers.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.lsBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def find_half_relatives(self, ring, sire, yearsire, dam, yeardam):
        '''
        Search all halfbrothers and sisters of the selected pigeon.

        @param ring: the selected pigeon
        @param sire: sire of selected pigeon
        @param yearsire: year of the sire of selected pigeon
        @param dam: dam of selected pigeon
        @param yeardam: year of the dam of selected pigeon
        '''

        self.lsHalfBrothers.clear()

        for pigeon in self.parser.pigeons:

            if not sire == '':
                if sire == self.parser.pigeons[pigeon].sire\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.append([pigeon, self.parser.pigeons[pigeon].year, sire+'/'+yearsire[2:]])

            if not dam == '':
                if dam == self.parser.pigeons[pigeon].dam\
                and not (sire == self.parser.pigeons[pigeon].sire and\
                    dam == self.parser.pigeons[pigeon].dam):

                    self.lsHalfBrothers.append([pigeon, self.parser.pigeons[pigeon].year, dam+'/'+yeardam[2:]])

        self.lsHalfBrothers.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.lsHalfBrothers.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def find_offspring(self, ring, sire, dam):
        '''
        Find all youngsters of the selected pigeon.

        @param ring: the selected pigeon
        @param sire: sire of selected pigeon
        @param dam: dam of selected pigeon
        '''

        self.lsOffspring.clear()

        for pigeon in self.parser.pigeons:
            if self.parser.pigeons[pigeon].sire == ring or self.parser.pigeons[pigeon].dam == ring:

                self.lsOffspring.append([pigeon, self.parser.pigeons[pigeon].year])

        self.lsOffspring.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.lsOffspring.set_sort_column_id(1, gtk.SORT_ASCENDING)

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
            self.btnadd.set_property('visible', True)
        elif operation == 'edit':
            self.save.set_property('visible', True)
            self.beforeEditPath, focus = self.treeview.get_cursor()

        self.entryRing1.grab_focus()

        self.alignUnEdit.set_property('visible', False)
        self.alignEdit.set_property('visible', True)

        widgets = ['toolbar', 'notebook', 'treeview', 'vboxButtons']
        self.set_multiple_sensitive(widgets, False)

    def add_edit_finish(self):
        '''
        Do all the necessary things to finish editing or adding.
        '''

        self.parser.get_pigeons()

        self.fill_treeview(path=self.beforeEditPath)

        self.beforeEditPath = 0

        self.alignUnEdit.set_property('visible', True)
        self.alignEdit.set_property('visible', False)

        widgets = ['toolbar', 'notebook', 'treeview', 'vboxButtons']
        self.set_multiple_sensitive(widgets, True)

        self.btnadd.set_property('visible', False)
        self.save.set_property('visible', False)

    def get_add_edit_info(self):
        '''
        Return a tuple containig info about the editable widgets.
        '''

        imageTemp = ''

        try:
            imageTemp = self.database.get_image(self.entryRing1.get_text())
        except:
            pass

        if not imageTemp == '' and not self.imageDeleted == True:
            image = imageTemp
        else:
            image = self.imageToAdd

        self.imageDeleted = False

        infoTuple = (self.entryRing1.get_text(),\
                     self.calculate_year(self.entryYear1.get_text()),\
                     self.cbsex.get_active_text(),\
                     1,\
                     self.cbColour.child.get_text(),\
                     self.entryName1.get_text(),\
                     self.cbStrain.child.get_text(),\
                     self.cbLoft.child.get_text(),\
                     image,\
                     self.entrySireEdit.get_text(),\
                     self.calculate_year(self.entryYearSireEdit.get_text()),\
                     self.entryDamEdit.get_text(),\
                     self.calculate_year(self.entryYearDamEdit.get_text()),\
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
        infoTuple += (infoTuple[0],) # Add the band to the end
        self.database.update_pigeon(infoTuple)

        self.update_data(infoTuple)

    def write_new_pigeon(self):
        '''
        Write the new pigeon to the database
        '''

        infoTuple = self.get_add_edit_info()
        ring = infoTuple[0]

        #TODO; review this statement. Needs cleanup.
        if self.database.has_pigeon(ring):
            if self.parser.pigeons[ring].show:
                overwrite = Widgets.message_dialog('warning', Const.MSGEXIST, self.main)
                if overwrite == 'no':
                    return
            else:
                overwrite = Widgets.message_dialog('warning', Const.MSGSHOW, self.main)
                if overwrite == 'no':
                    return
                if overwrite == 'yes':
                    self.database.show_pigeon(ring, 1)
                    return

        self.database.insert_pigeon(infoTuple)

        self.update_data(infoTuple)

    def update_data(self, infoTuple):
        '''
        Update the data
        '''

        colour = infoTuple[4]
        if colour:
            self.database.insert_colour((colour, ))
            self.fill_list(self.cbColour, self.database.get_all_colours())

        strain = infoTuple[6]
        if strain:
            self.database.insert_strain((strain, ))
            self.fill_list(self.cbStrain, self.database.get_all_strains())

        loft = infoTuple[7]
        if loft:
            self.database.insert_loft((loft, ))
            self.fill_list(self.cbLoft, self.database.get_all_lofts())

    def calculate_year(self, year):
        '''
        Add 19 or 20 in front of the year.
        '''

        if not year:
            return ''

        year = int(year)
        if year in range(0, 50): #XXX
            year += 2000
        else:
            year += 1900

        return str(year)

    def set_default_image(self, widget):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(Const.IMAGEDIR + 'icon_logo.png', 75, 75)
        self.imagePigeon1.set_from_pixbuf(pixbuf)
        self.imageToAdd = ''
        self.imageDeleted = True

    def open_filedialog(self, widget=None):
        self.filedialog.show()

    def show_uri(self, screen, link):
        try:
            gtk.show_uri(screen, link, 0)
        except:
            pass

    def url_hook(self, about, link):
        self.show_uri(about.get_screen(), link)

    def email_hook(self, about, email):
        self.show_uri(about.get_screen(), "mailto:%s" % email)

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
        ring = model[path][0]
        year = model[path][1]

        return ring, year

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
            Widgets.message_dialog('error', Const.MSGEMPTY, self.main)
            return False

        try:
            datetime.datetime.strptime(date, self.date_format)
        except ValueError:
            Widgets.message_dialog('error', Const.MSGFORMAT, self.main)
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
                self.lsFind.append([pigeon, self.parser.pigeons[pigeon].year, self.parser.pigeons[pigeon].name])

        if len(self.lsFind) > 0:
            self.lsFind.set_sort_column_id(0, gtk.SORT_ASCENDING)
            self.lsFind.set_sort_column_id(1, gtk.SORT_ASCENDING)
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
        self.cbSerieSex = gtk.ComboBox(self.sexStore)
        for box in [self.cbsex, self.cbSerieSex]:
            cell = gtk.CellRendererText()
            box.pack_start(cell, True)
            box.add_attribute(cell, 'text', 1)
            box.show()

        self.table1.attach(self.cbSerieSex, 6, 7, 1, 2, gtk.SHRINK, gtk.FILL, 0, 0)
        self.table4.attach(self.cbsex, 1, 2, 1, 2, gtk.SHRINK, gtk.FILL, 0, 0)

    def set_filefilter(self):
        '''
        Set a file filter for supported image files
        '''

        supportedImages = ["png", "jpg", "bmp"]
        fileFilter = gtk.FileFilter()
        fileFilter.set_name(_("Images"))
        for item in supportedImages:
            fileFilter.add_mime_type("image/%s" %item)
            fileFilter.add_pattern("*.%s" %item)
        self.filedialog.add_filter(fileFilter)

    def set_completion(self, widget):
        '''
        Set entrycompletion on given widget

        @param widget: the widget to set entrycompletion
        '''

        completion = gtk.EntryCompletion()
        completion.set_model(widget.get_model())
        completion.set_minimum_key_length(1)
        completion.set_text_column(0)
        widget.child.set_completion(completion)

    def fill_list(self, widget, items):
        '''
        Fill the comboboxentry's with their data

        @param widget: the comboboxentry
        @param items: list of items to add
        '''

        model = widget.get_model()
        model.clear()
        items.sort()
        for item in items:
            model.append([item])

        number = len(model)
        if number > 10 and number <= 30:
            widget.set_wrap_width(2)
        elif number > 30:
            widget.set_wrap_width(3)

