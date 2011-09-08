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

import const
import common
import errors
import builder
import messages
from ui import dialogs
from ui import resultwindow
from ui import resultparser
from ui.tabs import basetab
from ui.widgets import date
from ui.widgets import menus
from ui.widgets import comboboxes
from translation import gettext as _


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

    def __init__(self, parent, database, options, parser):
        basetab.BaseTab.__init__(self, _("Results"), "icon_result.png")
        builder.GtkBuilder.__init__(self, "ResultsView.ui")

        self.parent = parent
        self.database = database
        self.options = options
        self.parser = parser
        self.entrydate = date.DateEntry(True)
        self.table.attach(self.entrydate, 1, 2, 0, 1, 0)
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)
        self.set_columns()
        combos = {self.combosector: self.database.SECTORS,
                  self.combotype: self.database.TYPES,
                  self.combocategory: self.database.CATEGORIES,
                  self.comboracepoint: self.database.RACEPOINTS,
                  self.comboweather: self.database.WEATHER,
                  self.combowind: self.database.WIND}
        for combo, data in combos.items():
            comboboxes.fill_combobox(combo, self.database.select_from_table(data))
            comboboxes.set_entry_completion(combo)
        self._root.unparent()
        self.dialog.set_transient_for(parent)

    # Callbacks
    def on_dialog_delete(self, widget, event):
        self.dialog.hide()
        return True

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_buttonedit_clicked, None),
                (gtk.STOCK_REMOVE, self.on_buttonremove_clicked, None)]
            menus.popup_menu(event, entries)

    def on_buttonall_clicked(self, widget):
        resultwindow.ResultWindow(self.parent, self.parser,
                                  self.database, self.options)

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
        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        rowid = model[rowiter][self.COL_ID]

        d = dialogs.MessageDialog(const.QUESTION,
                                  messages.MSG_REMOVE_RESULT,
                                  self.parent)
        if not d.yes:
            return

        self.database.delete_from_table(self.database.RESULTS, rowid, 0)
        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def on_buttonclose_clicked(self, widget):
        self.dialog.hide()

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
                dialogs.MessageDialog(const.ERROR, messages.MSG_RESULT_EXISTS,
                                      self.parent)
                return
            rowid = self.database.insert_into_table(self.database.RESULTS, data)
            rowiter = self.liststore.insert(0, [rowid, date, point, place,
                                                out, cof, sector, ftype,
                                                category, wind, weather, comment])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        elif self._mode == const.EDIT:
            model, node = self._selection.get_selected()
            data.append(self.liststore.get_value(node, 0))
            self.database.update_table(self.database.RESULTS, data, 2, 0)
            self.liststore.set(node, 1, date, 2, point, 3, place, 4, out,
                                     5, cof, 6, sector, 7, ftype, 8, category,
                                     9, wind, 10, weather, 11, comment)
            self._selection.emit('changed')
            self.dialog.hide()

        data = [(self.comboracepoint, point, self.database.RACEPOINTS),
                (self.combosector, sector, self.database.SECTORS),
                (self.combotype, ftype, self.database.TYPES),
                (self.combocategory, category, self.database.CATEGORIES),
                (self.comboweather, weather, self.database.WEATHER),
                (self.combowind, wind, self.database.WIND)]
        for combo, value, table in data:
            self._insert_combo_data(combo, value, table)

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.buttonremove, self.buttonedit]
        self.set_multiple_sensitive(widgets, not rowiter is None)

    def on_spinplaced_changed(self, widget):
        self.spinoutof.set_range(widget.get_value_as_int(),
                                 widget.get_range()[1])

    # Public methods
    def fill_treeview(self, pigeon):
        band = pigeon.get_band_string()
        self.labelpigeon.set_text(band)
        self.pindex = pigeon.get_pindex()
        self.treeview.freeze_child_notify()
        self.treeview.set_model(None)

        self.liststore.set_default_sort_func(lambda *args: -1) 
        self.liststore.set_sort_column_id(-1, gtk.SORT_ASCENDING)

        self.liststore.clear()
        for result in self.database.get_pigeon_results(self.pindex):
            place = result[4]
            out = result[5]
            cof = common.calculate_coefficient(place, out)
            self.liststore.insert(0, [result[0], result[2], result[3],
                                      place, out, cof,
                                      result[6], result[7], result[8],
                                      result[9], result[10], result[15]])
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.treeview.set_model(self.liststore)
        self.treeview.thaw_child_notify()

    def add_new_result(self):
        self.buttonadd.clicked()

    def set_columns(self):
        columnsdic = {4: self.options.colcoef,
                      5: self.options.colsector,
                      6: self.options.coltype,
                      7: self.options.colcategory,
                      8: self.options.colwind,
                      9: self.options.colweather,
                      10: self.options.colcomment}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

    # Internal methods
    def _get_selected_result(self):
        model, rowiter = self._selection.get_selected()
        if not rowiter: return
        return list(model[rowiter])

    def _get_data(self):
        try:
            date = self.entrydate.get_text()
        except errors.InvalidInputError, msg:
            dialogs.MessageDialog(const.ERROR, msg.value, self.dialog)
            return
        point = self.comboracepoint.child.get_text()
        place = self.spinplaced.get_value_as_int()
        out = self.spinoutof.get_value_as_int()
        sector = self.combosector.child.get_text()
        ftype = self.combotype.child.get_text()
        category = self.combocategory.child.get_text()
        weather = self.comboweather.child.get_text()
        wind = self.combowind.child.get_text()
        comment = self.entrycomment.get_text()

        if not date or not point or not place or not out:
            dialogs.MessageDialog(const.ERROR, messages.MSG_EMPTY_DATA,
                                  self.dialog)
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
        self.labelmode.set_text(text)
        self.dialog.set_modal(mode == const.EDIT)
        self.dialog.show()
        self.entrydate.grab_focus()

    def _set_entry_values(self, values):
        self.entrydate.set_text(values[0])
        self.comboracepoint.child.set_text(values[1])
        self.spinplaced.set_value(values[2])
        self.spinoutof.set_value(values[3])
        self.combosector.child.set_text(values[4])
        self.combotype.child.set_text(values[5])
        self.combocategory.child.set_text(values[6])
        self.comboweather.child.set_text(values[7])
        self.combowind.child.set_text(values[8])
        self.entrycomment.set_text(values[9])

    def _insert_combo_data(self, combo, data, table):
        if not data: return
        # Racepoint table has more columns
        row = (data,) if not table == self.database.RACEPOINTS else (data, "", "", "", "")
        self.database.insert_into_table(table, row)
        model = combo.get_model()
        for treerow in model:
            if data in treerow:
                return
        model.append([data])
        model.set_sort_column_id(0, gtk.SORT_ASCENDING)

