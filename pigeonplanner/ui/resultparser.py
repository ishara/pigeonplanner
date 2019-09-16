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

try:
    from yapsy.VersionedPluginManager import VersionedPluginManager
    yapsy_available = True
except ImportError:
    yapsy_available = False

from pigeonplanner.ui import builder
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.widgets import dateentry
from pigeonplanner.ui.messagedialog import WarningDialog, ErrorDialog
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import mailing
from pigeonplanner.database.models import Result

logger = logging.getLogger(__name__)


class ResultParser(builder.GtkBuilder):
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "ResultParser.ui")
        self.data = None
        self.resultfilename = None

        self._build_interface()
        self.widgets.parserdialog.set_transient_for(parent)
        self.widgets.parserdialog.show_all()
        if yapsy_available:
            self._find_parsers()
        else:
            ErrorDialog((_("This tool needs Yapsy to run correctly."), None, ""),
                        self.widgets.parserdialog)

    def close_window(self, _widget=None, _event=None):
        self.widgets.parserdialog.destroy()
        return False

    def on_parsebutton_clicked(self, _widget):
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
            self.data, results = parser.parse_file(resultfile)
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

        self.widgets.datagrid.set_sensitive(True)
        self.widgets.liststore.clear()
        if not results:
            self.widgets.infobar.show()
            self.widgets.addbutton.set_sensitive(False)
            self.widgets.pigeonsw.set_sensitive(False)
            return
        self.widgets.infobar.hide()
        self.widgets.addbutton.set_sensitive(True)
        self.widgets.pigeonsw.set_sensitive(True)
        for pigeon, result in results.items():
            try:
                speedfloat = float(result[-1].replace(",", "."))
            except ValueError:
                result[-1] = ""
                speedfloat = 0.0
            row = result
            row.insert(0, pigeon)
            row.insert(0, True)
            row.append(speedfloat)
            self.widgets.liststore.append(row)

    # noinspection PyMethodMayBeStatic
    def on_helpbutton_clicked(self, _widget):
        common.open_help(9)

    def on_cancelbutton_clicked(self, _widget):
        self.close_window()

    def on_addbutton_clicked(self, _widget):
        point = self.widgets.racepointentry.get_text()
        out = self.widgets.pigeonsentry.get_text()
        try:
            date = self.widgets.dateentry.get_text()
            if point.strip() == "" or out.strip() == "":
                raise ValueError
            # Just raise a ValueError if it's not a number
            int(out)
        except (dateentry.InvalidDateInput, ValueError):
            ErrorDialog((_("The date, racepoint or number of pigeons is incorrect."),
                         None, ""), self.widgets.parserdialog)
            return
        sector = self.widgets.sectorentry.get_text()
        category = self.widgets.categoryentry.get_text()
        ftype = self.widgets.typeentry.get_text()
        wind = self.widgets.windentry.get_text()
        windspeed = self.widgets.windspeedentry.get_text()
        weather = self.widgets.weatherentry.get_text()
        temperature = self.widgets.temperatureentry.get_text()
        
        for row in self.widgets.liststore:
            toggle, pigeon, ring, year, place, speed, speedfloat = row
            if not toggle:
                continue
            data = {"date": date, "racepoint": point, "place": place,
                    "out": out, "sector": sector, "type": ftype, "category": category,
                    "wind": wind, "weather": weather, "comment": "",
                    "speed": speedfloat, "windspeed": windspeed, "temperature": temperature}

            try:
                query = Result.insert(pigeon=pigeon, **data)
                query.execute()
            except errors.IntegrityError:
                logger.info("Selected result already exists for pigeon id=%s band=%s", pigeon.id, pigeon.band_tuple)
        self.close_window()

    def on_celltoggle_toggled(self, _cell, path):
        self.widgets.liststore[path][0] = not self.widgets.liststore[path][0]

    def on_parsercombo_changed(self, widget):
        parserplugin = self._get_active_parserplugin()
        widget.set_tooltip_text(parserplugin.description)

    # noinspection PyMethodMayBeStatic
    def on_reportdialog_delete_event(self, _widget, _event):
        return True

    def on_closebutton_clicked(self, _widget):
        self.widgets.reportdialog.hide()

    def on_sendbutton_clicked(self, _widget):
        self.widgets.reportdialog.hide()
        textbuffer = self.widgets.textview.get_buffer()
        body = textbuffer.get_text(*textbuffer.get_bounds())
        subject = "[Pigeon Planner] Resultparser exception"
        try:
            mailing.send_email(const.REPORTMAIL, "", subject, body,
                               self.resultfilename)
        except Exception as exc:
            logger.error("Failed to send report: %s", exc)
            ErrorDialog((_("Failed to send report."), None, ""),
                        self.widgets.parserdialog)

    def _build_interface(self):
        self.widgets.sendbutton.set_use_stock(True)

        self.widgets.filebutton = filechooser.ResultChooser()
        self.widgets.grid.attach(self.widgets.filebutton, 1, 0, 1, 1)

    def _find_parsers(self):
        manager = VersionedPluginManager()
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
