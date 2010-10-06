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
Results window class
"""


import os.path
import datetime

import gtk

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import printing
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import maildialog
from pigeonplanner.ui import toolswindow
from pigeonplanner.ui.widgets import menus
from pigeonplanner.ui.widgets import comboboxes


(KEY,
 PINDEX,
 DATE,
 POINT,
 PLACE,
 OUT,
 SECTOR,
 TYPE,
 CATEGORY,
 WIND,
 WEATHER,
 PUT,
 BACK,
 OWNPLACE,
 OWNOUT,
 COMMENT) = range(16)


class ResultWindow(builder.GtkBuilder):
    def __init__(self, main, pigeons, database):
        builder.GtkBuilder.__init__(self, const.GLADERESULT)

        self.main = main
        self.database = database
        self.pigeons = pigeons

        self.resultwindow.set_transient_for(self.main.mainwindow)

        self.filter_pigeons = []
        self.filter_pigeon_years = []
        self.filter_race_years = []
        self.filter_points = []
        self.filter_sectors = []

        self.build_toolbar()
        self.fill_treeview()
        self.liststore.foreach(self.fill_filters)

        self.pdfname = "%s_%s.pdf" %(_("Results"), datetime.date.today())

        self.resultwindow.show()

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_resultwindow)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.resultwindow.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)
        self.vbox.reorder_child(toolbar, 0)

    def create_action_group(self):
        action_group = gtk.ActionGroup("ResultWindowActions")
        action_group.add_actions((
            ("Save", gtk.STOCK_SAVE, None, None,
                    _("Save these results"), self.on_save_clicked),
            ("Mail", 'email', None, None,
                    _("Email these results"), self.on_mail_clicked),
            ("Preview", gtk.STOCK_PRINT_PREVIEW, None, None,
                    _("View these results"), self.on_preview_clicked),
            ("Print", gtk.STOCK_PRINT, None, None,
                    _("Print these results"), self.on_print_clicked),
            ("Filter", gtk.STOCK_CLEAR, _("_Filter..."), None,
                    _("Set filter options"), self.on_filter_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_window),
           ))

        return action_group

    def result_filter(self, result):
        if self.chkFilterPigeons.get_active():
            if not result[PINDEX] == self.cbFilterPigeons.get_active_text():
                return False

        if self.chkFilterPigeonYears.get_active():
            if not (self.pigeons[result[PINDEX]].year == 
                    self.cbFilterPigeonYears.get_active_text()):
                return False

        if self.chkFilterRaceYears.get_active():
            if not (result[DATE][:4] == 
                    self.cbFilterRaceYears.get_active_text()):
                return False

        if self.chkFilterPoints.get_active():
            if not result[POINT] == self.cbFilterPoints.get_active_text():
                return False

        if self.chkFilterSectors.get_active():
            if not result[SECTOR] == self.cbFilterSectors.get_active_text():
                return False

        if self.chkFilterCoef.get_active():
            coef = int(common.calculate_coefficient(result[PLACE],
                                                    result[OUT]))
            if not coef == self.sbFilterCoef.get_value_as_int():
                return False

        if self.chkFilterPlace.get_active():
            if not result[PLACE] == self.sbFilterPlace.get_value_as_int():
                return False

        return True

    def fill_treeview(self, filter_active=False):
        self.treeviewres.freeze_child_notify()
        self.treeviewres.set_model(None)

        self.liststore.set_default_sort_func(lambda *args: -1) 
        self.liststore.set_sort_column_id(-1, gtk.SORT_ASCENDING)

        self.liststore.clear()

        for result in self.database.get_all_results():
            if filter_active and not self.result_filter(result): continue

            pindex = result[PINDEX]
            place = result[PLACE]
            out = result[OUT]
            cof = (float(place)/float(out))*100
            try:
                year = self.pigeons[pindex].year
                ring = self.pigeons[pindex].ring
            except KeyError:
                # HACK Pigeon is removed but results are kept.
                #      Make the band with the pindex.
                ring, year = common.get_band_from_pindex(pindex)

            self.liststore.insert(0, [pindex, ring, year, result[DATE],
                                      result[POINT], place, out, cof,
                                      result[SECTOR], result[TYPE],
                                      result[CATEGORY], result[WEATHER],
                                      result[WIND], result[COMMENT]
                                ])

        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)

        self.treeviewres.set_model(self.liststore)
        self.treeviewres.thaw_child_notify()

    def on_close_window(self, widget, event=None):
        self.resultwindow.destroy()

    def on_filter_clicked(self, widget):
        filterdialog = dialogs.FilterDialog(self.resultwindow,
                                            _("Filter results"),
                                            self.fill_treeview)

        self.cbFilterPigeons = self.pigeons_combobox()
        self.chkFilterPigeons = filterdialog.add_filter_custom(
                                                    _("Pigeons"),
                                                    self.cbFilterPigeons)
        self.chkFilterPigeonYears, self.cbFilterPigeonYears = \
                                        filterdialog.add_filter_combobox(
                                                    _("Year of pigeon"),
                                                    self.filter_pigeon_years)
        self.chkFilterRaceYears, self.cbFilterRaceYears = \
                                        filterdialog.add_filter_combobox(
                                                    _("Year of race"),
                                                    self.filter_race_years)
        self.chkFilterPoints, self.cbFilterPoints = \
                                        filterdialog.add_filter_combobox(
                                                    _("Racepoint"),
                                                    self.filter_points)
        self.chkFilterSectors, self.cbFilterSectors = \
                                        filterdialog.add_filter_combobox(
                                                    _("Sector"),
                                                    self.filter_sectors)
        self.chkFilterCoef, self.sbFilterCoef = \
                                        filterdialog.add_filter_spinbutton(
                                                    _("Coefficient"))
        self.chkFilterPlace, self.sbFilterPlace = \
                                        filterdialog.add_filter_spinbutton(
                                                    _("Place"), 1)

        filterdialog.run()

    def on_mail_clicked(self, widget):
        self.do_operation('mail')
        results = os.path.join(const.TEMPDIR, self.pdfname)

        maildialog.MailDialog(self.resultwindow, self.database, results)

    def on_save_clicked(self, widget):
        self.do_operation('save')

    def on_preview_clicked(self, widget):
        self.do_operation('preview')

    def on_print_clicked(self, widget):
        self.do_operation('print')

    def do_operation(self, op):
        userinfo = common.get_own_address(self.main.database)

        if not toolswindow.edit_user_info(self.resultwindow, self.main,
                                          userinfo['name']):
            return

        results = []
        for item in self.liststore:
            values = []
            for x in range(2, 14):
                value = self.liststore.get_value(item.iter, x)
                if value == None:
                    value = ''
                if x == 2:
                    value = "%s / %s" %(self.liststore.get_value(item.iter, 1),
                                        value[2:])
                if x == 7:
                    value = '%3.2f' %value
                values.append(str(value))
            results.append(values)

        printing.PrintResults(self.resultwindow, results, userinfo,
                              self.main.options.optionList, op, self.pdfname)

    def fill_filters(self, model, path, treeiter):
        pindex, ring, year, date, point, sector = model.get(treeiter,
                                                            0, 1, 2, 3, 4, 8)
        if not pindex in self.filter_pigeons:
            self.filter_pigeons.append(pindex)
        if not year in self.filter_pigeon_years:
            self.filter_pigeon_years.append(year)
        if not date[:4] in self.filter_race_years:
            self.filter_race_years.append(date[:4])
        if not point in self.filter_points:
            self.filter_points.append(point)
        if not sector in self.filter_sectors:
            self.filter_sectors.append(sector)

    def pigeons_combobox(self):
        store = gtk.ListStore(str, str)
        for pindex in self.filter_pigeons:
            try:
                year = self.pigeons[pindex].year
                ring = self.pigeons[pindex].ring
            except KeyError:
                ring, year = common.get_band_from_pindex(pindex)
            band = "%s/%s" %(ring, year)
            store.append([pindex, band])
        cell = gtk.CellRendererText()
        combobox = gtk.ComboBox(store)
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_active(0)
        comboboxes.set_combobox_wrap(combobox)

        return combobox

