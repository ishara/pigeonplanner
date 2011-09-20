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
import gtk.gdk

import const
from ui import utils
from ui.tabs import basetab
from ui.detailsview import DetailsDialog
from translation import gettext as _


class RelativesTab(basetab.BaseTab):
    def __init__(self, mainwindow, database, parser):
        basetab.BaseTab.__init__(self, _("Relatives"), "icon_relatives.png")
        self.mainwindow = mainwindow
        self.database = database
        self.parser = parser

        treeviewdirect = gtk.TreeView()
        swdirect = gtk.ScrolledWindow()
        swdirect.set_shadow_type(gtk.SHADOW_IN)
        swdirect.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swdirect.add(treeviewdirect)
        aligndirect = gtk.Alignment(.5, .5, 1, 1)
        aligndirect.add(swdirect)
        framedirect = gtk.Frame(_("<b>Brothers and sisters</b>"))
        framedirect.set_shadow_type(gtk.SHADOW_NONE)
        framedirect.get_label_widget().set_use_markup(True)
        framedirect.add(aligndirect)
        self._liststoredirect = self._build_treeview(treeviewdirect)

        treeviewhalf = gtk.TreeView()
        swhalf = gtk.ScrolledWindow()
        swhalf.set_shadow_type(gtk.SHADOW_IN)
        swhalf.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swhalf.add(treeviewhalf)
        alignhalf = gtk.Alignment(.5, .5, 1, 1)
        alignhalf.add(swhalf)
        framehalf = gtk.Frame(_("<b>Half brothers and sisters</b>"))
        framehalf.set_shadow_type(gtk.SHADOW_NONE)
        framehalf.get_label_widget().set_use_markup(True)
        framehalf.add(alignhalf)
        self._liststorehalf = self._build_treeview(treeviewhalf, True)

        treeviewoff = gtk.TreeView()
        swoff = gtk.ScrolledWindow()
        swoff.set_shadow_type(gtk.SHADOW_IN)
        swoff.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swoff.add(treeviewoff)
        alignoff = gtk.Alignment(.5, .5, 1, 1)
        alignoff.add(swoff)
        frameoff = gtk.Frame(_("<b>Offspring</b>"))
        frameoff.set_shadow_type(gtk.SHADOW_NONE)
        frameoff.get_label_widget().set_use_markup(True)
        frameoff.add(alignoff)
        self._liststoreoff = self._build_treeview(treeviewoff)

        self._root = gtk.HBox(True)
        self._root.pack_start(framedirect, True, True, 4)
        self._root.pack_start(framehalf, True, True, 0)
        self._root.pack_start(frameoff, True, True, 4)
        self._root.show_all()

    # Callbacks
    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        path, col, cellx, celly = pthinfo
        pigeon = treeview.get_model()[path][0]

        if event.button == 3:
            utils.popup_menu(event, [
                                     (gtk.STOCK_INFO,
                                      self.on_show_details, (pigeon,)),
                                     (gtk.STOCK_JUMP_TO,
                                      self.on_goto_pigeon, (pigeon,)),
                                    ])
        elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.on_show_details(None, pigeon)

    def on_show_details(self, widget, pigeon):
        if not pigeon.get_pindex() in self.parser.pigeons:
            return
        DetailsDialog(self.database, self.parser, pigeon, self.mainwindow)

    def on_goto_pigeon(self, widget, pigeon):
        self.mainwindow.get_treeview().select_pigeon(None, pigeon.get_pindex())

    # Public methods
    def fill_treeviews(self, pigeon):
        self.clear_treeviews()
        pindex_selected = pigeon.get_pindex()
        pindex_sire_sel = pigeon.get_sire_pindex()
        pindex_dam_sel = pigeon.get_dam_pindex()
        for pindex, pigeon in self.parser.pigeons.items():
            ring, year = pigeon.get_band()
            pindex_sire = pigeon.get_sire_pindex()
            pindex_dam = pigeon.get_dam_pindex()
            sex = pigeon.get_sex()
            # Offspring
            if pindex_sire == pindex_selected or pindex_dam == pindex_selected:
                self._liststoreoff.insert(0, [pigeon, ring, year,
                                              sex, const.SEX_IMGS[sex]])
            # Half relatives
            if pindex_sire_sel and pindex_sire_sel == pindex_sire and not\
               (pindex_sire_sel == pindex_sire and pindex_dam_sel == pindex_dam):
                self._liststorehalf.insert(0, [pigeon, ring, year,
                                               pigeon.get_sire_string(True),
                                               sex, const.SEX_IMGS[sex]])
            if pindex_dam_sel and pindex_dam_sel == pindex_dam and not\
               (pindex_sire_sel == pindex_sire and pindex_dam_sel == pindex_dam):
                self._liststorehalf.insert(0, [pigeon, ring, year,
                                               pigeon.get_dam_string(True),
                                               sex, const.SEX_IMGS[sex]])
            # Direct relatives
            # We need both sire and dam to retrieve these
            if not pindex_sire_sel or not pindex_dam_sel: continue
            if pindex_sire_sel == pindex_sire and pindex_dam_sel == pindex_dam\
               and not pindex == pindex_selected:
                self._liststoredirect.insert(0, [pigeon, ring, year, sex,
                                                 const.SEX_IMGS[sex]])

        self._liststoredirect.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self._liststoredirect.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self._liststorehalf.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self._liststorehalf.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self._liststoreoff.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self._liststoreoff.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def clear_treeviews(self):
        self._liststoredirect.clear()
        self._liststorehalf.clear()
        self._liststoreoff.clear()

    # Internal methods
    def _build_treeview(self, treeview, extended=False):
        pb_id = 4
        store = [object, str, str, str, gtk.gdk.Pixbuf]
        columns = [_("Band no."), _("Year")]
        if extended:
            pb_id = 5
            store.insert(1, str)
            columns.append(_("Common parent"))
        liststore = gtk.ListStore(*store)
        treeview.set_model(liststore)
        treeview.connect('button-press-event', self.on_treeview_press)
        for index, column in enumerate(columns):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(column, textrenderer, text=index+1)
            tvcolumn.set_sort_column_id(index+1)
            tvcolumn.set_resizable(True)
            treeview.append_column(tvcolumn)
        pbrenderer = gtk.CellRendererPixbuf()
        pbrenderer.set_property('xalign', 0.0)
        tvcolumn = gtk.TreeViewColumn(_("Sex"), pbrenderer, pixbuf=pb_id)
        tvcolumn.set_sort_column_id(pb_id-1)
        tvcolumn.set_resizable(True)
        treeview.append_column(tvcolumn)

        return liststore

