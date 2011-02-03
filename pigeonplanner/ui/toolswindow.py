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

"""
Tools window class
"""


import datetime
import logging
logger = logging.getLogger(__name__)

import gtk

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import backup
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner import printing
from pigeonplanner.ui import dialogs
from pigeonplanner.ui.widgets import filefilters


class ToolsWindow(builder.GtkBuilder):
    def __init__(self, main):
        builder.GtkBuilder.__init__(self, const.GLADETOOLS)

        self.main = main
        self.db = self.main.database

        self.toolsdialog.set_transient_for(self.main.mainwindow)

        distance_units = [
                    (_('Yards'), 0.9144),
                    (_('Kilometres'), 1000),
                    (_('Metres'), 1),
                    (_('Centimetres'), 0.01),
                    (_('Inches'), 0.025),
                    (_('Feet'), 0.3048),
                    (_('Miles'), 1609.344),
                    (_('Nautical Miles'), 1852)
            ]
        speed_units = [
                (_('Yard per Minute'), 0.01524),
                (_('Metres per Minute'), 0.0166666666),
                (_('Metres per Second'), 1),
                (_('Kilometre per Hour'), 0.27777777777777777777777777777777),
                (_('Feet per Second'), 0.3048),
                (_('Feet per Minute'), 0.00508),
                (_('Mile per Hour'), 0.44704)
            ]

        for item in distance_units:
            self.ls_dist_units.append(item)
        for item in speed_units:
            self.ls_speed_units.append(item)

        self.combobox_velocity_distance.set_active(0)
        self.combobox_velocity_speed.set_active(0)
        self.combobox_prognosis_distance.set_active(0)
        self.combobox_prognosis_speed.set_active(0)

        # Build main treeview
        self.selection = self.treeview.get_selection()
        self.selection.connect('changed', self.selection_changed)

        # Add the categories
        i = 0
        for category in [_("Velocity calculator"),
                         _("Datasets"), _("Statistics"), _("Backup")]:
            self.liststore.append([i, category])
            label = getattr(self, "label_title_%s" %i)
            label.set_markup("<b><i><big>%s</big></i></b>" %category)
            i += 1

        self.treeview.set_cursor(0)

        # Build other treeviews
        self.sel_velocity = self.tv_velocity.get_selection()

        self.sel_stats = self.tvstats.get_selection()

        # Fill spinbuttons
        dt = datetime.datetime.now()
        self.spinbutton_prognosis_hours.set_value(dt.hour)
        self.spinbutton_prognosis_minutes.set_value(dt.minute)
        self.spinbutton_prognosis_seconds.set_value(dt.second)

        # Backups file filter
        self.fcButtonRestore.add_filter(filefilters.BackupFilter())

        # Fill the data combobox
        data = [_("Colours"), _("Racepoints"), _("Sectors"), _("Types"),
                _("Categories"), _("Strains"), _("Lofts"), _("Weather"),
                _("Wind")]
        data.sort()
        for item in data:
            self.cbdata.append_text(item)
            self.cbdata2.append_text(item)
        self.cbdata.set_active(0)
        self.cbdata2.set_active(0)

        self.toolsdialog.show()

    def on_close_dialog(self, widget=None, event=None):
        self.toolsdialog.destroy()

    def selection_changed(self, selection):
        model, path = selection.get_selected()
        if not path: return

        try:
            self.notebook.set_current_page(model[path][0])
        except TypeError:
            pass

    # Velocity
    def on_spinbutton_time_changed(self, widget):
        value = widget.get_value_as_int()
        widget.set_text(common.add_zero_to_time(value))

    ## Exact
    def on_button_velocity_calculate_clicked(self, widget):
        dist_iter = self.combobox_velocity_distance.get_active_iter()
        distunit = self.ls_dist_units.get(dist_iter, 1)[0]
        speed_iter = self.combobox_velocity_speed.get_active_iter()
        speedunit = self.ls_speed_units.get(speed_iter, 1)[0]

        distance = self.spinbutton_velocity_distance.get_value()
        hours = self.spinbutton_velocity_hours.get_value_as_int()
        minutes = self.spinbutton_velocity_minutes.get_value_as_int()
        seconds = self.spinbutton_velocity_seconds.get_value_as_int()
        seconds_total = (hours * 3600) + (minutes * 60) + seconds
        if seconds_total == 0:
            self.spinbutton_velocity_seconds.set_value(1)
            seconds_total = 1

        speed = (distance * distunit) / (seconds_total * speedunit)
        self.entry_velocity_result.set_text("%.6f" %speed)

    ## Prognosis
    def on_spinbutton_prognosis_from_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]

        self.spinbutton_prognosis_to.set_range(spinmin, spinmax)

    def on_calculate_clicked(self, widget):
        dist_iter = self.combobox_prognosis_distance.get_active_iter()
        distunit = self.ls_dist_units.get(dist_iter, 1)[0]
        speed_iter = self.combobox_prognosis_speed.get_active_iter()
        speedunit = self.ls_speed_units.get(speed_iter, 1)[0]

        begin = self.spinbutton_prognosis_from.get_value_as_int()
        end = self.spinbutton_prognosis_to.get_value_as_int()
        distance = self.spinbutton_prognosis_distance.get_value()
        hours = self.spinbutton_prognosis_hours.get_value_as_int()
        minutes = self.spinbutton_prognosis_minutes.get_value_as_int()
        seconds = self.spinbutton_prognosis_seconds.get_value_as_int()
        seconds_total = (hours * 3600) + (minutes * 60) + seconds

        self.ls_velocity.clear()

        for speed in xrange(begin, end+50, 50):
            flight = int((distance*distunit) / (speed*speedunit))
            arrival = seconds_total + flight
            self.ls_velocity.insert(0, [speed,
                                        datetime.timedelta(seconds=flight),
                                        datetime.timedelta(seconds=arrival)])

        self.ls_velocity.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def on_printcalc_clicked(self, widget):
        data = [self.ls_velocity.get(row.iter, 0, 1, 2)
                for row in self.ls_velocity]
        if data:
            date = datetime.datetime.now()
            distance = "%s %s" %(
                        self.spinbutton_prognosis_distance.get_value_as_int(),
                        self.combobox_prognosis_distance.get_active_text())
            release = "%s:%s:%s" %(self.spinbutton_prognosis_hours.get_text(),
                                 self.spinbutton_prognosis_minutes.get_text(),
                                 self.spinbutton_prognosis_seconds.get_text())
            info = [date.strftime("%Y-%m-%d"), release, distance]
            printing.PrintVelocity(self.main.mainwindow, data, info,
                                   self.main.options, const.PRINT)

    # Data
    def on_cbdata_changed(self, widget):
        self.fill_item_combo(widget.get_active_text())

    def fill_item_combo(self, datatype):
        """
        Fill the item combobox with available items for the selected data
        """

        self.cbitems.get_model().clear()

        if datatype == _("Colours"):
            items = self.db.select_from_table(self.db.COLOURS)
        elif datatype == _("Sectors"):
            items = self.db.select_from_table(self.db.SECTORS)
        elif datatype == _("Types"):
            items = self.db.select_from_table(self.db.TYPES)
        elif datatype == _("Categories"):
            items = self.db.select_from_table(self.db.CATEGORIES)
        elif datatype == _("Racepoints"):
            items = self.db.select_from_table(self.db.RACEPOINTS)
        elif datatype == _("Strains"):
            items = self.db.select_from_table(self.db.STRAINS)
        elif datatype == _("Lofts"):
            items = self.db.select_from_table(self.db.LOFTS)
        elif datatype == _("Weather"):
            items = self.db.select_from_table(self.db.WEATHER)
        elif datatype == _("Wind"):
            items = self.db.select_from_table(self.db.WIND)

        if items:
            items.sort()

        for item in items:
            self.cbitems.append_text(item)

        if len(self.cbitems.get_model()) > 10:
            self.cbitems.set_wrap_width(2)

        self.cbitems.set_active(0)

        if self.cbitems.get_active_text():
            self.dataremove.set_sensitive(True)
        else:
            self.dataremove.set_sensitive(False)

    def on_dataremove_clicked(self, widget):
        dataset = self.cbdata.get_active_text()
        item = self.cbitems.get_active_text()

        d = dialogs.MessageDialog(const.QUESTION, messages.MSG_REMOVE_ITEM,
                                  self.toolsdialog,
                                  {'item': item, 'dataset': dataset})
        if d.yes:
            index = self.cbitems.get_active()

            if dataset == _("Colours"):
                self.db.delete_from_table(self.db.COLOURS, item)
            elif dataset == _("Sectors"):
                self.db.delete_from_table(self.db.SECTORS, item)
            elif dataset == _("Types"):
                self.db.delete_from_table(self.db.TYPES, item)
            elif dataset == _("Categories"):
                self.db.delete_from_table(self.db.CATEGORIES, item)
            elif dataset == _("Racepoints"):
                self.db.delete_from_table(self.db.RACEPOINTS, item)
            elif dataset == _("Strains"):
                self.db.delete_from_table(self.db.STRAINS, item)
            elif dataset == _("Lofts"):
                self.db.delete_from_table(self.db.LOFTS, item)
            elif dataset == _("Weather"):
                self.db.delete_from_table(self.db.WEATHER, item)
            elif dataset == _("Wind"):
                self.db.delete_from_table(self.db.WIND, item)

            self.cbitems.remove_text(index)
            self.cbitems.set_active(0)

    def on_dataadd_clicked(self, widget):
        datatype = self.cbdata2.get_active_text()
        item = (self.entryData.get_text(), )

        if datatype == _("Colours"):
            self.db.insert_into_table(self.db.COLOURS, item)
        elif datatype == _("Sectors"):
            self.db.insert_into_table(self.db.SECTORS, item)
        elif datatype == _("Types"):
            self.db.insert_into_table(self.db.TYPES, item)
        elif datatype == _("Categories"):
            self.db.insert_into_table(self.db.CATEGORIES, item)
        elif datatype == _("Racepoints"):
            self.db.insert_into_table(self.db.RACEPOINTS, item+("", "", ""))
        elif datatype == _("Strains"):
            self.db.insert_into_table(self.db.STRAINS, item)
        elif datatype == _("Lofts"):
            self.db.insert_into_table(self.db.LOFTS, item)
        elif datatype == _("Weather"):
            self.db.insert_into_table(self.db.WEATHER, item)
        elif datatype == _("Wind"):
            self.db.insert_into_table(self.db.WIND, item)

        self.entryData.set_text('')

        if datatype == self.cbdata.get_active_text():
            self.fill_item_combo(datatype)

    def on_entryData_changed(self, widget):
        if len(widget.get_text()) > 0:
            self.dataadd.set_sensitive(True)
        else:
            self.dataadd.set_sensitive(False)

    # Statistics
    def on_btnsearchdb_clicked(self, widget):
        total, cocks, hens, ybirds = \
                            common.count_active_pigeons(self.db)

        items = [(_("Number of pigeons"), total),
                 (_("Number of cocks"), "%s (%s %%)"
                                %(cocks, self.get_percentage(cocks, total))),
                 (_("Number of hens"), "%s (%s %%)"
                                %(hens, self.get_percentage(hens, total))),
                 (_("Number of young birds"), "%s (%s %%)"
                                %(ybirds, self.get_percentage(ybirds, total))),
                 (_("Number of results"),
                                    len(self.db.get_all_results()))
                ]

        self.ls_stats.clear()
        for description, value in items:
            self.ls_stats.insert(0, [description, value])

    def get_percentage(self, value, total):
        return "%.2f" %((value/float(total))*100)

    # Backup
    def on_makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            if backup.make_backup(folder):
                dialogs.MessageDialog(const.INFO, messages.MSG_BACKUP_SUCCES,
                                      self.main.mainwindow)
            else:
                dialogs.MessageDialog(const.INFO, messages.MSG_BACKUP_FAILED,
                                      self.main.mainwindow)

    def on_restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            if backup.restore_backup(zipfile):
                dialogs.MessageDialog(const.INFO, messages.MSG_RESTORE_SUCCES,
                                      self.main.mainwindow)
            else:
                dialogs.MessageDialog(const.INFO, messages.MSG_RESTORE_FAILED,
                                      self.main.mainwindow)

