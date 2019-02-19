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
import gobject

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.core import enums
from pigeonplanner.core import const
from pigeonplanner.core import config
from pigeonplanner.database.models import Pigeon, Colour, Strain, Loft


class FilterDialog(builder.GtkBuilder):
    def __init__(self, treeview):
        builder.GtkBuilder.__init__(self, "FilterDialog.ui")
        self.treeview = treeview

        self.filter = utils.TreeviewFilter()

    def show(self, parent):
        self.widgets.combocolour.set_data(Colour, active=None)
        self.widgets.combostrain.set_data(Strain, active=None)
        self.widgets.comboloft.set_data(Loft, active=None)

        self.widgets.filterdialog.set_transient_for(parent)
        self.widgets.filterdialog.show_all()

    def hide(self):
        self.widgets.filterdialog.hide()

    def on_close(self, widget, event=None):
        self.widgets.filterdialog.hide()
        return True

    def on_spinbutton_output(self, widget):
        value = widget.get_value_as_int()
        text = "" if value == 0 else str(value)
        widget.set_text(text)
        return True

    def on_checksex_toggled(self, widget):
        self.widgets.combosex.set_sensitive(widget.get_active())

    def on_checkstatus_toggled(self, widget):
        self.widgets.combostatus.set_sensitive(widget.get_active())

    def on_checksire_toggled(self, widget):
        self.widgets.bandentrysire.set_sensitive(widget.get_active())

    def on_checkdam_toggled(self, widget):
        self.widgets.bandentrydam.set_sensitive(widget.get_active())

    def on_bandentrysire_search_clicked(self, widget):
        return None, enums.Sex.cock, None

    def on_bandentrydam_search_clicked(self, widget):
        return None, enums.Sex.hen, None

    def on_clear_clicked(self, widget):
        for combo in ["year", "sex", "status"]:
            getattr(self.widgets, "combo"+combo).set_active(0)
        for spin in ["year"]:
            getattr(self.widgets, "spin"+spin).set_value(0)
        for combo in ["colour", "strain", "loft"]:
            getattr(self.widgets, "combo"+combo).child.set_text("")
        for check in ["sex", "status", "sire", "dam"]:
            getattr(self.widgets, "check"+check).set_active(False)
        self.widgets.bandentrysire.clear()
        self.widgets.bandentrydam.clear()

        self.filter.clear()
        self.treeview._modelfilter.refilter()
        component.get("Statusbar").set_filter(False)
        self.treeview.emit("pigeons-changed")

    def on_search_clicked(self, widget):
        self.filter.clear()

        year = self.widgets.spinyear.get_value_as_int()
        yearop = self.widgets.comboyear.get_operator()
        self.filter.add("band_year", year, yearop, int)

        if self.widgets.checksex.get_active():
            sex = self.widgets.combosex.get_sex()
            self.filter.add("sex", sex, type_=int, allow_empty_value=True)

        if self.widgets.checkstatus.get_active():
            status = self.widgets.combostatus.get_status()
            self.filter.add("status_id", status, type_=int, allow_empty_value=True)

        if self.widgets.checksire.get_active():
            sire = self.widgets.bandentrysire.get_band(False)
            self.filter.add("sire_filter", sire, type_=tuple, allow_empty_value=True)

        if self.widgets.checkdam.get_active():
            dam = self.widgets.bandentrydam.get_band(False)
            self.filter.add("dam_filter", dam, type_=tuple, allow_empty_value=True)

        colour = self.widgets.combocolour.child.get_text()
        self.filter.add("colour", colour)

        strain = self.widgets.combostrain.child.get_text()
        self.filter.add("strain", strain)

        loft = self.widgets.comboloft.child.get_text()
        self.filter.add("loft", loft)

        self.treeview._modelfilter.refilter()
        component.get("Statusbar").set_filter(self.filter.has_filters())
        self.treeview.emit("pigeons-changed")


