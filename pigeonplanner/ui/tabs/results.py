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
from pigeonplanner import config
from pigeonplanner import errors
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner import database
from pigeonplanner.ui import utils
from pigeonplanner.ui import resultwindow
from pigeonplanner.ui import resultparser
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.messagedialog import ErrorDialog, QuestionDialog


class ResultsTab(builder.GtkBuilder, basetab.BaseTab):
    (COL_ID,
     COL_DATE,
     COL_RACEPOINT,
     COL_PLACED,
     COL_OUT,
     COL_COEF,
     COL_SECTOR,
     COL_TYPE,
     COL_CATEGORY,
     COL_WIND,
     COL_WEATHER,
     COL_COMMENT) = range(12)

    def __init__(self, parent, database, parser):
        builder.GtkBuilder.__init__(self, "ResultsView.ui")
        basetab.BaseTab.__init__(self, _("Results"), "icon_result.png")

        self.parent = parent
        self.database = database
        self.parser = parser
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect('changed', self.on_selection_changed)
        self.set_columns()

        self.widgets.comboracepoint.set_data(self.database, self.database.RACEPOINTS)
        self.widgets.combosector.set_data(self.database, self.database.SECTORS)
        self.widgets.combotype.set_data(self.database, self.database.TYPES)
        self.widgets.combocategory.set_data(self.database, self.database.CATEGORIES)
        self.widgets.comboweather.set_data(self.database, self.database.WEATHER)
        self.widgets.combowind.set_data(self.database, self.database.WIND)

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
        resultwindow.ResultWindow(self.parent, self.parser, self.database)

    def on_buttonimport_clicked(self, widget):
        resultparser.ResultParser(self.parent, self.database, 
                                  self.parser.pigeons.keys())

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        values = [common.get_date(), '', 1, 1, '', '', '', '', '', '']
        self._set_dialog(self._mode, values)

    def on_buttonedit_clicked(self, widget):
        result = self._get_selected_result()
        for index, item in enumerate(result):
            # Happens on conversion from 0.6.0 to 0.7.0
            if item is None:
                result[index] = ''

        self._mode = const.EDIT
        del result[self.COL_COEF] # Delete the coefficient
        del result[self.COL_ID] # Delete the row id
        self._set_dialog(self._mode, result)

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.liststore.get_path(rowiter)
        rowid = model[rowiter][self.COL_ID]

        if not QuestionDialog(messages.MSG_REMOVE_RESULT, self.parent).run():
            return

        self.database.delete_from_table(self.database.RESULTS, rowid, 0)
        self.widgets.liststore.remove(rowiter)
        self.widgets.selection.select_path(path)

    def on_buttonclose_clicked(self, widget):
        self.widgets.dialog.hide()

    def on_buttonsave_clicked(self, widget):
        data = self._get_data()
        if data is None: return
        (date, point, place, out, sector, ftype, category, wind, weather,
            comment) = data
        cof = common.calculate_coefficient(place, out)
        # Not implemented yet, but have a database column
        values = ['', '', 0, 0]
        values.reverse()
        for value in values:
            data.insert(9, value)
        if self._mode == const.ADD:
            data.insert(0, self.pindex)
            if self.database.has_result(data):
                ErrorDialog(messages.MSG_RESULT_EXISTS, self.parent)
                return
            rowid = self.database.insert_into_table(self.database.RESULTS, data)
            rowiter = self.widgets.liststore.insert(0, [rowid, date, point, place,
                                                out, cof, sector, ftype,
                                                category, wind, weather, comment])
            self.widgets.selection.select_iter(rowiter)
            path = self.widgets.liststore.get_path(rowiter)
            self.widgets.treeview.scroll_to_cell(path)
        elif self._mode == const.EDIT:
            model, node = self.widgets.selection.get_selected()
            data.append(self.widgets.liststore.get_value(node, 0))
            self.database.update_table(self.database.RESULTS, data, 2, 0)
            self.widgets.liststore.set(node, 1, date, 2, point, 3, place, 4, out,
                                             5, cof, 6, sector, 7, ftype, 8, category,
                                             9, wind, 10, weather, 11, comment)
            self.widgets.selection.emit('changed')
            self.widgets.dialog.hide()

        data = [(self.widgets.comboracepoint, point, self.database.RACEPOINTS),
                (self.widgets.combosector, sector, self.database.SECTORS),
                (self.widgets.combotype, ftype, self.database.TYPES),
                (self.widgets.combocategory, category, self.database.CATEGORIES),
                (self.widgets.comboweather, weather, self.database.WEATHER),
                (self.widgets.combowind, wind, self.database.WIND)]
        for combo, value, table in data:
            self._insert_combo_data(combo, value, table)

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        utils.set_multiple_sensitive(widgets, not rowiter is None)

    def on_spinplaced_changed(self, widget):
        self.widgets.spinoutof.set_range(widget.get_value_as_int(),
                                         widget.get_range()[1])

    # Public methods
    def set_pigeon(self, pigeon):
        band = pigeon.get_band_string()
        self.widgets.labelpigeon.set_text(band)
        self.pindex = pigeon.get_pindex()
        self.widgets.treeview.freeze_child_notify()
        self.widgets.treeview.set_model(None)

        self.widgets.liststore.set_default_sort_func(lambda *args: -1) 
        self.widgets.liststore.set_sort_column_id(-1, gtk.SORT_ASCENDING)

        self.widgets.liststore.clear()
        for result in self.database.get_pigeon_results(self.pindex):
            place = result[4]
            out = result[5]
            cof = common.calculate_coefficient(place, out)
            self.widgets.liststore.insert(0, [result[0], result[2], result[3],
                                              place, out, cof,
                                              result[6], result[7], result[8],
                                              result[9], result[10], result[15]])
        self.widgets.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.widgets.treeview.set_model(self.widgets.liststore)
        self.widgets.treeview.thaw_child_notify()

    def clear_pigeon(self):
        self.widgets.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    def add_new_result(self):
        self.widgets.buttonadd.clicked()

    def set_columns(self):
        columnsdic = {4: config.get('columns.result-coef'),
                      5: config.get('columns.result-sector'),
                      6: config.get('columns.result-type'),
                      7: config.get('columns.result-category'),
                      8: config.get('columns.result-wind'),
                      9: config.get('columns.result-weather'),
                      10: config.get('columns.result-comment')}
        for key, value in columnsdic.items():
            self.widgets.treeview.get_column(key).set_visible(value)

    # Internal methods
    def _get_selected_result(self):
        model, rowiter = self.widgets.selection.get_selected()
        if not rowiter: return
        return list(model[rowiter])

    def _get_data(self):
        try:
            date = self.widgets.entrydate.get_text()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.widgets.dialog)
            return
        point = self.widgets.comboracepoint.child.get_text()
        place = self.widgets.spinplaced.get_value_as_int()
        out = self.widgets.spinoutof.get_value_as_int()
        sector = self.widgets.combosector.child.get_text()
        ftype = self.widgets.combotype.child.get_text()
        category = self.widgets.combocategory.child.get_text()
        weather = self.widgets.comboweather.child.get_text()
        wind = self.widgets.combowind.child.get_text()
        comment = self.widgets.entrycomment.get_text()

        if not date or not point or not place or not out:
            ErrorDialog(messages.MSG_EMPTY_DATA, self.dialog)
            return
        return [date, point, place, out, sector, ftype, category,
                wind, weather, comment]

    def _set_dialog(self, mode, values):
        """
        Set the dialog in the correct state

        @param mode: add or edit mode
        @param values: the values for the entry widgets
        """

        self._set_entry_values(values)
        text = _('Edit result for:') if mode == const.EDIT else _('Add result for:')
        self.widgets.labelmode.set_text(text)
        self.widgets.dialog.set_modal(mode == const.EDIT)
        self.widgets.dialog.show()
        self.widgets.entrydate.grab_focus()

    def _set_entry_values(self, values):
        self.widgets.entrydate.set_text(values[0])
        self.widgets.comboracepoint.child.set_text(values[1])
        self.widgets.spinplaced.set_value(values[2])
        self.widgets.spinoutof.set_value(values[3])
        self.widgets.combosector.child.set_text(values[4])
        self.widgets.combotype.child.set_text(values[5])
        self.widgets.combocategory.child.set_text(values[6])
        self.widgets.comboweather.child.set_text(values[7])
        self.widgets.combowind.child.set_text(values[8])
        self.widgets.entrycomment.set_text(values[9])

    def _insert_combo_data(self, combo, data, table):
        if not data: return
        # Racepoint table has more columns
        row = (data,) if not table == self.database.RACEPOINTS else (data, "", "", "", "")
        try:
            self.database.insert_into_table(table, row)
        except database.InvalidValueError:
            return
        model = combo.get_model()
        for treerow in model:
            if data in treerow:
                return
        model.append([data])
        model.set_sort_column_id(0, gtk.SORT_ASCENDING)

