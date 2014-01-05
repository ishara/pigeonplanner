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

from pigeonplanner import messages
from pigeonplanner import database
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import resultwindow
from pigeonplanner.ui import resultparser
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.messagedialog import ErrorDialog, QuestionDialog
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import config
from pigeonplanner.core import pigeonparser


def get_view_for_current_config():
    if config.get("interface.results-mode") == ClassicView.ID:
        return ClassicView
    else:
        return SplittedView


class BaseView(object):
    ID = None

    def __init__(self, root):
        self._root = root
        self.pigeon = None

        self.build_ui()

    def _build_parent_frame(self, label, child):
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(child)
        label = gtk.Label("<b>%s</b>" % label)
        label.set_use_markup(True)
        frame = gtk.Frame()
        frame.set_label_widget(label)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.add(sw)

        return frame

    @property
    def maintree(self):
        raise NotImplementedError

    def build_ui(self):
        raise NotImplementedError

    def set_columns(self):
        raise NotImplementedError

    def set_pigeon(self, pigeon):
        raise NotImplementedError

    def get_selected(self):
        raise NotImplementedError

    def remove_selected(self):
        raise NotImplementedError

    def add_result(self, data):
        raise NotImplementedError

    def update_result(self, data):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError


class ClassicView(BaseView):
    ID = 0

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
     COL_COMMENT,
     COL_PLACEDINT,
     COL_COEFFLOAT) = range(14)

    def __init__(self, root):
        BaseView.__init__(self, root)

    @property
    def maintree(self):
        return self.treeview

    def build_ui(self):
        self.liststore = gtk.ListStore(str, str, str, str, int, str, str,
                                       str, str, str, str, str, int, float)
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)
        self.selection = self.treeview.get_selection()
        colnames = [(_("Date"), None), (_("Racepoint"), None),
                    (_("Placed"), 12), (_("Out of"), None),
                    (_("Coefficient"), 13), (_("Sector"), None),
                    (_("Type"), None), (_("Category"), None),
                    (_("Wind"), None), (_("Weather"), None), (_("Comment"), None)]
        for index, (colname, sortid) in enumerate(colnames):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(colname, textrenderer, text=index+1)
            tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(sortid or index+1)
            self.treeview.append_column(tvcolumn)
        self._frame = self._build_parent_frame(_("Results of pigeon"), self.treeview)
        self._frame.show_all()
        self._root.pack_start(self._frame, True, True, 0)

    def set_columns(self):
        columnsdic = {4: config.get("columns.result-coef"),
                      5: config.get("columns.result-sector"),
                      6: config.get("columns.result-type"),
                      7: config.get("columns.result-category"),
                      8: config.get("columns.result-wind"),
                      9: config.get("columns.result-weather"),
                      10: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        self.liststore.clear()
        for result in database.get_results_for_data({"pindex": pigeon.pindex}):
            placestr, coef, coefstr = common.format_place_coef(result["place"], result["out"])

            self.liststore.append(
                [result["Resultkey"], result["date"], result["point"],
                 placestr, result["out"], coefstr, result["sector"], result["type"],
                 result["category"], result["wind"], result["weather"], result["comment"],
                 result["place"], coef
                ]
            )

    def get_selected(self):
        # Columns could contain None prior to 0.7.0, convert to empty string
        model, rowiter = self.selection.get_selected()
        return [model.get_value(rowiter, self.COL_DATE) or "",
                model.get_value(rowiter, self.COL_RACEPOINT) or "",
                model.get_value(rowiter, self.COL_PLACED) or "",
                model.get_value(rowiter, self.COL_OUT) or "",
                model.get_value(rowiter, self.COL_SECTOR) or "",
                model.get_value(rowiter, self.COL_TYPE) or "",
                model.get_value(rowiter, self.COL_CATEGORY) or "",
                model.get_value(rowiter, self.COL_WEATHER) or "",
                model.get_value(rowiter, self.COL_WIND) or "",
                model.get_value(rowiter, self.COL_COMMENT) or "",
            ]

    def remove_selected(self):
        model, rowiter = self.selection.get_selected()
        path = self.liststore.get_path(rowiter)

        database.remove_result(model[rowiter][self.COL_ID])
        self.liststore.remove(rowiter)
        self.selection.select_path(path)

    def add_result(self, data, key):
        placestr, coef, coefstr = common.format_place_coef(data["place"], data["out"])
        rowiter = self.liststore.insert(0,
                [key, data["date"], data["point"],
                 placestr, data["out"], coefstr, data["sector"], data["type"],
                 data["category"], data["wind"], data["weather"], data["comment"],
                 data["place"], coef
                ]
            )
        self.selection.select_iter(rowiter)
        path = self.liststore.get_path(rowiter)
        self.treeview.scroll_to_cell(path)

    def update_result(self, data):
        placestr, coef, coefstr = common.format_place_coef(data["place"], data["out"])
        model, node = self.selection.get_selected()
        key = self.liststore.get_value(node, 0)
        self.liststore.set(node, self.COL_DATE, data["date"],
                                 self.COL_RACEPOINT, data["point"],
                                 self.COL_PLACED, placestr,
                                 self.COL_OUT, data["out"],
                                 self.COL_COEF, coefstr,
                                 self.COL_SECTOR, data["sector"],
                                 self.COL_TYPE, data["type"],
                                 self.COL_CATEGORY, data["category"],
                                 self.COL_WIND, data["wind"],
                                 self.COL_WEATHER, data["weather"],
                                 self.COL_COMMENT, data["comment"],
                                 self.COL_PLACEDINT, data["place"],
                                 self.COL_COEFFLOAT, coef)
        return key

    def clear(self):
        self.liststore.clear()

    def refresh(self):
        self.selection.emit("changed")

    def destroy(self):
        self._frame.destroy()


class SplittedView(BaseView):
    ID = 1

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
     COL_COMMENT,
     COL_PLACEDINT,
     COL_COEFFLOAT) = range(9)

    def __init__(self, root):
        BaseView.__init__(self, root)

    @property
    def maintree(self):
        return self.treeview

    def build_ui(self):
        self.race_ls = gtk.ListStore(str, str, str, str, str)
        self.race_tv = gtk.TreeView()
        self.race_tv.set_model(self.race_ls)
        self.race_tv.set_rules_hint(True)
        self.race_tv.set_enable_search(False)
        self.race_sel = self.race_tv.get_selection()
        self.race_sel.connect("changed", self.on_race_sel_changed)
        colnames = [_("Date"), _("Racepoint"), _("Type"), _("Wind"), _("Weather")]
        for index, colname in enumerate(colnames):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(colname, textrenderer, text=index)
            tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(index)
            self.race_tv.append_column(tvcolumn)
        self._frame1 = self._build_parent_frame(_("Races"), self.race_tv)
        self._frame1.show_all()
        self._root.pack_start(self._frame1, True, True, 0)

        self.liststore = gtk.ListStore(str, str, int, str, str, str, str, int, float)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)
        self.selection = self.treeview.get_selection()
        colnames = [(_("Placed"), 7), (_("Out of"), None),
                    (_("Coefficient"), 8), (_("Sector"), None),
                    (_("Category"), None), (_("Comment"), None)]
        for index, (colname, sortid) in enumerate(colnames):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(colname, textrenderer, text=index+1)
            tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(sortid or index+1)
            self.treeview.append_column(tvcolumn)
        self._frame2 = self._build_parent_frame(_("Results of pigeon"), self.treeview)
        self._frame2.show_all()
        self._root.pack_start(self._frame2, True, True, 0)

    def set_columns(self):
        columnsdic = {2: config.get("columns.result-coef"),
                      3: config.get("columns.result-sector"),
                      4: config.get("columns.result-category"),
                      5: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

        columnsdic = {2: config.get("columns.result-type"),
                      3: config.get("columns.result-wind"),
                      4: config.get("columns.result-weather")}
        for key, value in columnsdic.items():
            self.race_tv.get_column(key).set_visible(value)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        self.liststore.clear()
        self.race_ls.clear()
        for race in database.get_races_for_pigeon(pigeon.pindex):
            self.race_ls.append([race["date"], race["point"], race["type"],
                                         race["wind"], race["weather"]])

    def get_selected(self):
        # Columns could contain None prior to 0.7.0, convert to empty string
        model, rowiter = self.selection.get_selected()
        model_race, rowiter_race = self.race_sel.get_selected()
        return [model_race.get_value(rowiter_race, self.COL_DATE) or "",
                model_race.get_value(rowiter_race, self.COL_RACEPOINT) or "",
                model.get_value(rowiter, self.COL_PLACED) or "",
                model.get_value(rowiter, self.COL_OUT) or "",
                model.get_value(rowiter, self.COL_SECTOR) or "",
                model_race.get_value(rowiter_race, self.COL_TYPE) or "",
                model.get_value(rowiter, self.COL_CATEGORY) or "",
                model_race.get_value(rowiter_race, self.COL_WEATHER) or "",
                model_race.get_value(rowiter_race, self.COL_WIND) or "",
                model.get_value(rowiter, self.COL_COMMENT) or "",
            ]

    def remove_selected(self):
        model, rowiter = self.selection.get_selected()
        path = self.liststore.get_path(rowiter)

        database.remove_result(model[rowiter][self.COL_ID])
        self.liststore.remove(rowiter)
        self.selection.select_path(path)

        if len(self.liststore) == 0:
            model, rowiter = self.race_sel.get_selected()
            self.race_ls.remove(rowiter)

    def add_result(self, data, key):
        seldata = {"pindex": self.pigeon.pindex, "date": data["date"], "point": data["point"]}
        if not database.get_results_for_data(seldata):
            rowiter = self.race_ls.insert(0, [data["date"], data["point"],
                                        data["type"], data["wind"], data["weather"]])
            self.race_ls.set_sort_column_id(0, gtk.SORT_ASCENDING)
            self.race_sel.select_iter(rowiter)
            path = self.race_ls.get_path(rowiter)
            self.race_tv.scroll_to_cell(path)
        else:
            model, node = self.race_sel.get_selected()
            self.race_ls.set(node, self.COL_DATE, data["date"],
                                   self.COL_RACEPOINT, data["point"],
                                   self.COL_TYPE, data["type"],
                                   self.COL_WIND, data["wind"],
                                   self.COL_WEATHER, data["weather"])

    def update_result(self, data):
        placestr, coef, coefstr = common.format_place_coef(data["place"], data["out"])
        model, node = self.selection.get_selected()
        key = self.liststore.get_value(node, 0)
        self.liststore.set(node, self.COL_PLACED, placestr,
                                 self.COL_OUT, data["out"],
                                 self.COL_COEF, coefstr,
                                 self.COL_SECTOR, data["sector"],
                                 self.COL_CATEGORY, data["category"],
                                 self.COL_COMMENT, data["comment"],
                                 self.COL_PLACEDINT, data["place"],
                                 self.COL_COEFFLOAT, coef)
        model, node = self.race_sel.get_selected()
        self.race_ls.set(node, self.COL_DATE, data["date"],
                               self.COL_RACEPOINT, data["point"],
                               self.COL_TYPE, data["type"],
                               self.COL_WIND, data["wind"],
                               self.COL_WEATHER, data["weather"])
        return key

    def clear(self):
        self.liststore.clear()
        self.race_ls.clear()

    def refresh(self):
        self.race_sel.emit("changed")

    def destroy(self):
        self._frame1.destroy()
        self._frame2.destroy()

    def on_race_sel_changed(self, selection):
        model, rowiter = selection.get_selected()
        if rowiter is None:
            return

        date = model.get_value(rowiter, 0)
        racepoint = model.get_value(rowiter, 1)
        self.liststore.clear()
        data = {"pindex": self.pigeon.pindex, "date": date, "point": racepoint}
        for result in database.get_results_for_data(data):
            placestr, coef, coefstr = common.format_place_coef(result["place"], result["out"])
            self.liststore.append([result["Resultkey"], placestr, result["out"], coefstr,
                                   result["sector"], result["category"],
                                   result["comment"], result["place"], coef])


class ResultsTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "ResultsView.ui")
        basetab.BaseTab.__init__(self, _("Results"), "icon_result.png")

        self.parent = parent
        view = get_view_for_current_config()
        self.widgets.resultview = view(self.widgets._root)
        self.widgets.resultview.set_columns()
        self.widgets.resultview.maintree.connect("button-press-event", self.on_treeview_press)
        mainsel = self.widgets.resultview.maintree.get_selection()
        mainsel.connect("changed", self.on_selection_changed)

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
        self._mode = enums.Action.add
        values = [common.get_date(), "", 1, 1, "", "", "", "", "", ""]
        self._set_dialog(self._mode, values)

    def on_buttonedit_clicked(self, widget):
        result = self.widgets.resultview.get_selected()
        self._mode = enums.Action.edit
        self._set_dialog(self._mode, result)

    def on_buttonremove_clicked(self, widget):
        if not QuestionDialog(messages.MSG_REMOVE_RESULT, self.parent).run():
            return

        self.widgets.resultview.remove_selected()

    def on_buttonclose_clicked(self, widget):
        self.widgets.dialog.hide()

    def on_buttonsave_clicked(self, widget):
        data = self._get_data()
        if data is None: return

        if self._mode == enums.Action.add:
            data["pindex"] = self.pigeon.pindex
            if database.result_exists(data):
                ErrorDialog(messages.MSG_RESULT_EXISTS, self.parent)
                return

            key = database.add_result(data)
            self.widgets.resultview.add_result(data, key)
        elif self._mode == enums.Action.edit:
            key = self.widgets.resultview.update_result(data)
            database.update_result_for_key(key, data)
            self.widgets.dialog.hide()

        database.update_result_as_race(data["date"], data["point"],
                                       data["sector"], data["wind"], data["weather"])
        self.widgets.resultview.refresh()

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
        self.pigeon = pigeon
        self.widgets.labelpigeon.set_text(pigeon.get_band_string())

        self.widgets.resultview.set_pigeon(pigeon)

    def clear_pigeon(self):
        self.widgets.resultview.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    def add_new_result(self):
        self.widgets.buttonadd.clicked()

    def set_columns(self):
        self.widgets.resultview.set_columns()

    def reset_result_mode(self):
        if self.widgets.resultview.ID != config.get("interface.results-mode"):
            self.widgets.resultview.destroy()
            view = get_view_for_current_config()
            self.widgets.resultview = view(self.widgets._root)
            self.widgets.resultview.set_pigeon(self.pigeon)

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
        text = _("Edit result for:") if mode == enums.Action.edit else _("Add result for:")
        self.widgets.labelmode.set_text(text)
        #TODO: Setting modal doesn't work
        self.widgets.dialog.set_modal(mode == enums.Action.edit)
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

