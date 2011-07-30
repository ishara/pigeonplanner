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

import const
import common
import builder


class VelocityCalculator(builder.GtkBuilder):
    def __init__(self, parent, database, options):
        builder.GtkBuilder.__init__(self, "VelocityCalculator.ui")

        self.parent = parent
        self.database = database
        self.options = options

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

        dt = datetime.datetime.now()
        self.spinbutton_prognosis_hours.set_value(dt.hour)
        self.spinbutton_prognosis_minutes.set_value(dt.minute)
        self.spinbutton_prognosis_seconds.set_value(dt.second)
        self.spinbutton_prognosis_from.set_value(800)
        self.spinbutton_prognosis_to.set_value(1800)

        self.velocitywindow.set_transient_for(parent)
        self.velocitywindow.show()

    # Callbacks
    def close_window(self, widget, event=None):
        self.velocitywindow.destroy()

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
            distance = "%s %s" % (
                        self.spinbutton_prognosis_distance.get_value_as_int(),
                        self.combobox_prognosis_distance.get_active_text())
            release = "%s:%s:%s" % (self.spinbutton_prognosis_hours.get_text(),
                                 self.spinbutton_prognosis_minutes.get_text(),
                                 self.spinbutton_prognosis_seconds.get_text())
            info = [date.strftime("%Y-%m-%d"), release, distance]
            import printing
            printing.PrintVelocity(self.parent, data, info,
                                   self.options, const.PRINT)

