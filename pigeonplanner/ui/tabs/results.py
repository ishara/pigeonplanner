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


import gtk

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner import database
from pigeonplanner import pigeonparser
from pigeonplanner.ui import utils
from pigeonplanner.ui import resultwindow
from pigeonplanner.ui import resultparser
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.messagedialog import ErrorDialog, QuestionDialog
from pigeonplanner.core import errors
from pigeonplanner.core import config


(COL_DATE,
 COL_RACEPOINT,
 COL_TYPE,
 COL_WIND,
 COL_WEATHER) = range(5)

(COL_ID,
 COL_PLACED,
 COL_OUT,
 COL_COEF,
 COL_SECTOR,
 COL_CATEGORY,
 COL_COMMENT) = range(7)


class ResultsTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "ResultsView.ui")
        basetab.BaseTab.__init__(self, _("Results"), "icon_result.png")

        self.parent = parent
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)
        self.widgets.race_sel = self.widgets.race_tv.get_selection()
        self.widgets.race_sel.connect("changed", self.on_race_sel_changed)
        self.set_columns()

        self.widgets.comboracepoint.set_data(database.get_all_data(database.Tables.RACEPOINTS), sort=False)
        self.widgets.combosector.set_data(database.get_all_data(database.Tables.SECTORS), sort=False)
        self.widgets.combotype.set_data(database.get_all_data(database.Tables.TYPES), sort=False)
        self.widgets.combocategory.set_data(database.get_all_data(database.Tables.CATEGORIES), sort=False)
        self.widgets.comboweather.set_data(database.get_all_data(database.Tables.WEATHER), sort=False)
        self.widgets.combowind.set_data(database.get_all_data(database.Tables.WIND), sort=False)

        self.widgets.dialog.set_transient_for(parent)

    # Callbacks
    def on_dialog_delete(self, widget, event):
        self.widgets.dialog.hide()
        return True

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_buttonedit_clicked, None),
                (gtk.STOCK_REMOVE, self.on_buttonremove_clicked, None)]
            utils.popup_menu(event, entries)

    def on_buttonall_clicked(self, widget):
        resultwindow.ResultWindow(self.parent)

    def on_buttonimport_clicked(self, widget):
        resultparser.ResultParser(self.parent, pigeonparser.parser.pigeons.keys())

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        values = [common.get_date(), "", 1, 1, "", "", "", "", "", ""]
        self._set_dialog(self._mode, values)

    def on_buttonedit_clicked(self, widget):
        # Columns could contain None prior to 0.7.0, convert to empty string
        model, rowiter = self.widgets.selection.get_selected()
        model_race, rowiter_race = self.widgets.race_sel.get_selected()
        result = [model_race.get_value(rowiter_race, COL_DATE) or "",
                  model_race.get_value(rowiter_race, COL_RACEPOINT) or "",
                  model.get_value(rowiter, COL_PLACED) or "",
                  model.get_value(rowiter, COL_OUT) or "",
                  model.get_value(rowiter, COL_SECTOR) or "",
                  model_race.get_value(rowiter_race, COL_TYPE) or "",
                  model.get_value(rowiter, COL_CATEGORY) or "",
                  model_race.get_value(rowiter_race, COL_WEATHER) or "",
                  model_race.get_value(rowiter_race, COL_WIND) or "",
                  model.get_value(rowiter, COL_COMMENT) or "",
                  ]
        self._mode = const.EDIT
        self._set_dialog(self._mode, result)

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.liststore.get_path(rowiter)
        if not QuestionDialog(messages.MSG_REMOVE_RESULT, self.parent).run():
            return

        database.remove_result(model[rowiter][COL_ID])
        self.widgets.liststore.remove(rowiter)
        self.widgets.selection.select_path(path)

        if len(self.widgets.liststore) == 0:
            model, rowiter = self.widgets.race_sel.get_selected()
            self.widgets.race_ls.remove(rowiter)

    def on_buttonclose_clicked(self, widget):
        self.widgets.dialog.hide()

    def on_buttonsave_clicked(self, widget):
        data = self._get_data()
        if data is None: return
        place = data["place"]
        if place == 0:
            cof = "-"
            place = "-"
        else:
            cof = common.calculate_coefficient(place, data["out"], True)
        if self._mode == const.ADD:
            data["pindex"] = self.pindex
            if database.result_exists(data):
                ErrorDialog(messages.MSG_RESULT_EXISTS, self.parent)
                return

            if not database.get_results_for_pigeon(self.pindex, data["date"], data["point"]):
                rowiter = self.widgets.race_ls.insert(0, [data["date"], data["point"],
                                            data["type"], data["wind"], data["weather"]])
                self.widgets.race_ls.set_sort_column_id(0, gtk.SORT_ASCENDING)
                self.widgets.race_sel.select_iter(rowiter)
                path = self.widgets.race_ls.get_path(rowiter)
                self.widgets.race_tv.scroll_to_cell(path)
            else:
                model, node = self.widgets.race_sel.get_selected()
                self.widgets.race_ls.set(node, COL_DATE, data["date"],
                                               COL_RACEPOINT, data["point"],
                                               COL_TYPE, data["type"],
                                               COL_WIND, data["wind"],
                                               COL_WEATHER, data["weather"])
            database.add_result(data)
        elif self._mode == const.EDIT:
            model, node = self.widgets.selection.get_selected()
            key = self.widgets.liststore.get_value(node, 0)
            database.update_result_for_key(key, data)
            self.widgets.liststore.set(node, COL_PLACED, str(data["place"]),
                                             COL_OUT, data["out"],
                                             COL_COEF, str(cof),
                                             COL_SECTOR, data["sector"],
                                             COL_CATEGORY, data["category"],
                                             COL_COMMENT, data["comment"])
            model, node = self.widgets.race_sel.get_selected()
            self.widgets.race_ls.set(node, COL_DATE, data["date"],
                                           COL_RACEPOINT, data["point"],
                                           COL_TYPE, data["type"],
                                           COL_WIND, data["wind"],
                                           COL_WEATHER, data["weather"])
            self.widgets.dialog.hide()

        database.update_result_as_race(data["date"], data["point"],
                                       data["sector"], data["wind"], data["weather"])
        self.widgets.race_sel.emit("changed")

        data = [(self.widgets.comboracepoint, data["point"], database.Tables.RACEPOINTS),
                (self.widgets.combosector, data["sector"], database.Tables.SECTORS),
                (self.widgets.combotype, data["type"], database.Tables.TYPES),
                (self.widgets.combocategory, data["category"], database.Tables.CATEGORIES),
                (self.widgets.comboweather, data["weather"], database.Tables.WEATHER),
                (self.widgets.combowind, data["wind"], database.Tables.WIND)]
        for combo, value, table in data:
            database.add_data(table, value)
            combo.add_item(value)

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        utils.set_multiple_sensitive(widgets, not rowiter is None)

    def on_race_sel_changed(self, selection):
        model, rowiter = selection.get_selected()
        if rowiter is None:
            return

        date = model.get_value(rowiter, 0)
        racepoint = model.get_value(rowiter, 1)
        self.widgets.liststore.clear()
        for result in database.get_results_for_pigeon(self.pindex, date, racepoint):
            place = result[4]
            out = result[5]
            if place == 0:
                cof = "-"
                place = "-"
            else:
                cof = common.calculate_coefficient(place, out, True)
            self.widgets.liststore.append([result[0], str(place), out, str(cof),
                                           result[6], result[8], result[15]])

    def on_checkplaced_toggled(self, widget):
        sensitive = widget.get_active()
        self.widgets.spinplaced.set_sensitive(sensitive)

    def on_spinplaced_changed(self, widget):
        self.widgets.spinoutof.set_range(widget.get_value_as_int(),
                                         widget.get_range()[1])

    def on_entrydate_changed(self, widget):
        self._autofill_race()

    def on_comboracepoint_changed(self, widget):
        self._autofill_race()

    # Public methods
    def set_pigeon(self, pigeon):
        band = pigeon.get_band_string()
        self.widgets.labelpigeon.set_text(band)
        self.pindex = pigeon.get_pindex()

        self.widgets.liststore.clear()
        self.widgets.race_ls.clear()
        for race in database.get_races_for_pigeon(self.pindex):
            self.widgets.race_ls.append([race[2], race[3], race[7], race[9], race[10]])

    def clear_pigeon(self):
        self.widgets.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    def add_new_result(self):
        self.widgets.buttonadd.clicked()

    def set_columns(self):
        columnsdic = {2: config.get("columns.result-coef"),
                      3: config.get("columns.result-sector"),
                      4: config.get("columns.result-category"),
                      5: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.widgets.treeview.get_column(key).set_visible(value)

        columnsdic = {2: config.get("columns.result-type"),
                      3: config.get("columns.result-wind"),
                      4: config.get("columns.result-weather")}
        for key, value in columnsdic.items():
            self.widgets.race_tv.get_column(key).set_visible(value)

    # Internal methods
    def _get_data(self):
        try:
            date = self.widgets.entrydate.get_text()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.widgets.dialog)
            return
        point = self.widgets.comboracepoint.child.get_text()
        if self.widgets.checkplaced.get_active():
            place = self.widgets.spinplaced.get_value_as_int()
        else:
            place = 0
        out = self.widgets.spinoutof.get_value_as_int()
        sector = self.widgets.combosector.child.get_text()
        ftype = self.widgets.combotype.child.get_text()
        category = self.widgets.combocategory.child.get_text()
        weather = self.widgets.comboweather.child.get_text()
        wind = self.widgets.combowind.child.get_text()
        comment = self.widgets.entrycomment.get_text()

        if not date or not point or not out:
            ErrorDialog(messages.MSG_EMPTY_DATA, self.widgets.dialog)
            return
        return {"date": date, "point": point, "place": place, "out": out,
                "sector": sector, "type": ftype, "category": category,
                "wind": wind, "weather": weather, "comment": comment}

    def _set_dialog(self, mode, values):
        """
        Set the dialog in the correct state

        @param mode: add or edit mode
        @param values: the values for the entry widgets
        """

        self._set_entry_values(values)
        text = _("Edit result for:") if mode == const.EDIT else _("Add result for:")
        self.widgets.labelmode.set_text(text)
        #TODO: Setting modal doesn't work
        self.widgets.dialog.set_modal(mode == const.EDIT)
        self.widgets.dialog.show()
        self.widgets.entrydate.grab_focus()

    def _set_entry_values(self, values):
        placed = values[2]
        if placed == "0" or placed == "-":
            self.widgets.checkplaced.set_active(False)
            placed = 1
        else:
            self.widgets.checkplaced.set_active(True)

        self.widgets.entrydate.set_text(values[0])
        self.widgets.comboracepoint.child.set_text(values[1])
        self.widgets.spinplaced.set_value(int(placed))
        self.widgets.spinoutof.set_value(values[3])
        self.widgets.combosector.child.set_text(values[4])
        self.widgets.combotype.child.set_text(values[5])
        self.widgets.combocategory.child.set_text(values[6])
        self.widgets.comboweather.child.set_text(values[7])
        self.widgets.combowind.child.set_text(values[8])
        self.widgets.entrycomment.set_text(values[9])

    def _autofill_race(self):
        date = self.widgets.entrydate.get_text()
        racepoint = self.widgets.comboracepoint.child.get_text()
        if date == "" or racepoint == "":
            # Don't bother checking
            return
        race = database.get_race_info(date, racepoint)
        if race is not None:
            ftype, wind, weather = race["type"], race["wind"], race["weather"]
        else:
            ftype, wind, weather = "", "", ""
        self.widgets.combotype.child.set_text(ftype)
        self.widgets.combowind.child.set_text(wind)
        self.widgets.comboweather.child.set_text(weather)

