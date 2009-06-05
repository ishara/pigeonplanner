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
import gtk.glade

import Const
import Print
import Results


class ResultWindow:
    def __init__(self, main, pigeons):

        self.gladefile = Const.GLADEDIR + "ResultWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_cbYearRace_changed'    : self.cbYearRace_changed,
                      'on_cbPigeon_changed'      : self.cbPigeon_changed,
                      'on_cbYearPigeons_changed' : self.cbYearPigeons_changed,
                      'on_cbRacepoint_changed'   : self.cbRacepoint_changed,
                      'on_cbSector_changed'      : self.cbSector_changed,
                      'on_sbCoefficient_changed' : self.sbCoefficient_changed,
                      'on_sbPlace_changed'       : self.sbPlace_changed,
                      'on_print_clicked'         : self.print_clicked,
                      'on_close_clicked'         : self.close,
                      'on_window_destroy'        : self.close}
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            setattr(self, name, w)

        self.pigeons = pigeons
        self.main = main

        self.resultwindow.set_transient_for(self.main.main)

        self.liststore = gtk.ListStore(str, str, int, int, float, str, str, str)
        renderer = gtk.CellRendererText()
        column1 = gtk.TreeViewColumn(_("Date"), renderer, text=0)
        column2 = gtk.TreeViewColumn(_("Racepoint"), renderer, text=1)
        column3 = gtk.TreeViewColumn(_("Placed"), renderer, text=2)
        column4 = gtk.TreeViewColumn(_("Out of"), renderer, text=3)
        column5 = gtk.TreeViewColumn(_("Coefficient"), renderer, text=4)
        column6 = gtk.TreeViewColumn(_("Sector"), renderer, text=5)
        self.column7 = gtk.TreeViewColumn(_("Band no."), renderer, text=6)
        self.column8 = gtk.TreeViewColumn()
        column1.set_resizable(True)
        column2.set_resizable(True)
        column3.set_resizable(True)
        column4.set_resizable(True)
        column5.set_resizable(True)
        column6.set_resizable(True)
        self.column7.set_resizable(True)
        column1.set_sort_column_id(0)
        column2.set_sort_column_id(1)
        column3.set_sort_column_id(2)
        column4.set_sort_column_id(3)
        column5.set_sort_column_id(4)
        column6.set_sort_column_id(5)
        self.column7.set_sort_column_id(6)
        self.column8.set_sort_column_id(7)
        self.treeviewres.set_model(self.liststore)
        self.treeviewres.append_column(self.column7)
        self.treeviewres.append_column(column1)
        self.treeviewres.append_column(column2)
        self.treeviewres.append_column(column3)
        self.treeviewres.append_column(column4)
        self.treeviewres.append_column(column5)
        self.treeviewres.append_column(column6)

        self.column7.connect('clicked', self.column7_clicked)

        self.block_handler = False

        self.pigeon = _("All")
        self.yearrace = _("All")
        self.yearpigeon = _("All")
        self.racepoint = _("All")
        self.sector = _("All")
        self.coef = 0
        self.place = 0
        self.set_results(True)

        self.liststore.set_sort_column_id(7, gtk.SORT_ASCENDING)
        self.column8.set_sort_order(gtk.SORT_DESCENDING)

    def close(self, widget, event=None):
        self.resultwindow.destroy()

    def print_clicked(self, widget):
        results = []
        for item in self.liststore:
            date = self.liststore.get_value(item.iter, 0)
            racepoint = self.liststore.get_value(item.iter, 1)
            placed = self.liststore.get_value(item.iter, 2)
            out = self.liststore.get_value(item.iter, 3)
            coef = self.liststore.get_value(item.iter, 4)
            sector = self.liststore.get_value(item.iter, 5)
            band = self.liststore.get_value(item.iter, 6)

            results.append({band : [date, racepoint, placed, out, coef, sector]})

        Print.PrintResults(results, self.yearpigeon, self.yearrace, self.racepoint, self.sector, self.coef, self.place)

    def column7_clicked(self, column):
        treeview = column.get_tree_view()
        liststore = treeview.get_model()

        if self.column8.get_sort_order() == gtk.SORT_ASCENDING:
            liststore.set_sort_column_id(7, gtk.SORT_ASCENDING)
            self.column8.set_sort_order(gtk.SORT_DESCENDING)
        else:
            liststore.set_sort_column_id(7, gtk.SORT_DESCENDING)
            self.column8.set_sort_order(gtk.SORT_ASCENDING)

    def cbPigeon_changed(self, widget):
        self.pigeon = widget.get_active_text()
        self.set_results()

    def cbYearRace_changed(self, widget):
        self.yearrace = widget.get_active_text()
        self.set_results()

    def cbYearPigeons_changed(self, widget):
        self.yearpigeon = widget.get_active_text()
        self.set_results()

    def cbRacepoint_changed(self, widget):
        self.racepoint = widget.get_active_text()
        self.set_results()

    def cbSector_changed(self, widget):
        self.sector = widget.get_active_text()
        self.set_results()

    def sbCoefficient_changed(self, widget):
        self.coef = widget.get_value_as_int()
        self.set_results()

    def sbPlace_changed(self, widget):
        self.place = widget.get_value_as_int()
        self.set_results()

    def set_results(self, combo=False):
        self.get_results(combo, self.pigeon, self.yearrace, self.yearpigeon, self.racepoint, self.sector, self.coef, self.place)

    def get_results(self, fill_combo, selpigeon, yearrace, yearpigeon, racepoint, sec, coef, place):
        if self.block_handler:
            return

        self.liststore.clear()

        numberOfResults = 0

        if fill_combo:
            pigeons = []
            yearRaces = []
            yearPigeons = []
            racepoints = []
            sectors = []

        for pigeon in self.pigeons:
            dics = Results.read_result(pigeon)
            if not dics:
                continue
            for dic in dics:
                date = dic['date']
                point = dic['point']
                placed = dic['place']
                out = dic['out']
                sector = dic['sector']

                cof = (float(placed)/float(out))*100
                band = pigeon + '/' + self.pigeons[pigeon].year[2:]
                bandsort = self.pigeons[pigeon].year + pigeon

                #TODO: This could (and should) be better I think...
                if ((racepoint == point or racepoint == _("All")) and\
                   (selpigeon[:7] == pigeon or selpigeon == _("All")) and\
                   (yearpigeon == self.pigeons[pigeon].year or yearpigeon == _("All")) and\
                   (yearrace == date[:4] or yearrace == _("All")) and\
                   (sec == sector or sec == _("All")) and\
                   (cof <= coef or coef == 0) and\
                   (placed <= place or place == 0)):

                    numberOfResults += 1

                    self.liststore.append([date, point, placed, out, cof, sector, band, bandsort])

                if fill_combo:
                    if not pigeon in pigeons:
                        pigeons.append(pigeon)

                    if not date[:4] in yearRaces:
                        yearRaces.append(date[:4])

                    if not self.pigeons[pigeon].year in yearPigeons:
                        yearPigeons.append(self.pigeons[pigeon].year)

                    if not point in racepoints:
                        racepoints.append(point)

                    if not sector in sectors and not sector == '':
                        sectors.append(sector)

        self.labelResults.set_text(str(numberOfResults))

        if fill_combo:
            pigeons.sort()
            pigeons.insert(0, _("All"))

            yearRaces.sort()
            yearRaces.insert(0, _("All"))

            yearPigeons.sort()
            yearPigeons.insert(0, _("All"))

            racepoints.sort()
            racepoints.insert(0, _("All"))

            sectors.sort()
            sectors.insert(0, _("All"))

            for item in pigeons:
                if not item == _("All"):
                    item = item + ' / ' + self.pigeons[item].year[2:]
                self.cbPigeon.get_model().append([item])

            for item in yearRaces:
                self.cbYearRace.get_model().append([item])

            for item in yearPigeons:
                self.cbYearPigeons.get_model().append([item])

            for item in racepoints:
                self.cbRacepoint.get_model().append([item])

            for item in sectors:
                self.cbSector.get_model().append([item])

            self.cbPigeon.set_wrap_width(2)
            self.cbRacepoint.set_wrap_width(2)

            self.block_handler = True
            self.cbPigeon.set_active(0)
            self.cbYearRace.set_active(0)
            self.cbYearPigeons.set_active(0)
            self.cbRacepoint.set_active(0)
            self.cbSector.set_active(0)
            self.block_handler = False

