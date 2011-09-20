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

import const
import common
import builder
import printing
from ui import tools
from ui import dialogs
from ui import maildialog
from ui.widgets import comboboxes
from translation import gettext as _


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
    ui = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <toolitem action="Mail"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Filter"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""
    def __init__(self, parent, parser, database, options):
        builder.GtkBuilder.__init__(self, "ResultWindow.ui")

        self.database = database
        self.parser = parser
        self.options = options
        self.pdfname = "%s_%s.pdf" % (_("Results"), datetime.date.today())

        self.filters = []
        self.filter_pigeons = []
        self.filter_pigeon_years = []
        self.filter_race_years = []
        self.filter_points = []
        self.filter_sectors = []
        self.cols = {'pigeon': 0, 'pyear': 2, 'ryear': 3, 'race': 4,
                     'place': 5, 'coef': 7, 'sector': 8}

        self._build_toolbar()
        self._modelsort = self.treeview.get_model()
        self._modelsort.set_sort_func(2, self._sort_func)
        self._modelsort.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self._modelfilter = self._modelsort.get_model()
        self._modelfilter.set_visible_func(self._visible_func)
        self.fill_treeview()
        self.set_columns()

        self.resultwindow.set_transient_for(parent)
        self.resultwindow.show()

    # Callbacks
    def on_close_window(self, widget, event=None):
        self.resultwindow.destroy()

    def on_filterapply_clicked(self, widget):
        self.filters = widget.get_filters()
        self._modelfilter.refilter()

    def on_filterclear_clicked(self, widget):
        self.filters = widget.get_filters()
        self._modelfilter.refilter()

    def on_filter_clicked(self, widget):
        dialog = dialogs.FilterDialog(self.resultwindow, _("Filter results"))
        dialog.connect('apply-clicked', self.on_filterapply_clicked)
        dialog.connect('clear-clicked', self.on_filterclear_clicked)

        combo = self._get_pigeons_combobox()
        dialog.add_custom('pigeon', _("Pigeons"), combo, combo.get_active_text)
        dialog.add_combobox('pyear', _("Year of pigeon"), self.filter_pigeon_years)
        dialog.add_combobox('ryear', _("Year of race"), self.filter_race_years)
        dialog.add_combobox('race', _("Racepoint"), self.filter_points)
        dialog.add_combobox('sector', _("Sector"), self.filter_sectors)
        dialog.add_spinbutton('coef', _("Coefficient"))
        dialog.add_spinbutton('place', _("Place"), 1)

        self.filters = dialog.get_filters()
        dialog.run()

    def on_mail_clicked(self, widget):
        self._do_operation(const.MAIL)
        results = os.path.join(const.TEMPDIR, self.pdfname)

        maildialog.MailDialog(self.resultwindow, self.database, results)

    def on_save_clicked(self, widget):
        self._do_operation(const.SAVE)

    def on_preview_clicked(self, widget):
        self._do_operation(const.PREVIEW)

    def on_print_clicked(self, widget):
        self._do_operation(const.PRINT)

    # Public methods
    def fill_treeview(self):
        self.treeview.freeze_child_notify()
        self.treeview.set_model(None)

        self.liststore.set_default_sort_func(lambda *args: -1) 
        self.liststore.set_sort_column_id(-1, gtk.SORT_ASCENDING)
        self.liststore.clear()
        for result in self.database.get_all_results():
            pindex = result[PINDEX]
            date = result[DATE]
            point = result[POINT]
            sector = result[SECTOR]
            place = result[PLACE]
            out = result[OUT]
            cof = common.calculate_coefficient(place, out)
            ring, year = common.get_band_from_pindex(pindex)
            self.liststore.insert(0, [pindex, ring, year, date, point,
                                      place, out, cof, sector, result[TYPE],
                                      result[CATEGORY], result[WIND],
                                      result[WEATHER], result[COMMENT]])
            self._add_filter_data(pindex, year, date, point, sector)
        self.treeview.set_model(self._modelsort)
        self.treeview.thaw_child_notify()

    def set_columns(self):
        columnsdic = {6: self.options.colcoef,
                      7: self.options.colsector,
                      8: self.options.coltype,
                      9: self.options.colcategory,
                      10: self.options.colwind,
                      11: self.options.colweather,
                      12: self.options.colcomment}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

    # Private methods
    def _build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(self.actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.resultwindow.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)

    def _get_pigeons_combobox(self):
        store = gtk.ListStore(str, str)
        for pindex in self.filter_pigeons:
            ring, year = common.get_band_from_pindex(pindex)
            band = "%s/%s" % (ring, year)
            store.append([pindex, band])
        cell = gtk.CellRendererText()
        combobox = gtk.ComboBox(store)
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_active(0)
        comboboxes.set_combobox_wrap(combobox)
        return combobox

    def _add_filter_data(self, pindex, year, date, point, sector):
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

    def _visible_func(self, model, treeiter):
        for name, check, widget in self.filters:
            data = model.get_value(treeiter, self.cols[name])
            if name == 'ryear':
                data = data[:4]
            if check.get_active() and not data == widget.get_data():
                return False
        return True

    def _sort_func(self, model, iter1, iter2):
        data1 = model.get_value(iter1, 2)
        data2 = model.get_value(iter2, 2)
        if data1 == data2:
            data1 = model.get_value(iter1, 1)
            data2 = model.get_value(iter2, 1)
        return cmp(data1, data2)

    def _do_operation(self, op):
        userinfo = common.get_own_address(self.database)

        if not tools.check_user_info(self.resultwindow, self.database,
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
                    value = "%s / %s" % (self.liststore.get_value(item.iter, 1),
                                         value[2:])
                if x == 7:
                    value = '%3.2f' % value
                values.append(str(value))
            results.append(values)

        printing.PrintResults(self.resultwindow, results, userinfo,
                              self.options, op, self.pdfname)

