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
import os
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
                      'on_btnupdate_clicked'     : self.btnupdate_clicked,
                      'on_cbdata_changed'        : self.cbdata_changed,
                      'on_dataremove_clicked'    : self.dataremove_clicked,
                      'on_btnsearchdb_clicked'   : self.btnsearchdb_clicked,
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
        columns = [_("Tools")]
        types = [int, str]
        self.liststore, self.selection = Widgets.setup_treeview(self.treeview, columns, types, self.selection_changed, False, False, True)

        # Add the categories
        i = 0
        for category in [_("Velocity calculator"), _("Datasets"), _("Statistics"), _("Backup"), _("Update")]:
            self.liststore.append([i, category])
            i += 1

        self.treeview.set_cursor(0)

        # Build velocity treeview
        columns = [_("Velocity"), _("Flight Time"), _("Time of Arrival")]
        types = [int, str, str]
        self.ls_velocity, self.sel_velocity = Widgets.setup_treeview(self.tv_velocity, columns, types, None, False, False, False)

        # Build statistics treeview
        columns = ["Item", "Value"]
        types = [str, str]
        self.ls_stats, self.sel_stats = Widgets.setup_treeview(self.tvstats, columns, types, None, False, False, False)

        # Fill spinbuttons
        dt = datetime.datetime.now()
        self.sbhour.set_value(dt.hour)
        self.sbminute.set_value(dt.minute)
        self.sbdist.set_value(125)

        # Backups file filter
        fileFilter = gtk.FileFilter()
        fileFilter.set_name(_("PP Backups"))
        fileFilter.add_mime_type("zip/zip")
        fileFilter.add_pattern("*PigeonPlannerBackup.zip")
        self.fcButtonRestore.add_filter(fileFilter)

        # Fill the data combobox
        data = [_("Colours"), _("Racepoints"), _("Sectors"), _("Strains"), _("Lofts")]
        data.sort()
        for item in data:
            self.cbdata.append_text(item)
        self.cbdata.set_active(0)

    def close_clicked(self, widget, event=None):
        self.toolsdialog.destroy()

    def selection_changed(self, selection):
        model, path = selection.get_selected()
        if not path: return

        try:
            self.notebook.set_current_page(model[path][0])
        except TypeError:
            pass

    # Velocity
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

    # Data
    def cbdata_changed(self, widget):
        datatype = widget.get_active_text()
        self.fill_item_combo(datatype)

        if self.cbitems.get_active_text():
            self.dataremove.set_sensitive(True)
        else:
            self.dataremove.set_sensitive(False)

    def fill_item_combo(self, datatype):
        self.cbitems.get_model().clear()

        if datatype == _("Colours"):
            items = self.main.database.get_all_colours()
        elif datatype == _("Sectors"):
            items = self.main.database.get_all_sectors()
        elif datatype == _("Racepoints"):
            items = self.main.database.get_all_racepoints()
        elif datatype == _("Strains"):
            items = self.main.database.get_all_strains()
        elif datatype == _("Lofts"):
            items = self.main.database.get_all_lofts()

        if items:
            items.sort()

        for item in items:
            self.cbitems.append_text(item)

        self.cbitems.set_active(0)

    def dataremove_clicked(self, widget):
        dataset = self.cbdata.get_active_text()
        item = self.cbitems.get_active_text()

        remove = Widgets.message_dialog('question', Const.MSG_REMOVE_ITEM, self.toolsdialog, {'item': item, 'dataset': dataset})

        if remove:
            index = self.cbitems.get_active()

            if dataset == _("Colours"):
                self.main.database.delete_colour(item)
            elif dataset == _("Sectors"):
                self.main.database.delete_sector(item)
            elif dataset == _("Racepoints"):
                self.main.database.delete_racepoint(item)
            elif dataset == _("Strains"):
                self.main.database.delete_strain(item)
            elif dataset == _("Lofts"):
                self.main.database.delete_loft(item)

            self.cbitems.remove_text(index)
            self.cbitems.set_active(0)

    # Statistics
    def btnsearchdb_clicked(self, widget):
        items = {_("Number of pigeons"): self.main.database.get_pigeons(),
                 _("Number of results"): self.main.database.get_all_results()
                }

        self.ls_stats.clear()

        for item, value in items.iteritems():
            self.ls_stats.append([item, len(value)])

    # Backup
    def makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            Backup.make_backup(folder)
            Widgets.message_dialog('info', Const.MSG_BACKUP_SUCCES, self.main.main)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            Backup.restore_backup(zipfile)
            Widgets.message_dialog('info', Const.MSG_RESTORE_SUCCES, self.main.main)

    # Update
    def btnupdate_clicked(self, widget):
        local = os.path.join(Const.PREFDIR, Const.UPDATEURL.split('/')[-1])

        try:
            urllib.urlretrieve(Const.UPDATEURL, local)
            versionfile = open(local, 'r')
            version = versionfile.readline().strip()
            versionfile.close()
            os.remove(local)
        except IOError:
            version = None

        if not version:
            msg = Const.MSG_UPDATE_ERROR
        elif Const.VERSION < version:
            msg = Const.MSG_UPDATE_AVAILABLE
            self.linkbutton.set_property('visible', True)
        elif Const.VERSION == version:
            msg = Const.MSG_NO_UPDATE
        elif Const.VERSION > version:
            msg = Const.MSG_UPDATE_DEVELOPMENT

        self.labelversion.set_text(msg)
