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


import operator
import datetime

import gtk

from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import database
from pigeonplanner.ui import tools
from pigeonplanner.ui import utils
from pigeonplanner.ui.filechooser import PdfSaver
from pigeonplanner.core import config
from pigeonplanner.reportlib import (report, PRINT_ACTION_DIALOG,
                                     PRINT_ACTION_PREVIEW, PRINT_ACTION_EXPORT)
from pigeonplanner.reports.results import ResultsReport, ResultsReportOptions


(COL_RACE_KEY,
 COL_RACE_DATE,
 COL_RACE_RACEPOINT,
 COL_RACE_TYPE,
 COL_RACE_WIND,
 COL_RACE_WEATHER) = range(6)

(COL_RESULT_BAND,
 COL_RESULT_YEAR,
 COL_RESULT_PLACED,
 COL_RESULT_OUT,
 COL_RESULT_COEF,
 COL_RESULT_SECTOR,
 COL_RESULT_CATEGORY,
 COL_RESULT_COMMENT,
 COL_RESULT_PLACED_INT,
 COL_RESULT_COEF_FLOAT) = range(100, 110)


column2name = {
            COL_RACE_DATE: "date",
            COL_RACE_RACEPOINT: "point",
            COL_RACE_TYPE: "type",
            COL_RACE_WIND: "wind",
            COL_RACE_WEATHER: "weather",
            COL_RESULT_BAND: "band",
            COL_RESULT_YEAR: "year",
            COL_RESULT_PLACED_INT: "place",
            COL_RESULT_COEF_FLOAT: "coef",
            COL_RESULT_OUT: "out",
            COL_RESULT_SECTOR: "sector",
            COL_RESULT_CATEGORY: "category"
        }


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
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "ResultWindow.ui")

        self.pdfname = "%s_%s.pdf" % (_("Results"), datetime.date.today())
        self._filter_races = utils.TreeviewFilter()
        self._filter_results = utils.TreeviewFilter()
        self._results = {}

        self.widgets.sel_race = self.widgets.tv_race.get_selection()
        self.widgets.sel_race.connect("changed", self.on_sel_race_changed)
        self.widgets.sort_race = self.widgets.tv_race.get_model()
        self.widgets.filter_race = self.widgets.sort_race.get_model()
        self.widgets.filter_race.set_visible_func(self._visible_races_func)
        self.widgets.sort_result = self.widgets.tv_result.get_model()

        self._build_toolbar()
        self.fill_treeview()
        self.set_columns()

        self.widgets.combopoint.set_data(database.get_all_data(database.Tables.RACEPOINTS), sort=False, active=None)
        self.widgets.combosector.set_data(database.get_all_data(database.Tables.SECTORS), sort=False, active=None)
        self.widgets.combotype.set_data(database.get_all_data(database.Tables.TYPES), sort=False, active=None)
        self.widgets.combocategory.set_data(database.get_all_data(database.Tables.CATEGORIES), sort=False, active=None)
        self.widgets.comboweather.set_data(database.get_all_data(database.Tables.WEATHER), sort=False, active=None)
        self.widgets.combowind.set_data(database.get_all_data(database.Tables.WIND), sort=False, active=None)

        self.widgets.resultwindow.set_transient_for(parent)
        self.widgets.resultwindow.show()

    # Callbacks
    def on_close_window(self, widget, event=None):
        self.widgets.resultwindow.destroy()

    def on_close_filter(self, widget, event=None):
        self.widgets.filterdialog.hide()
        return True

    def on_filter_clicked(self, widget):
        self.widgets.filterdialog.show()

    def on_filterclear_clicked(self, widget):
        for combo in ["date", "year", "place", "out", "coef"]:
            getattr(self.widgets, "combo"+combo).set_active(0)
        for spin in ["year", "place", "out", "coef"]:
            getattr(self.widgets, "spin"+spin).set_value(0)
        for combo in ["point", "type", "wind", "weather", "sector", "category"]:
            getattr(self.widgets, "combo"+combo).child.set_text("")

        self.widgets.entrydate.set_text("")
        self.widgets.entryband.clear()
        self.widgets.checkclassified.set_active(False)

        self._filter_races.clear()
        self._filter_results.clear()
        self._save_filter_results()
        self.widgets.filter_race.refilter()

    def on_filtersearch_clicked(self, widget):
        # Races filter
        self._filter_races.clear()
        date = self.widgets.entrydate.get_text()
        dateop = self.widgets.combodate.get_operator()
        self._filter_races.add(COL_RACE_DATE, date, dateop)

        point = self.widgets.combopoint.child.get_text()
        self._filter_races.add(COL_RACE_RACEPOINT, point)

        ftype = self.widgets.combotype.child.get_text()
        self._filter_races.add(COL_RACE_TYPE, ftype)

        wind = self.widgets.combowind.child.get_text()
        self._filter_races.add(COL_RACE_WIND, wind)

        weather = self.widgets.comboweather.child.get_text()
        self._filter_races.add(COL_RACE_WEATHER, weather)

        # Results filter
        self._filter_results.clear()
        pindex = self.widgets.entryband.get_pindex()
        if pindex:
            band, year = common.get_band_from_pindex(pindex)
            self._filter_results.add(COL_RESULT_BAND, band)
            self._filter_results.add(COL_RESULT_YEAR, year, type_=int)

        year = self.widgets.spinyear.get_value_as_int()
        yearop = self.widgets.comboyear.get_operator()
        self._filter_results.add(COL_RESULT_YEAR, year, yearop, int)

        place = self.widgets.spinplace.get_value_as_int()
        placeop = self.widgets.comboplace.get_operator()
        self._filter_results.add(COL_RESULT_PLACED_INT, place, placeop, int)

        out = self.widgets.spinout.get_value_as_int()
        outop = self.widgets.comboout.get_operator()
        self._filter_results.add(COL_RESULT_OUT, out, outop, int)

        coef = self.widgets.spincoef.get_value()
        coefop = self.widgets.combocoef.get_operator()
        self._filter_results.add(COL_RESULT_COEF_FLOAT, coef, coefop, float)

        sector = self.widgets.combosector.child.get_text()
        self._filter_results.add(COL_RESULT_SECTOR, sector)

        category = self.widgets.combocategory.child.get_text()
        self._filter_results.add(COL_RESULT_CATEGORY, category)

        if self.widgets.checkclassified.get_active():
            self._filter_results.add(COL_RESULT_PLACED_INT, 0, operator.gt, int, True)

        self._save_filter_results()
        self.widgets.filter_race.refilter()

    def on_spinbutton_output(self, widget):
        value = widget.get_value_as_int()
        text = "" if value == 0 else str(value)
        widget.set_text(text)
        return True

    def on_mail_clicked(self, widget):
        #TODO: disabled for now. Remove?
        ##self._do_operation(const.MAIL)
        ##results = os.path.join(const.TEMPDIR, self.pdfname)
        ##maildialog.MailDialog(self.resultwindow, results)
        pass

    def on_save_clicked(self, widget):
        chooser = PdfSaver(self.widgets.resultwindow, self.pdfname)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            save_path = chooser.get_filename()
            self._do_operation(PRINT_ACTION_EXPORT, save_path)
        chooser.destroy()

    def on_preview_clicked(self, widget):
        self._do_operation(PRINT_ACTION_PREVIEW)

    def on_print_clicked(self, widget):
        self._do_operation(PRINT_ACTION_DIALOG)

    def on_sel_race_changed(self, selection):
        self.widgets.ls_result.clear()
        model, rowiter = selection.get_selected()
        if rowiter is None:
            return

        key = model.get_value(rowiter, COL_RACE_KEY)
        for result in self._results[key]["filtered"]:
            self.widgets.ls_result.append([result["band"], result["year"],
                                           result["placestr"], result["out"], result["coefstr"],
                                           result["sector"], result["category"],
                                           result["comment"], result["place"], result["coef"]])

    # Public methods
    def fill_treeview(self):
        self.widgets.ls_race.clear()
        self.widgets.ls_result.clear()
        counter = 0
        for race in database.get_all_races():
            self._results[counter] = {"results": [], "filtered": []}
            resultstmp = database.get_results_for_data({"date": race["date"], "point": race["point"]})
            for result in resultstmp:
                result = dict(result)
                band, year = common.get_band_from_pindex(result["pindex"])
                result["band"] = band
                result["year"] = year
                result["ring"] = "%s / %s" % (band, year[2:])
                result["coef"] = common.calculate_coefficient(result["place"], result["out"])

                if result["place"] == 0:
                    result["coefstr"] = "-"
                    result["placestr"] = "-"
                else:
                    result["coefstr"] = common.calculate_coefficient(result["place"], result["out"], True)
                    result["placestr"] = str(result["place"])
                self._results[counter]["results"].append(result)
                self._results[counter]["filtered"].append(result)

            self.widgets.ls_race.append([counter, race["date"], race["point"],
                                         race["type"], race["wind"], race["weather"]])
            counter += 1

    def set_columns(self):
        columnsdic = {2: config.get("columns.result-type"),
                      3: config.get("columns.result-wind"),
                      4: config.get("columns.result-weather")}
        for key, value in columnsdic.items():
            self.widgets.tv_race.get_column(key).set_visible(value)

        columnsdic = {4: config.get("columns.result-coef"),
                      5: config.get("columns.result-sector"),
                      6: config.get("columns.result-category"),
                      7: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.widgets.tv_result.get_column(key).set_visible(value)

    # Private methods
    def _build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(self.widgets.actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.widgets.resultwindow.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget("/Toolbar")
        self.widgets.vbox.pack_start(toolbar, False, False)

    def _visible_races_func(self, model, treeiter):
        for item in self._filter_races:
            modelvalue = model.get_value(treeiter, item.name)
            if not item.operator(modelvalue, item.value):
                return False

        if not self._filter_results.has_filters():
            # No result filters
            return True

        race_key = self.widgets.ls_race.get_value(treeiter, COL_RACE_KEY)
        return len(self._results[race_key]["filtered"]) > 0

    def _save_filter_results(self):
        if not self._filter_results.has_filters():
            for result in self._results.values():
                result["filtered"] = result["results"][:]
            return

        for row in self.widgets.ls_race:
            filtered = []
            race_key = self.widgets.ls_race.get_value(row.iter, COL_RACE_KEY)
            for result in self._results[race_key]["results"]:
                show = True
                for item in self._filter_results:
                    resultvalue = result[column2name[item.name]]
                    if not item.operator(item.type(resultvalue), item.type(item.value)):
                        show = False
                        break
                if show:
                    filtered.append(result)
            self._results[race_key]["filtered"] = filtered

        self.widgets.sel_race.emit("changed")

    def _do_operation(self, print_action, save_path=None):
        userinfo = common.get_own_address()
        if not tools.check_user_info(self.widgets.resultwindow, userinfo["name"]):
            return

        # data = [{"race": {}, "results": [{}, {}]}]
        data = []
        for row in self.widgets.sort_race:
            temp = {"race": {}, "results": []}
            # Get the wanted columns for the race
            for col in (COL_RACE_DATE, COL_RACE_RACEPOINT,
                        COL_RACE_TYPE, COL_RACE_WIND, COL_RACE_WEATHER):
                name = column2name[col]
                temp["race"][name] = self.widgets.sort_race.get_value(row.iter, col)
            # Get the filtered results for the race
            race_key = self.widgets.sort_race.get_value(row.iter, COL_RACE_KEY)
            temp["results"] = self._results[race_key]["filtered"][:]
            data.append(temp)

        psize = common.get_pagesize_from_opts()
        opts = ResultsReportOptions(psize, None, print_action, save_path,
                                           parent=self.widgets.resultwindow)
        report(ResultsReport, opts, data, userinfo)

