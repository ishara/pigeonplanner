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


from gi.repository import Gtk

from pigeonplanner import messages
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui import resultwindow
from pigeonplanner.ui import resultparser
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.widgets import dateentry
from pigeonplanner.ui.messagedialog import ErrorDialog, QuestionDialog, InfoDialog
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import config
from pigeonplanner.database.models import (Result, Racepoint, Category,
                                           Sector, Type, Weather, Wind)


def get_view_for_current_config():
    if config.get("interface.results-mode") == ClassicView.ID:
        return ClassicView
    else:
        return SplittedView


class BaseView:
    ID = None

    def __init__(self, root):
        self._root = root
        self.pigeon = None

        self.liststore = None
        self.treeview = None
        self.selection = None

        self.colname2string = {
            "date": _("Date"),
            "racepoint": _("Racepoint"),
            "type": _("Type"),
            "wind": _("Wind"),
            "windspeed": _("Windspeed"),
            "weather": _("Weather"),
            "temperature": _("Temperature"),
            "band": _("Band no."),
            "year": _("Year"),
            "placestr": _("Placed"),
            "place": _("Placed"),
            "out": _("Out of"),
            "coefstr": _("Coefficient"),
            "coef": _("Coefficient"),
            "speedstr": _("Speed"),
            "speed": _("Speed"),
            "sector": _("Sector"),
            "category": _("Category"),
            "comment": _("Comment"),
        }

    # noinspection PyMethodMayBeStatic
    def _build_parent_frame(self, label, child):
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(child)
        label = Gtk.Label(label="<b>%s</b>" % label)
        label.set_use_markup(True)
        frame = Gtk.Frame()
        frame.set_label_widget(label)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
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

    (LS_COL_OBJECT,
     LS_COL_DATE,
     LS_COL_RACEPOINT,
     LS_COL_PLACED,
     LS_COL_OUT,
     LS_COL_COEF,
     LS_COL_SPEED,
     LS_COL_SECTOR,
     LS_COL_TYPE,
     LS_COL_CATEGORY,
     LS_COL_WIND,
     LS_COL_WINDSPEED,
     LS_COL_WEATHER,
     LS_COL_TEMPERATURE,
     LS_COL_COMMENT,
     LS_COL_PLACEDINT,
     LS_COL_COEFFLOAT,
     LS_COL_SPEEDFLOAT) = range(18)

    (COL_DATE,
     COL_RACEPOINT,
     COL_PLACED,
     COL_OUT,
     COL_COEF,
     COL_SPEED,
     COL_SECTOR,
     COL_TYPE,
     COL_CATEGORY,
     COL_WIND,
     COL_WINDSPEED,
     COL_WEATHER,
     COL_TEMPERATURE,
     COL_COMMENT) = range(14)

    def __init__(self, root):
        BaseView.__init__(self, root)

        self._frame = None

        self.build_ui()

    # noinspection PyMethodMayBeStatic
    def _row_for_result(self, result):
        placestr, coef, coefstr = common.format_place_coef(result.place, result.out)
        speed = common.format_speed(result.speed)
        return [
            result, str(result.date), result.racepoint,
            placestr, result.out, coefstr, speed, result.sector, result.type,
            result.category, result.wind, result.windspeed, result.weather,
            result.temperature, result.comment, result.place, coef, result.speed
        ]

    @property
    def maintree(self):
        return self.treeview

    def build_ui(self):
        self.liststore = Gtk.ListStore(object, str, str, str, int, str, str, str, str,
                                       str, str, str, str, str, str, int, float, float)
        self.liststore.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self.treeview = Gtk.TreeView()
        self.treeview.set_model(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)
        self.selection = self.treeview.get_selection()
        colnames = [("date", None), ("racepoint", None),
                    ("place", self.LS_COL_PLACEDINT), ("out", None),
                    ("coef", self.LS_COL_COEFFLOAT),
                    ("speed", self.LS_COL_SPEEDFLOAT), ("sector", None),
                    ("type", None), ("category", None),
                    ("wind", None), ("windspeed", None),
                    ("weather", None), ("temperature", None), ("comment", None)]
        for index, (colname, sortid) in enumerate(colnames):
            textrenderer = Gtk.CellRendererText()
            tvcolumn = Gtk.TreeViewColumn(self.colname2string[colname],
                                          textrenderer, text=index+1)
            tvcolumn.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(sortid or index+1)
            self.treeview.append_column(tvcolumn)
        self._frame = self._build_parent_frame(_("Results of pigeon"), self.treeview)
        self._frame.show_all()
        self._root.pack_start(self._frame, True, True, 0)

    def set_columns(self):
        columnsdic = {self.COL_COEF: config.get("columns.result-coef"),
                      self.COL_SPEED: config.get("columns.result-speed"),
                      self.COL_SECTOR: config.get("columns.result-sector"),
                      self.COL_TYPE: config.get("columns.result-type"),
                      self.COL_CATEGORY: config.get("columns.result-category"),
                      self.COL_WIND: config.get("columns.result-wind"),
                      self.COL_WINDSPEED: config.get("columns.result-windspeed"),
                      self.COL_WEATHER: config.get("columns.result-weather"),
                      self.COL_TEMPERATURE: config.get("columns.result-temperature"),
                      self.COL_COMMENT: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        self.liststore.clear()
        for result in pigeon.results.order_by(Result.place.asc()):
            self.liststore.append(self._row_for_result(result))

    def get_selected(self):
        model, rowiter = self.selection.get_selected()
        return {
            "object": model.get_value(rowiter, self.LS_COL_OBJECT),
            "date": model.get_value(rowiter, self.LS_COL_DATE),
            "racepoint": model.get_value(rowiter, self.LS_COL_RACEPOINT),
            "place": model.get_value(rowiter, self.LS_COL_PLACEDINT),
            "out": model.get_value(rowiter, self.LS_COL_OUT),
            "speed": model.get_value(rowiter, self.LS_COL_SPEEDFLOAT),
            "sector": model.get_value(rowiter, self.LS_COL_SECTOR),
            "type": model.get_value(rowiter, self.LS_COL_TYPE),
            "category": model.get_value(rowiter, self.LS_COL_CATEGORY),
            "weather": model.get_value(rowiter, self.LS_COL_WEATHER),
            "temperature": model.get_value(rowiter, self.LS_COL_TEMPERATURE),
            "wind": model.get_value(rowiter, self.LS_COL_WIND),
            "windspeed": model.get_value(rowiter, self.LS_COL_WINDSPEED),
            "comment": model.get_value(rowiter, self.LS_COL_COMMENT),
        }

    def remove_selected(self):
        model, rowiter = self.selection.get_selected()
        path = self.liststore.get_path(rowiter)

        result = model[rowiter][self.LS_COL_OBJECT]
        result.delete_instance()
        self.liststore.remove(rowiter)
        self.selection.select_path(path)

    def add_result(self, result):
        rowiter = self.liststore.insert(0, self._row_for_result(result))
        self.selection.select_iter(rowiter)
        path = self.liststore.get_path(rowiter)
        self.treeview.scroll_to_cell(path)

    def update_result(self, data):
        placestr, coef, coefstr = common.format_place_coef(data["place"], data["out"])
        speed = common.format_speed(data["speed"])
        model, node = self.selection.get_selected()
        result = self.liststore.get_value(node, self.LS_COL_OBJECT)
        self.liststore.set(
            node,
            self.LS_COL_DATE, data["date"],
            self.LS_COL_RACEPOINT, data["racepoint"],
            self.LS_COL_PLACED, placestr,
            self.LS_COL_OUT, data["out"],
            self.LS_COL_COEF, coefstr,
            self.LS_COL_SPEED, speed,
            self.LS_COL_SECTOR, data["sector"],
            self.LS_COL_TYPE, data["type"],
            self.LS_COL_CATEGORY, data["category"],
            self.LS_COL_WIND, data["wind"],
            self.LS_COL_WINDSPEED, data["windspeed"],
            self.LS_COL_WEATHER, data["weather"],
            self.LS_COL_TEMPERATURE, data["temperature"],
            self.LS_COL_COMMENT, data["comment"],
            self.LS_COL_PLACEDINT, data["place"],
            self.LS_COL_COEFFLOAT, coef,
            self.LS_COL_SPEEDFLOAT, data["speed"]
        )
        return result

    def clear(self):
        self.liststore.clear()

    def refresh(self):
        self.selection.emit("changed")

    def destroy(self):
        self._frame.destroy()


class SplittedView(BaseView):
    ID = 1

    (LS_COL_DATE,
     LS_COL_RACEPOINT,
     LS_COL_TYPE,
     LS_COL_WIND,
     LS_COL_WINDSPEED,
     LS_COL_WEATHER,
     LS_COL_TEMPERATURE) = range(7)

    (LS_COL_OBJECT,
     LS_COL_PLACED,
     LS_COL_OUT,
     LS_COL_COEF,
     LS_COL_SPEED,
     LS_COL_SECTOR,
     LS_COL_CATEGORY,
     LS_COL_COMMENT,
     LS_COL_PLACEDINT,
     LS_COL_COEFFLOAT,
     LS_COL_SPEEDFLOAT) = range(11)

    (COL_DATE,
     COL_RACEPOINT,
     COL_TYPE,
     COL_WIND,
     COL_WINDSPEED,
     COL_WEATHER,
     COL_TEMPERATURE) = range(7)

    (COL_PLACED,
     COL_OUT,
     COL_COEF,
     COL_SPEED,
     COL_SECTOR,
     COL_CATEGORY,
     COL_COMMENT) = range(7)

    def __init__(self, root):
        BaseView.__init__(self, root)

        self.race_ls = None
        self.race_tv = None
        self.race_sel = None
        self._frame1 = None
        self._frame2 = None

        self.build_ui()

    @property
    def maintree(self):
        return self.treeview

    def build_ui(self):
        self.race_ls = Gtk.ListStore(str, str, str, str, str, str, str)
        self.race_tv = Gtk.TreeView()
        self.race_tv.set_model(self.race_ls)
        self.race_tv.set_rules_hint(True)
        self.race_tv.set_enable_search(False)
        self.race_sel = self.race_tv.get_selection()
        self.race_sel.connect("changed", self.on_race_sel_changed)
        colnames = ["date", "racepoint", "type", "wind", 
                    "windspeed", "weather", "temperature"]
        for index, colname in enumerate(colnames):
            textrenderer = Gtk.CellRendererText()
            tvcolumn = Gtk.TreeViewColumn(self.colname2string[colname],
                                          textrenderer, text=index)
            tvcolumn.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(index)
            self.race_tv.append_column(tvcolumn)
        self._frame1 = self._build_parent_frame(_("Races"), self.race_tv)
        self._frame1.show_all()
        self._root.pack_start(self._frame1, True, True, 0)

        self.liststore = Gtk.ListStore(object, str, int, str, str, str, str, str, int, float, float)
        self.treeview = Gtk.TreeView()
        self.treeview.set_model(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)
        self.selection = self.treeview.get_selection()
        colnames = [("place", self.LS_COL_PLACEDINT), ("out", None),
                    ("coef", self.LS_COL_COEFFLOAT),
                    ("speed", self.LS_COL_SPEEDFLOAT), ("sector", None),
                    ("category", None), ("comment", None)]
        for index, (colname, sortid) in enumerate(colnames):
            textrenderer = Gtk.CellRendererText()
            tvcolumn = Gtk.TreeViewColumn(self.colname2string[colname],
                                          textrenderer, text=index+1)
            tvcolumn.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
            tvcolumn.set_clickable(True)
            tvcolumn.set_sort_column_id(sortid or index+1)
            self.treeview.append_column(tvcolumn)
        self._frame2 = self._build_parent_frame(_("Results of pigeon"), self.treeview)
        self._frame2.show_all()
        self._root.pack_start(self._frame2, True, True, 0)

    def set_columns(self):
        columnsdic = {self.COL_COEF: config.get("columns.result-coef"),
                      self.COL_SPEED: config.get("columns.result-speed"),
                      self.COL_SECTOR: config.get("columns.result-sector"),
                      self.COL_CATEGORY: config.get("columns.result-category"),
                      self.COL_COMMENT: config.get("columns.result-comment")}
        for key, value in columnsdic.items():
            self.treeview.get_column(key).set_visible(value)

        columnsdic = {self.COL_TYPE: config.get("columns.result-type"),
                      self.COL_WIND: config.get("columns.result-wind"),
                      self.COL_WINDSPEED: config.get("columns.result-windspeed"),
                      self.COL_WEATHER: config.get("columns.result-weather"),
                      self.COL_TEMPERATURE: config.get("columns.result-temperature")}
        for key, value in columnsdic.items():
            self.race_tv.get_column(key).set_visible(value)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        self.liststore.clear()
        self.race_ls.clear()
        for race in pigeon.results.group_by(Result.date, Result.racepoint).order_by(Result.date.asc()):
            self.race_ls.append([str(race.date), race.racepoint, race.type, race.wind,
                                 race.windspeed, race.weather, race.temperature])

    def get_selected(self):
        model, rowiter = self.selection.get_selected()
        model_race, rowiter_race = self.race_sel.get_selected()
        return {
            "object": model.get_value(rowiter, self.LS_COL_OBJECT),
            "date": model_race.get_value(rowiter_race, self.LS_COL_DATE),
            "racepoint": model_race.get_value(rowiter_race, self.LS_COL_RACEPOINT),
            "place": model.get_value(rowiter, self.LS_COL_PLACEDINT),
            "out": model.get_value(rowiter, self.LS_COL_OUT),
            "speed": model.get_value(rowiter, self.LS_COL_SPEEDFLOAT),
            "sector": model.get_value(rowiter, self.LS_COL_SECTOR),
            "type": model_race.get_value(rowiter_race, self.LS_COL_TYPE),
            "category": model.get_value(rowiter, self.LS_COL_CATEGORY),
            "weather": model_race.get_value(rowiter_race, self.LS_COL_WEATHER),
            "temperature": model_race.get_value(rowiter_race, self.LS_COL_TEMPERATURE),
            "wind": model_race.get_value(rowiter_race, self.LS_COL_WIND),
            "windspeed": model_race.get_value(rowiter_race, self.LS_COL_WINDSPEED),
            "comment": model.get_value(rowiter, self.LS_COL_COMMENT),
        }

    def remove_selected(self):
        model, rowiter = self.selection.get_selected()
        path = self.liststore.get_path(rowiter)

        result = model[rowiter][self.LS_COL_OBJECT]
        result.delete_instance()
        self.liststore.remove(rowiter)
        self.selection.select_path(path)

        if len(self.liststore) == 0:
            model, rowiter = self.race_sel.get_selected()
            self.race_ls.remove(rowiter)

    def add_result(self, result):
        n_results = Result.select().where(
            (Result.pigeon == self.pigeon) &
            (Result.date == result.date) &
            (Result.racepoint == result.racepoint)
        ).count()
        if n_results > 1:
            for row in self.race_ls:
                if row[self.LS_COL_DATE] == result.date and \
                   row[self.LS_COL_RACEPOINT] == result.racepoint:
                    self.race_sel.select_iter(row.iter)
                    self.race_tv.scroll_to_cell(row.path)
                    break
            self.race_ls.set(
                row.iter,
                self.LS_COL_TYPE, result.type,
                self.LS_COL_WIND, result.wind,
                self.LS_COL_WINDSPEED, result.windspeed,
                self.LS_COL_WEATHER, result.weather,
                self.LS_COL_TEMPERATURE, result.temperature)
        else:
            rowiter = self.race_ls.insert(0, [result.date, result.racepoint, result.type,
                                              result.wind, result.windspeed,
                                              result.weather, result.temperature])
            self.race_ls.set_sort_column_id(0, Gtk.SortType.ASCENDING)
            self.race_sel.select_iter(rowiter)
            path = self.race_ls.get_path(rowiter)
            self.race_tv.scroll_to_cell(path)

    def update_result(self, data):
        model, node = self.selection.get_selected()
        result = self.liststore.get_value(node, self.LS_COL_OBJECT)

        model, racenode = self.race_sel.get_selected()
        date = self.race_ls.get_value(racenode, self.LS_COL_DATE)
        point = self.race_ls.get_value(racenode, self.LS_COL_RACEPOINT)
        if date != data["date"] or point != data["racepoint"]:
            if len(self.liststore) == 1:
                # This is the only result for this race
                self.race_ls.remove(racenode)
            # The date or point is changed, this means that the result should
            # be handled as a different race. Add a new one in this case.
            n_results = Result.select().where(
                (Result.pigeon == self.pigeon) &
                (Result.date == result.date) &
                (Result.racepoint == result.racepoint)
            ).count()
            if n_results > 0:
                # This race already exists for this pigeon
                for row in self.race_ls:
                    if row[self.LS_COL_DATE] == data["date"] and \
                       row[self.LS_COL_RACEPOINT] == data["racepoint"]:
                        self.race_sel.select_iter(row.iter)
                        self.race_tv.scroll_to_cell(row.path)
                        break
            else:
                rowiter = self.race_ls.append([data["date"], data["racepoint"], data["type"],
                                               data["wind"], data["windspeed"],
                                               data["weather"], data["temperature"]])
                self.race_sel.select_iter(rowiter)
                path = self.race_ls.get_path(rowiter)
                self.race_tv.scroll_to_cell(path)
        else:
            self.race_ls.set(
                racenode,
                self.LS_COL_TYPE, data["type"],
                self.LS_COL_WIND, data["wind"],
                self.LS_COL_WINDSPEED, data["windspeed"],
                self.LS_COL_WEATHER, data["weather"],
                self.LS_COL_TEMPERATURE, data["temperature"])
        return result

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
        for result in self.pigeon.results.where((Result.date == date) & (Result.racepoint == racepoint)):
            placestr, coef, coefstr = common.format_place_coef(result.place, result.out)
            speed = common.format_speed(result.speed)
            self.liststore.append([result, placestr, result.out, coefstr,
                                   speed, result.sector, result.category,
                                   result.comment, result.place, coef, result.speed])


class ResultsTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self):
        builder.GtkBuilder.__init__(self, "ResultsView.ui")
        basetab.BaseTab.__init__(self, "ResultsTab", _("Results"), "icon_result.png")

        self.pigeon = None
        self._mode = None

        view = get_view_for_current_config()
        self.widgets.resultview = view(self.widgets._root)
        self.widgets.resultview.set_columns()
        self.widgets.resultview.maintree.connect("button-press-event", self.on_treeview_press)
        mainsel = self.widgets.resultview.maintree.get_selection()
        mainsel.connect("changed", self.on_selection_changed)

        self.widgets.dialog.set_transient_for(self._parent)

    # Callbacks
    def on_dialog_delete(self, _widget, _event):
        self._close_dialog()
        return True

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return
        if event.button == 3:
            entries = [
                (self.on_buttonedit_clicked, None, _("Edit")),
                (self.on_buttonremove_clicked, None, _("Remove")),
                (self.on_addtopedigree_clicked, None, _("Add to pedigree details"))]
            utils.popup_menu(event, entries)

    def on_buttonall_clicked(self, _widget):
        resultwindow.ResultWindow(self._parent)

    def on_buttonimport_clicked(self, _widget):
        resultparser.ResultParser(self._parent)

    def on_buttonadd_clicked(self, _widget):
        self._mode = enums.Action.add
        values = Result.get_fields_with_defaults()
        values["date"] = common.get_date()
        values["racepoint"] = ""
        values["place"] = 1
        values["out"] = 1
        self._set_dialog(self._mode, values)

    def on_buttonedit_clicked(self, _widget):
        result = self.widgets.resultview.get_selected()
        self._mode = enums.Action.edit
        self._set_dialog(self._mode, result)

    def on_buttonremove_clicked(self, _widget):
        if not QuestionDialog(messages.MSG_REMOVE_RESULT, self._parent).run():
            return

        self.widgets.resultview.remove_selected()

    def on_buttonclose_clicked(self, _widget):
        self._close_dialog()

    def on_buttonsave_clicked(self, _widget):
        data = self._get_data()
        if data is None:
            return

        if self._mode == enums.Action.add:
            try:
                result = Result.create(pigeon=self.pigeon, **data)
            except errors.IntegrityError:
                ErrorDialog(messages.MSG_RESULT_EXISTS, self._parent)
                return
            self.widgets.resultview.add_result(result)
        elif self._mode == enums.Action.edit:
            old_result = self.widgets.resultview.update_result(data)
            try:
                old_result.update_and_return(**data)
            except errors.IntegrityError:
                ErrorDialog(messages.MSG_RESULT_EXISTS, self._parent)
                return
            self.widgets.dialog.hide()

        # Update the race specific data for each race
        update_query = Result.update(type=data["type"], wind=data["wind"],
                                     windspeed=data["windspeed"], weather=data["weather"],
                                     temperature=data["temperature"])\
            .where((Result.date == data["date"]) & (Result.racepoint == data["racepoint"]))
        update_query.execute()
        self.widgets.resultview.refresh()

        self.widgets.comboracepoint.add_item(data["racepoint"])
        self.widgets.combosector.add_item(data["sector"])
        self.widgets.combotype.add_item(data["type"])
        self.widgets.combocategory.add_item(data["category"])
        self.widgets.comboweather.add_item(data["weather"])
        self.widgets.combowind.add_item(data["wind"])

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        utils.set_multiple_sensitive(widgets, rowiter is not None)

    def on_checkplaced_toggled(self, widget):
        sensitive = widget.get_active()
        self.widgets.spinplaced.set_sensitive(sensitive)

    def on_spinplaced_changed(self, widget):
        self.widgets.spinoutof.set_range(widget.get_value_as_int(),
                                         widget.get_range()[1])

    def on_entrydate_changed(self, _widget):
        self._autofill_race()

    def on_comboracepoint_changed(self, _widget):
        self._autofill_race()

    def on_addtopedigree_clicked(self, _widget):
        result = self.widgets.resultview.get_selected()
        text = "%se %s %s %s." % (result["place"], result["racepoint"],
                                  result["out"], _("Pigeons")[0].lower())
        for index, field in enumerate(self.pigeon.extra):
            if field == "":
                setattr(self.pigeon, "extra%s" % (index+1), text)
                self.pigeon.save()
                component.get("Treeview").update_pigeon(self.pigeon)
                component.get("DetailsView").set_details(self.pigeon)
                break
        else:
            InfoDialog((_("No empty space found in pedigree details."), "", ""),
                       self._parent, None)

    # Public methods
    def set_pigeon(self, pigeon):
        self.pigeon = pigeon
        self.widgets.labelpigeon.set_text(pigeon.band)

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
            if self.pigeon is not None:
                # The result mode is changed on an empty database and no pigeon
                # has been set before.
                self.widgets.resultview.set_pigeon(self.pigeon)

    # Internal methods
    def _close_dialog(self):
        if not self.widgets.entrydate.is_valid_date():
            self.widgets.entrydate.set_today()
        self.widgets.dialog.hide()

    def _get_data(self):
        try:
            date = self.widgets.entrydate.get_text()
        except dateentry.InvalidDateInput as exc:
            ErrorDialog(exc.format_error(), self.widgets.dialog)
            return
        point = self.widgets.comboracepoint.get_child().get_text()
        if self.widgets.checkplaced.get_active():
            place = self.widgets.spinplaced.get_value_as_int()
        else:
            place = 0
        out = self.widgets.spinoutof.get_value_as_int()
        speed = self.widgets.spinspeed.get_value()
        sector = self.widgets.combosector.get_child().get_text()
        ftype = self.widgets.combotype.get_child().get_text()
        category = self.widgets.combocategory.get_child().get_text()
        weather = self.widgets.comboweather.get_child().get_text()
        temperature = self.widgets.entrytemperature.get_text()
        wind = self.widgets.combowind.get_child().get_text()
        windspeed = self.widgets.entrywindspeed.get_text()
        comment = self.widgets.entrycomment.get_text()

        if not date or not point or not out:
            ErrorDialog(messages.MSG_EMPTY_DATA, self.widgets.dialog)
            return
        return {"date": date, "racepoint": point, "place": place, "out": out,
                "sector": sector, "type": ftype, "category": category,
                "wind": wind, "weather": weather, "comment": comment,
                "speed": speed, "windspeed": windspeed, "temperature": temperature}

    def _set_dialog(self, mode, values):
        """
        Set the dialog in the correct state

        @param mode: add or edit mode
        @param values: the values for the entry widgets
        """

        # Update these everytime the dialog is shown. They are updated automatically
        # when adding or editing a result, but the data can be added/removed in the
        # data manager. This way it's always synced.
        self.widgets.comboracepoint.set_data(Racepoint)
        self.widgets.combosector.set_data(Sector)
        self.widgets.combotype.set_data(Type)
        self.widgets.combocategory.set_data(Category)
        self.widgets.comboweather.set_data(Weather)
        self.widgets.combowind.set_data(Wind)

        self._set_entry_values(values)
        text = _("Edit result for:") if mode == enums.Action.edit else _("Add result for:")
        self.widgets.labelmode.set_text(text)
        # TODO: Setting modal doesn't work
        self.widgets.dialog.set_modal(mode == enums.Action.edit)
        self.widgets.dialog.show()
        self.widgets.entrydate.grab_focus()

    def _set_entry_values(self, values):
        placed = values["place"]
        self.widgets.checkplaced.set_active(bool(placed))

        self.widgets.entrydate.set_text(values["date"])
        self.widgets.comboracepoint.get_child().set_text(values["racepoint"])
        self.widgets.spinplaced.set_value(placed)
        self.widgets.spinoutof.set_value(values["out"])
        self.widgets.spinspeed.set_value(values["speed"])
        self.widgets.combosector.get_child().set_text(values["sector"])
        self.widgets.combotype.get_child().set_text(values["type"])
        self.widgets.combocategory.get_child().set_text(values["category"])
        self.widgets.comboweather.get_child().set_text(values["weather"])
        self.widgets.entrytemperature.set_text(values["temperature"])
        self.widgets.combowind.get_child().set_text(values["wind"])
        self.widgets.entrywindspeed.set_text(values["windspeed"])
        self.widgets.entrycomment.set_text(values["comment"])

    def _autofill_race(self):
        try:
            date = self.widgets.entrydate.get_text()
        except dateentry.InvalidDateInput as exc:
            ErrorDialog(exc.format_error(), self.widgets.dialog)
            return
        racepoint = self.widgets.comboracepoint.get_child().get_text()
        if date == "" or racepoint == "":
            # Don't bother checking
            return
        try:
            race = Result.get((Result.date == date) & (Result.racepoint == racepoint))
            ftype, wind, windspeed, weather, temperature = (
                race.type, race.wind, race.windspeed,
                race.weather, race.temperature)
        except Result.DoesNotExist:
            ftype, wind, windspeed, weather, temperature = "", "", "", "", ""
        self.widgets.combotype.get_child().set_text(ftype)
        self.widgets.combowind.get_child().set_text(wind)
        self.widgets.entrywindspeed.set_text(windspeed)
        self.widgets.comboweather.get_child().set_text(weather)
        self.widgets.entrytemperature.set_text(temperature)
