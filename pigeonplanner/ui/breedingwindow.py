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

import csv
import datetime

from gi.repository import Gtk
from gi.repository import GObject

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui.filechooser import ExportChooser
from pigeonplanner.core import enums
from pigeonplanner.database.models import Breeding


class BreedingWindow(builder.GtkBuilder):
    (
        LS_OBJ,
        LS_DATE,
        LS_COCK,
        LS_HEN,
        LS_EGG_1_LAID,
        LS_EGG_1_HATCHED,
        LS_EGG_1_BAND,
        LS_EGG_2_LAID,
        LS_EGG_2_HATCHED,
        LS_EGG_2_BAND,
        LS_COCK_TUPLE,
        LS_HEN_TUPLE,
        LS_EGG_1_BAND_TUPLE,
        LS_EGG_2_BAND_TUPLE,
    ) = range(14)

    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "BreedingWindow.ui")

        self._filter = utils.TreeviewFilter()
        self._fill_treeview()
        self.widgets.treemodelfilter = self._builder.get_object("treemodelfilter")
        self.widgets.treemodelfilter.set_visible_func(self._visible_func)

        self.widgets.checkcockband.bind_property(
            "active", self.widgets.bandentrycock, "sensitive", GObject.BindingFlags.DEFAULT
        )
        self.widgets.checkhenband.bind_property(
            "active", self.widgets.bandentryhen, "sensitive", GObject.BindingFlags.DEFAULT
        )
        self.widgets.checkegg1band.bind_property(
            "active", self.widgets.bandentryegg1, "sensitive", GObject.BindingFlags.DEFAULT
        )
        self.widgets.checkegg2band.bind_property(
            "active", self.widgets.bandentryegg2, "sensitive", GObject.BindingFlags.DEFAULT
        )

        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show()

    def on_close_window(self, _widget, _event=None):
        self.widgets.window.destroy()

    def on_filterdialog_close(self, _widget, _event=None):
        self.widgets.filterdialog.hide()
        return True

    def on_export_clicked(self, _widget):
        default_filename = "%s_%s.csv" % (_("Breeding"), datetime.date.today())
        chooser = ExportChooser(self.widgets.window, default_filename, ("CSV", "*.csv"))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            self._export_data(filename)
        chooser.destroy()

    def on_filter_clicked(self, _widget):
        self.widgets.filterdialog.show()

    def on_filterclear_clicked(self, _widget):
        for item in ["date", "egg1laid", "egg1hatched", "egg2laid", "egg2hatched"]:
            getattr(self.widgets, "combo" + item).set_active(0)
            getattr(self.widgets, "entry" + item).set_text("")
        for check in ["cockband", "henband", "egg1band", "egg2band"]:
            getattr(self.widgets, "check" + check).set_active(False)
        for bandentry in ["cock", "hen", "egg1", "egg2"]:
            getattr(self.widgets, "bandentry" + bandentry).clear()

        self._filter.clear()
        self.widgets.treemodelfilter.refilter()

    def on_filtersearch_clicked(self, _widget):
        self._filter.clear()

        if self.widgets.checkcockband.get_active():
            band = self.widgets.bandentrycock.get_band(False)
            self._filter.add(self.LS_COCK_TUPLE, band, type_=tuple, allow_empty_value=True)

        if self.widgets.checkhenband.get_active():
            band = self.widgets.bandentryhen.get_band(False)
            self._filter.add(self.LS_HEN_TUPLE, band, type_=tuple, allow_empty_value=True)

        if self.widgets.checkegg1band.get_active():
            band = self.widgets.bandentryegg1.get_band(False)
            self._filter.add(self.LS_EGG_1_BAND_TUPLE, band, type_=tuple, allow_empty_value=True)

        if self.widgets.checkegg2band.get_active():
            band = self.widgets.bandentryegg2.get_band(False)
            self._filter.add(self.LS_EGG_2_BAND_TUPLE, band, type_=tuple, allow_empty_value=True)

        date = self.widgets.entrydate.get_text(validate=False)
        dateop = self.widgets.combodate.get_operator()
        self._filter.add(self.LS_DATE, date, dateop)

        date = self.widgets.entryegg1laid.get_text(validate=False)
        dateop = self.widgets.comboegg1laid.get_operator()
        self._filter.add(self.LS_EGG_1_LAID, date, dateop)

        date = self.widgets.entryegg1hatched.get_text(validate=False)
        dateop = self.widgets.comboegg1hatched.get_operator()
        self._filter.add(self.LS_EGG_1_HATCHED, date, dateop)

        date = self.widgets.entryegg2laid.get_text(validate=False)
        dateop = self.widgets.comboegg2laid.get_operator()
        self._filter.add(self.LS_EGG_2_LAID, date, dateop)

        date = self.widgets.entryegg2hatched.get_text(validate=False)
        dateop = self.widgets.comboegg2hatched.get_operator()
        self._filter.add(self.LS_EGG_2_HATCHED, date, dateop)

        self.widgets.treemodelfilter.refilter()

    # noinspection PyMethodMayBeStatic
    def on_bandentrycock_search_clicked(self, _widget):
        return None, enums.Sex.cock, None

    # noinspection PyMethodMayBeStatic
    def on_bandentryhen_search_clicked(self, _widget):
        return None, enums.Sex.hen, None

    # noinspection PyMethodMayBeStatic
    def on_bandentryegg1_search_clicked(self, _widget):
        return None, None, None

    # noinspection PyMethodMayBeStatic
    def on_bandentryegg2_search_clicked(self, _widget):
        return None, None, None

    def get_report_data(self):
        data = []
        for row in self.widgets.treemodelfilter:
            temp = []
            for col in (
                self.LS_DATE,
                self.LS_COCK,
                self.LS_HEN,
                self.LS_EGG_1_LAID,
                self.LS_EGG_1_HATCHED,
                self.LS_EGG_1_BAND,
                self.LS_EGG_2_LAID,
                self.LS_EGG_2_HATCHED,
                self.LS_EGG_2_BAND,
            ):
                temp.append(self.widgets.treemodelfilter.get_value(row.iter, col))
            data.append(temp)
        return data

    def _export_data(self, filename):
        data = self.get_report_data()
        header = [
            _("Date"),
            _("Cock"),
            _("Hen"),
            _("Egg 1 laid"),
            _("Egg 1 hatched"),
            _("Egg 1 bandnumber"),
            _("Egg 2 laid"),
            _("Egg 2 hatched"),
            _("Egg 2 bandnumber"),
        ]
        with open(filename, "w", encoding="utf-8-sig") as output:
            writer = csv.writer(output, dialect=csv.excel, quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(data)

    def _fill_treeview(self):
        for record in Breeding.select():
            row = [
                record,
                str(record.date),
                record.sire.band,
                record.dam.band,
                str(record.laid1),
                str(record.hatched1),
                record.child1.band if record.child1 is not None else "",
                str(record.laid2),
                str(record.hatched2),
                record.child2.band if record.child2 is not None else "",
                record.sire.band_tuple,
                record.dam.band_tuple,
                record.child1.band_tuple if record.child1 is not None else (),
                record.child2.band_tuple if record.child2 is not None else (),
            ]
            self.widgets.liststore.append(row)

    def _visible_func(self, model, treeiter, _data=None):
        for item in self._filter:
            modelvalue = model.get_value(treeiter, item.name)
            if not item.operator(modelvalue, item.value):
                return False
        return True
