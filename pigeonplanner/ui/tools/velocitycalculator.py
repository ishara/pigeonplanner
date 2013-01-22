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


import datetime

import gtk

import common
import builder
from reportlib import report
from reports.velocity import VelocityReport, VelocityReportOptions


class VelocityCalculator(builder.GtkBuilder):
    def __init__(self, parent, database):
        builder.GtkBuilder.__init__(self, "VelocityCalculator.ui")

        self.parent = parent
        self.database = database

        dt = datetime.datetime.now()
        self.widgets.spinbutton_prognosis_hours.set_value(dt.hour)
        self.widgets.spinbutton_prognosis_minutes.set_value(dt.minute)
        self.widgets.spinbutton_prognosis_seconds.set_value(dt.second)
        self.widgets.spinbutton_prognosis_from.set_value(800)
        self.widgets.spinbutton_prognosis_to.set_value(1800)

        self.widgets.velocitywindow.set_transient_for(parent)
        self.widgets.velocitywindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.widgets.velocitywindow.destroy()

    def on_buttonhelp_clicked(self, widget):
        common.open_help(11)

    def on_spinbutton_time_changed(self, widget):
        value = widget.get_value_as_int()
        widget.set_text(common.add_zero_to_time(value))

    ## Exact
    def on_button_velocity_calculate_clicked(self, widget):
        distunit = self.widgets.combobox_velocity_distance.get_unit()
        speedunit = self.widgets.combobox_velocity_speed.get_unit()

        distance = self.widgets.spinbutton_velocity_distance.get_value()
        hours = self.widgets.spinbutton_velocity_hours.get_value_as_int()
        minutes = self.widgets.spinbutton_velocity_minutes.get_value_as_int()
        seconds = self.widgets.spinbutton_velocity_seconds.get_value_as_int()
        seconds_total = (hours * 3600) + (minutes * 60) + seconds
        if seconds_total == 0:
            self.widgets.spinbutton_velocity_seconds.set_value(1)
            seconds_total = 1

        speed = (distance * distunit) / (seconds_total * speedunit)
        self.widgets.entry_velocity_result.set_text("%.6f" %speed)

    ## Prognosis
    def on_spinbutton_prognosis_from_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]
        self.widgets.spinbutton_prognosis_to.set_range(spinmin, spinmax)

    def on_calculate_clicked(self, widget):
        distunit = self.widgets.combobox_prognosis_distance.get_unit()
        speedunit = self.widgets.combobox_prognosis_speed.get_unit()

        begin = self.widgets.spinbutton_prognosis_from.get_value_as_int()
        end = self.widgets.spinbutton_prognosis_to.get_value_as_int()
        distance = self.widgets.spinbutton_prognosis_distance.get_value()
        hours = self.widgets.spinbutton_prognosis_hours.get_value_as_int()
        minutes = self.widgets.spinbutton_prognosis_minutes.get_value_as_int()
        seconds = self.widgets.spinbutton_prognosis_seconds.get_value_as_int()
        seconds_total = (hours * 3600) + (minutes * 60) + seconds

        self.widgets.ls_velocity.clear()
        for speed in xrange(begin, end+50, 50):
            flight = int((distance*distunit) / (speed*speedunit))
            arrival = seconds_total + flight
            self.widgets.ls_velocity.insert(0, [speed,
                                        datetime.timedelta(seconds=flight),
                                        datetime.timedelta(seconds=arrival)])
        self.widgets.ls_velocity.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def on_printcalc_clicked(self, widget):
        data = [self.widgets.ls_velocity.get(row.iter, 0, 1, 2)
                for row in self.widgets.ls_velocity]
        if data:
            date = datetime.datetime.now()
            distance = "%s %s" % (
                        self.widgets.spinbutton_prognosis_distance.get_value_as_int(),
                        self.widgets.combobox_prognosis_distance.get_active_text())
            release = "%s:%s:%s" % (self.widgets.spinbutton_prognosis_hours.get_text(),
                                 self.widgets.spinbutton_prognosis_minutes.get_text(),
                                 self.widgets.spinbutton_prognosis_seconds.get_text())
            info = [date.strftime("%Y-%m-%d"), release, distance]

            psize = common.get_pagesize_from_opts()
            reportopts = VelocityReportOptions(psize)
            report(VelocityReport, reportopts, data, info)

