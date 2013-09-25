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


import os
import logging
logger = logging.getLogger(__name__)

from yapsy.PluginManager import PluginManager

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import mailing
from pigeonplanner import database
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.messagedialog import WarningDialog


class ResultParser(builder.GtkBuilder):
    def __init__(self, parent, pigeons):
        builder.GtkBuilder.__init__(self, "ResultParser.ui")
        self.pigeons = pigeons
        self.data = None

        self._build_interface()
        self._find_parsers()
        self.widgets.parserdialog.set_transient_for(parent)
        self.widgets.parserdialog.show_all()

    def close_window(self, widget=None, event=None):
        self.widgets.parserdialog.destroy()
        return False

    def on_parsebutton_clicked(self, widget):
        self.resultfilename = self.widgets.filebutton.get_filename()
        if self.resultfilename is None:
            return
        resultfile = open(self.resultfilename, "r")
        parserplugin = self._get_active_parserplugin()
        parser = parserplugin.plugin_object
        if not parser.check(resultfile):
            msg = (_("This result is not in the '%s' format. Do you want to continue?") % 
                   parserplugin.name, None, None)
            if not WarningDialog(msg, self.widgets.parserdialog).run():
                return
        resultfile.seek(0)
        try:
            self.data, results = parser.parse_file(resultfile, self.pigeons)
        except Exception:
            import traceback
            data = [" **** File:", self.resultfilename,
                    "\n **** Parser:", "%s %s" % (parserplugin.name, parserplugin.version),
                    "\n **** Exception:", traceback.format_exc()]
            text = "\n".join(data)
            textbuffer = self.widgets.textview.get_buffer()
            textbuffer.set_text(text)
            self.widgets.reportdialog.show()
            return

        self.widgets.dateentry.set_text(self.data["date"])
        self.widgets.racepointentry.set_text(self.data["racepoint"].title())
        self.widgets.sectorentry.set_text(self.data["sector"].title())
        self.widgets.categoryentry.set_text(self.data["category"].title())
        self.widgets.pigeonsentry.set_text(self.data["n_pigeons"])

        self.widgets.datatable.set_sensitive(True)
        self.widgets.liststore.clear()
        if not results:
            self.widgets.infobar.show()
            self.widgets.addbutton.set_sensitive(False)
            self.widgets.pigeonsw.set_sensitive(False)
            return
        self.widgets.infobar.hide()
        self.widgets.addbutton.set_sensitive(True)
        self.widgets.pigeonsw.set_sensitive(True)
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
        date = self.widgets.dateentry.get_text()
        point = self.widgets.racepointentry.get_text()
        out = self.widgets.pigeonsentry.get_text()
        sector = self.widgets.sectorentry.get_text()
        category = self.widgets.categoryentry.get_text()
        for row in self.widgets.liststore:
            toggle, pindex, ring, year, place = row
            if not toggle: continue
            data = {"pindex": pindex, "date": date, "point": point, "place": place,
                    "out": out, "sector": sector, "type": "", "category": category,
                    "wind": "", "weather": "", "put": "", "back": "",
                    "ownplace": 0, "ownout": 0, "comment": ""}
            if database.result_exists(data):
                logger.info("Pigeon %s already has the selected result" % pindex)
            else:
                database.add_result(data)
        self.close_window()

    def on_celltoggle_toggled(self, cell, path):
        self.widgets.liststore[path][0] = not self.widgets.liststore[path][0]

    def on_parsercombo_changed(self, widget):
        parserplugin = self._get_active_parserplugin()
        widget.set_tooltip_text(parserplugin.description)

    def on_reportdialog_delete_event(self, widget, event):
        return True

    def on_closebutton_clicked(self, widget):
        self.widgets.reportdialog.hide()

    def on_sendbutton_clicked(self, widget):
        self.widgets.reportdialog.hide()
        textbuffer = self.widgets.textview.get_buffer()
        body = textbuffer.get_text(*textbuffer.get_bounds())
        subject = "[Pigeon Planner] Resultparser exception"
        mailing.send_email(const.REPORTMAIL, "", subject, body,
                           self.resultfilename)

    def _build_interface(self):
        self.widgets.sendbutton.set_use_stock(True)

        self.widgets.filebutton = filechooser.ResultChooser()
        self.widgets.table.attach(self.widgets.filebutton, 1, 2, 0, 1)

    def _find_parsers(self):
        manager = PluginManager()
        manager.setPluginPlaces([const.RESULTPARSERDIR,
                                 os.path.join(const.PLUGINDIR, "resultparsers")])
        manager.collectPlugins()

        for plugin in manager.getAllPlugins():
            name = "%s - %s" % (plugin.name, plugin.version)
            self.widgets.parserstore.append([plugin, name])
        self.widgets.parsercombo.set_active(0)

    def _get_active_parserplugin(self):
        comboiter = self.widgets.parsercombo.get_active_iter()
        return self.widgets.parserstore.get_value(comboiter, 0)

