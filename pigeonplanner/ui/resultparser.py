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


import logging
logger = logging.getLogger(__name__)

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import mailing
from pigeonplanner.resultparsers import get_all_parsers
from pigeonplanner.ui import filechooser


class ResultParser(builder.GtkBuilder):
    def __init__(self, parent, database, pigeons):
        builder.GtkBuilder.__init__(self, "ResultParser.ui")
        self.pigeons = pigeons
        self.database = database
        self.data = None

        self._build_interface()
        self._build_parsers()
        self.widgets.parserdialog.set_transient_for(parent)
        self.widgets.parserdialog.show_all()

    def close_window(self, widget=None, event=None):
        self.widgets.parserdialog.destroy()
        return False

    def on_parsebutton_clicked(self, widget):
        self.resultfilename = self.widgets.filebutton.get_filename()
        if self.resultfilename is None:
            return
        resultfile = open(self.resultfilename, 'r')
        parser = self._get_active_parser()
        try:
            self.data, results = parser.parse_file(resultfile, self.pigeons)
        except Exception as exc:
            import traceback
            data = [" **** File:", self.resultfilename,
                    "\n **** Parser:", parser.get_name(),
                    "\n **** Exception:", traceback.format_exc()]
            text = '\n'.join(data)
            textbuffer = self.widgets.textview.get_buffer()
            textbuffer.set_text(text)
            self.widgets.reportdialog.show()
            return
        self.widgets.datelabel.set_markup('<b>%s</b>' % self.data['date'])
        self.widgets.racepointlabel.set_markup('<b>%s</b>' % self.data['racepoint'])
        self.widgets.sectorlabel.set_markup('<b>%s</b>' % self.data['sector'])
        self.widgets.categorylabel.set_markup('<b>%s</b>' % self.data['category'])
        self.widgets.pigeonslabel.set_markup('<b>%s</b>' % self.data['n_pigeons'])
        self.widgets.liststore.clear()
        if not results:
            self.widgets.infobar.show()
            self.widgets.addbutton.set_sensitive(False)
            return
        self.widgets.infobar.hide()
        self.widgets.addbutton.set_sensitive(True)
        for pindex, result in results.items():
            row = result
            row.insert(0, pindex)
            row.insert(0, True)
            self.widgets.liststore.append(row)

    def on_helpbutton_clicked(self, widget):
        common.open_help(9)

    def on_cancelbutton_clicked(self, widget):
        self.close_window()

    def on_addbutton_clicked(self, widget):
        date = self.data['date']
        point = self.data['racepoint']
        out = self.data['n_pigeons']
        sector = self.data['sector']
        category = self.data['category']
        for row in self.widgets.liststore:
            toggle, pindex, ring, year, place = row
            if not toggle: continue
            data = [pindex, date, point, place, out, sector, '', category,
                    '', '', '', '', 0, 0, '']
            if self.database.has_result(data):
                logger.info('Pigeon %s already has the selected result' % pindex)
            else:
                self.database.insert_into_table(self.database.RESULTS, data)
        self.close_window()

    def on_celltoggle_toggled(self, cell, path):
        self.widgets.liststore[path][0] = not self.widgets.liststore[path][0]

    def on_parsercombo_changed(self, widget):
        parser = self._get_active_parser()
        widget.set_tooltip_text(parser.get_description())

    def on_reportdialog_delete_event(self, widget, event):
        return True

    def on_closebutton_clicked(self, widget):
        self.widgets.reportdialog.hide()

    def on_sendbutton_clicked(self, widget):
        self.widgets.reportdialog.hide()
        textbuffer = self.widgets.textview.get_buffer()
        body = textbuffer.get_text(*textbuffer.get_bounds())
        subject = "[Pigeon Planner] Resultparser exception"
        mailing.send_email(const.REPORTMAIL, '', subject, body,
                           self.resultfilename)

    def _build_interface(self):
        self.widgets.sendbutton.set_use_stock(True)

        self.widgets.filebutton = filechooser.ResultChooser()
        self.widgets.table.attach(self.widgets.filebutton, 1, 2, 0, 1)

    def _build_parsers(self):
        parsers = get_all_parsers()
        for parser in parsers:
            parser = parser()
            self.widgets.parserstore.append([parser, parser.get_name()])
        self.widgets.parsercombo.set_active(0)

    def _get_active_parser(self):
        comboiter = self.widgets.parsercombo.get_active_iter()
        return self.widgets.parserstore.get_value(comboiter, 0)