class MainTreeView(gtk.TreeView, component.Component):

    __gtype_name__ = "MainTreeView"
    __gsignals__ = {"pigeons-changed": (gobject.SIGNAL_RUN_LAST, None, ())}

    (LS_PIGEON,
     LS_RING,
     LS_YEAR,
     LS_COUNTRY,
     LS_NAME,
     LS_COLOUR,
     LS_SEX,
     LS_SIRE,
     LS_DAM,
     LS_LOFT,
     LS_STRAIN,
     LS_STATUS,
     LS_SEXIMG) = range(13)

    (COL_BAND,
     COL_YEAR,
     COL_COUNTRY,
     COL_NAME,
     COL_COLOUR,
     COL_SEX,
     COL_SIRE,
     COL_DAM,
     COL_LOFT,
     COL_STRAIN,
     COL_STATUS) = range(11)

    def __init__(self):
        gtk.TreeView.__init__(self)
        component.Component.__init__(self, "Treeview")

        self._block_visible_func = False

        component.get("Statusbar").set_filter(False)
        self._liststore = self._build_treeview()
        self._modelfilter = self._liststore.filter_new()
        self._modelfilter.set_visible_func(self._visible_func)
        self._modelsort = gtk.TreeModelSort(self._modelfilter)
        self._modelsort.set_sort_func(self.LS_YEAR, self._sort_func)
        self._modelsort.set_sort_column_id(self.LS_YEAR, gtk.SORT_ASCENDING)
        self.set_model(self._modelsort)
        self.set_rules_hint(True)
        self._selection = self.get_selection()
        self._selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.set_columns()
        self.show_all()

        self._filterdialog = FilterDialog(self)

    # Public methods
    def get_top_iter(self, rowiter):
        filteriter = self._modelfilter.convert_child_iter_to_iter(rowiter)
        return self._modelsort.convert_child_iter_to_iter(None, filteriter)

    def get_child_iter(self, rowiter):
        filteriter = self._modelsort.convert_iter_to_child_iter(None, rowiter)
        return self._modelfilter.convert_iter_to_child_iter(filteriter)

    def get_top_path(self, path):
        filterpath = self._modelfilter.convert_child_path_to_path(path)
        return self._modelsort.convert_child_path_to_path(filterpath)

    def get_child_path(self, path):
        filterpath = self._modelsort.convert_path_to_child_path(path)
        return self._modelfilter.convert_path_to_child_path(filterpath)

    def add_row(self, row, select=True):
        rowiter = self._liststore.insert(0, row)
        if select:
            try:
                topiter = self.get_top_iter(rowiter)
            except RuntimeError:
                # This happens when a pigeon is added which falls outside the current
                # active filter. It means the pigeon shouldn't be shown and thus there
                # is no iter for the row.
                pass
            else:
                path = self._liststore.get_path(rowiter)
                self._selection.unselect_all()
                self._selection.select_iter(topiter)
                self.scroll_to_cell(self.get_top_path(path))
        self.emit("pigeons-changed")

    def update_row(self, data, rowiter=None, path=None):
        if rowiter is None and path is None:
            raise ValueError("A path or iter is required!")
        if rowiter is None:
            rowiter = self._liststore.get_iter(path)
        self._liststore.set(rowiter, *data)
        self.emit("pigeons-changed")

    def remove_row(self, path):
        sortiter = self._modelsort.get_iter(path)
        rowiter = self.get_child_iter(sortiter)
        self._liststore.remove(rowiter)
        self.emit("pigeons-changed")

    def get_n_rows(self):
        return len(self._liststore)

    def fill_treeview(self, path=0):
        # Block the function that checks if a row needs to be shown or not.
        # This is an expensive operation and is called on each insert. This slows
        # down startup with many pigeons. The check is useless anyway when pigeons
        # are inserted through this method as the database query will handle this.
        self._block_visible_func = True
        self._liststore.clear()

        query = Pigeon.select()
        if not config.get("interface.show-all-pigeons"):
            query = query.where(Pigeon.visible == True)
        for pigeon in query:
            self._liststore.insert(0, self._row_for_pigeon(pigeon))

        self._selection.select_path(path)
        self.emit("pigeons-changed")

        self._block_visible_func = False

    def add_pigeon(self, pigeon, select=True):
        self.add_row(self._row_for_pigeon(pigeon), select)

    def update_pigeon(self, pigeon, rowiter=None, path=None):
        if rowiter is None and path is None:
            path = self.get_path_for_pigeon(pigeon)
            path = self.get_child_path(path)

        data = (
            self.LS_PIGEON, pigeon.id,
            self.LS_RING, pigeon.band,
            self.LS_YEAR, pigeon.band_year,
            self.LS_COUNTRY, pigeon.band_country,
            self.LS_NAME, pigeon.name,
            self.LS_COLOUR, pigeon.colour,
            self.LS_SEX, pigeon.sex_string,
            self.LS_SIRE, "" if pigeon.sire is None else pigeon.sire.band,
            self.LS_DAM, "" if pigeon.dam is None else pigeon.dam.band,
            self.LS_LOFT, pigeon.loft,
            self.LS_STRAIN, pigeon.strain,
            self.LS_STATUS, pigeon.status.status_string,
            self.LS_SEXIMG, utils.get_sex_image(pigeon.sex)
        )
        self.update_row(data, rowiter=rowiter, path=path)

    def has_pigeon(self, pigeon):
        for row in self._liststore:
            if self._liststore.get_value(row.iter, self.LS_PIGEON) == pigeon.id:
                return True
        return False

    def select_pigeon(self, widget, pigeon):
        """Select the pigeon in the main treeview

        :param widget: Only given when selected through menu
        :param pigeon: The pigeon object to search
        """
        for row in self._modelsort:
            if self._modelsort.get_value(row.iter, self.LS_PIGEON) == pigeon.id:
                self._selection.unselect_all()
                self._selection.select_iter(row.iter)
                self.scroll_to_cell(row.path)
                self.grab_focus()
                return True
        return False

    def select_all_pigeons(self):
        self._selection.select_all()

    def get_pigeons(self, filtered=False):
        model = self._modelsort if filtered else self._liststore
        ids = [row[self.LS_PIGEON] for row in model]
        if const.WINDOWS and len(ids) > 998:
            # SQLite has a limit on number of variables in a query, often denoted as a question mark. This
            # is a compile time setting (SQLITE_MAX_VARIABLE_NUMBER) and cannot be changed during runtime.
            # The default is 999 and is only kept on Windows. The value on macOS is 500000 and 250000 on
            # Linux. The limit on Windows is quite easily reached, especially when hidden pigeons are shown
            # as well. Multiple users reported this problem. The solution is to retrieve the Pigeon objects
            # in chunks that are just under the limit. Since this workaround is slower than the original
            # query, only apply this if the limited conditions are met.
            chunk_size = 998
            pigeons = []
            for i in range(0, len(ids), chunk_size):
                query = Pigeon.select().where(Pigeon.id.in_(ids[i:i + chunk_size]))
                pigeons.extend([pigeon for pigeon in query])
            return pigeons
        return Pigeon.select().where(Pigeon.id.in_(ids))

    def get_selected_pigeon(self):
        model, paths = self._selection.get_selected_rows()
        if len(paths) == 1:
            path = paths[0]
            return Pigeon.get_by_id(model[path][self.LS_PIGEON])
        elif len(paths) > 1:
            ids = [model[path][self.LS_PIGEON] for path in paths]
            return Pigeon.select().where(Pigeon.id.in_(ids))
        else:
            return None

    def get_path_for_pigeon(self, pigeon):
        for row in self._liststore:
            if row[self.LS_PIGEON] == pigeon.id:
                return self.get_top_path(row.path)[0]

    def get_pigeon_at_path(self, path):
        path = self.get_child_path(path)
        return Pigeon.get_by_id(self._liststore[path][self.LS_PIGEON])

    def set_columns(self):
        columnsdic = {self.COL_COUNTRY: config.get("columns.pigeon-band-country"),
                      self.COL_NAME: config.get("columns.pigeon-name"),
                      self.COL_COLOUR: config.get("columns.pigeon-colour"),
                      self.COL_SEX: config.get("columns.pigeon-sex"),
                      self.COL_SIRE: config.get("columns.pigeon-sire"),
                      self.COL_DAM: config.get("columns.pigeon-dam"),
                      self.COL_LOFT: config.get("columns.pigeon-loft"),
                      self.COL_STRAIN: config.get("columns.pigeon-strain"),
                      self.COL_STATUS: config.get("columns.pigeon-status")}
        for key, value in columnsdic.items():
            self.get_column(key).set_visible(value)
            if key == self.COL_SEX and value:
                sexcoltype = config.get("columns.pigeon-sex-type")
                for renderer in self.get_column(key).get_cell_renderers():
                    if isinstance(renderer, gtk.CellRendererText):
                        text = renderer
                    else:
                        pixbuf = renderer
                text.set_visible(sexcoltype == 1 or sexcoltype == 3)
                pixbuf.set_visible(sexcoltype == 2 or sexcoltype == 3)

    def run_filterdialog(self, parent):
        self._filterdialog.show(parent)

    # Internal methods
    def _build_treeview(self):
        liststore = gtk.ListStore(int, str, str, str, str, str, str, str,
                                  str, str, str, str, gtk.gdk.Pixbuf)
        columns = [_("Band no."), _("Year"), _("Country"), _("Name"), _("Colour"), _("Sex"),
                   _("Sire"), _("Dam"), _("Loft"), _("Strain"), _("Status")]
        for index, column in enumerate(columns):
            tvcolumn = gtk.TreeViewColumn(column)
            if index == self.COL_SEX:
                renderer = gtk.CellRendererPixbuf()
                tvcolumn.pack_start(renderer, expand=False)
                tvcolumn.add_attribute(renderer, "pixbuf", self.LS_SEXIMG)
            textrenderer = gtk.CellRendererText()
            tvcolumn.pack_start(textrenderer, expand=False)
            tvcolumn.add_attribute(textrenderer, "text", index+1)
            tvcolumn.set_sort_column_id(index+1)
            tvcolumn.set_resizable(True)
            self.append_column(tvcolumn)
        return liststore

    def _row_for_pigeon(self, pigeon):
        return [
            pigeon.id,
            pigeon.band,
            pigeon.band_year,
            pigeon.band_country,
            pigeon.name,
            pigeon.colour,
            pigeon.sex_string,
            "" if pigeon.sire is None else pigeon.sire.band,
            "" if pigeon.dam is None else pigeon.dam.band,
            pigeon.loft,
            pigeon.strain,
            pigeon.status.status_string,
            utils.get_sex_image(pigeon.sex)
        ]

    def _visible_func(self, model, treeiter):
        if self._block_visible_func:
            return True
        pigeon = Pigeon.get_by_id(model[treeiter][self.LS_PIGEON])
        for item in self._filterdialog.filter:
            pvalue = getattr(pigeon, item.name)
            if not item.operator(item.type(pvalue), item.type(item.value)):
                return False
        return True

    def _sort_func(self, model, iter1, iter2):
        data1 = model.get_value(iter1, self.LS_YEAR)
        data2 = model.get_value(iter2, self.LS_YEAR)
        if data1 == data2:
            data1 = model.get_value(iter1, self.LS_RING)
            data2 = model.get_value(iter2, self.LS_RING)
        return cmp(data1, data2)
