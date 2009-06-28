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


import urllib
import datetime
import os.path

import gtk
import gtk.glade

import Const
import Backup
import Widgets
from Print import PrintVelocity


class ToolsWindow:
    def __init__(self, main):
        self.gladefile = Const.GLADEDIR + "ToolsWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_makebackup_clicked'    : self.makebackup_clicked,
                      'on_restorebackup_clicked' : self.restorebackup_clicked,
                      'on_sbbegin_changed'       : self.sbbegin_changed,
                      'on_calculate_clicked'     : self.calculate_clicked,
                      'on_printcalc_clicked'     : self.printcalc_clicked,
                      'on_calchelp_clicked'      : self.calchelp_clicked,
                      'on_btnupdate_clicked'     : self.btnupdate_clicked,
                      'on_window_destroy'        : self.close_clicked,
                      'on_close_clicked'         : self.close_clicked }
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        self.main = main

        self.toolsdialog.set_transient_for(self.main.main)
        self.linkbutton.set_uri(Const.DOWNLOADURL)

        # Build main treeview
        self.liststore = gtk.ListStore(int, str)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Tools"), renderer, text=1)
        self.treeview.set_model(self.liststore)
        self.treeview.append_column(column)

        self.selection = self.treeview.get_selection()
        self.selection.connect('changed', self.selection_changed)

        # Add the categories
        i = 0
        for category in [_("Backup"), _("Velocity calculator"), _("Update")]:
            self.liststore.append([i, category])
            i += 1

        self.treeview.set_cursor(0)

        # Build velocity treeview
        self.ls_velocity = gtk.ListStore(int, str, str)
        renderer = gtk.CellRendererText()
        column1 = gtk.TreeViewColumn(_("Velocity"), renderer, text=0)
        column2 = gtk.TreeViewColumn(_("Flight Time"), renderer, text=1)
        column3 = gtk.TreeViewColumn(_("Time of Arrival"), renderer, text=2)
        self.tv_velocity.set_model(self.ls_velocity)
        self.tv_velocity.append_column(column1)
        self.tv_velocity.append_column(column2)
        self.tv_velocity.append_column(column3)

        # Fill spinbuttons
        dt = datetime.datetime.now()
        self.sbhour.set_value(dt.hour)
        self.sbminute.set_value(dt.minute)
        self.sbdist.set_value(125) #XXX: Random?

        # Backups file filter
        fileFilter = gtk.FileFilter()
        fileFilter.set_name(_("PP Backups"))
        fileFilter.add_mime_type("zip/zip")
        fileFilter.add_pattern("*PigeonPlannerBackup.zip")
        self.fcButtonRestore.add_filter(fileFilter)

    def close_clicked(self, widget, event=None):
        self.toolsdialog.destroy()

    def selection_changed(self, selection):
        model, path = selection.get_selected()
        if not path:
            return

        try:
            self.notebook.set_current_page(model[path][0])
        except TypeError:
            pass

    def makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            Backup.make_backup(folder)
            Widgets.message_dialog('info', Const.MSGBCKPOK, self.main.main)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            Backup.restore_backup(zipfile)
            Widgets.message_dialog('info', Const.MSGRESTOK, self.main.main)

    def sbbegin_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]

        self.sbend.set_range(spinmin, spinmax)

    def calculate_clicked(self, widget):
        self.ls_velocity.clear()

        begin = self.sbbegin.get_value_as_int()
        end = self.sbend.get_value_as_int()
        velocity = begin

        releaseInMinutes = self.sbhour.get_value_as_int()*60 + self.sbminute.get_value_as_int()

        while velocity <= end:
            timeInMinutes = (self.sbdist.get_value_as_int()*1000)/velocity
            arrivalInMinutes = releaseInMinutes + timeInMinutes
            self.ls_velocity.append([velocity, datetime.timedelta(minutes=timeInMinutes), datetime.timedelta(minutes=arrivalInMinutes)])
            velocity += 50

    def printcalc_clicked(self, widget):
        data = []
        for row in self.ls_velocity:
            velocity, flight, arrival = self.ls_velocity.get(row.iter, 0, 1, 2)
            data.append((velocity, flight, arrival))

        if data:
            date = datetime.datetime.now()
            release = "%s:%s" %(self.sbhour.get_value_as_int(), self.sbminute.get_value_as_int())
            info = [date.strftime("%Y-%m-%d"), release, self.sbdist.get_value_as_int()]

            PrintVelocity(self.main.main, data, info)

    def calchelp_clicked(self, widget):
        pass

    def btnupdate_clicked(self, widget):
        local = os.path.join(Const.PREFDIR, Const.UPDATEURL.split('/')[-1])

        urllib.urlretrieve(Const.UPDATEURL, local)

        version = open(local, 'r').readline().strip()

        if Const.VERSION < version:
            msg = _("A new version is available. Please go to the Pigeon Planner website by clicking the link below and download the latest version")
            self.linkbutton.set_property('visible', True)
        elif Const.VERSION == version:
            msg = _("You already have the latest version installed.")
        elif Const.VERSION > version:
            msg = _("This isn't normal, or you must be running a development version")

        self.labelversion.set_text(msg)


