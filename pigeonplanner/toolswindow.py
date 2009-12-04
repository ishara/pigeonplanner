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
import datetime
import logging
logger = logging.getLogger(__name__)

import gobject
import gtk
import gtk.glade

import const
import update
import backup
import widgets
import messages
from printing import PrintVelocity


class ToolsWindow:
    def __init__(self, main):
        self.wTree = gtk.glade.XML(const.GLADETOOLS)
        self.wTree.signal_autoconnect(self)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        self.main = main

        self.toolsdialog.set_transient_for(self.main.main)
        self.linkbutton.set_uri(const.DOWNLOADURL)

        # Build main treeview
        columns = [_("Tools")]
        types = [int, str]
        self.liststore, self.selection = widgets.setup_treeview(self.treeview, columns, types, self.selection_changed, False, False, True)

        # Add the categories
        i = 0
        for category in [_("Velocity calculator"), _("Datasets"), _("Addresses"), _("Statistics"), _("Database"), _("Backup"), _("Update")]:
            self.liststore.append([i, category])
            i += 1

        self.treeview.set_cursor(0)

        # Build velocity treeview
        columns = [_("Velocity"), _("Flight Time"), _("Time of Arrival")]
        types = [int, str, str]
        self.ls_velocity, self.sel_velocity = widgets.setup_treeview(self.tv_velocity, columns, types, None, False, False, False)

        # Build addresses treeview
        columns = [_("Name")]
        types = [str]
        self.ls_address, self.sel_address = widgets.setup_treeview(self.tvaddress,
                                                                   columns, types,
                                                                   self.adselection_changed,
                                                                   True, True, False)

        # Fill address treeview
        self.fill_address_view()

        # Build statistics treeview
        columns = ["Item", "Value"]
        types = [str, str]
        self.ls_stats, self.sel_stats = widgets.setup_treeview(self.tvstats, columns, types, None, False, False, False)

        # Fill spinbuttons
        dt = datetime.datetime.now()
        self.sbhour.set_value(dt.hour)
        self.sbminute.set_value(dt.minute)

        # Backups file filter
        self.fcButtonRestore.add_filter(widgets.backupFileFilter)

        # Fill the data combobox
        data = [_("Colours"), _("Racepoints"), _("Sectors"), _("Strains"), _("Lofts")]
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
    def on_sbbegin_changed(self, widget):
        spinmin = widget.get_value_as_int()
        spinmax = widget.get_range()[1]

        self.sbend.set_range(spinmin, spinmax)

    def on_sbminute_changed(self, widget):
        value = widget.get_value_as_int()

        if value >= 0 and value < 10:
            widget.set_text('0%s' %value)

    def on_calculate_clicked(self, widget):
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

    def on_printcalc_clicked(self, widget):
        data = []
        for row in self.ls_velocity:
            velocity, flight, arrival = self.ls_velocity.get(row.iter, 0, 1, 2)
            data.append((velocity, flight, arrival))

        if data:
            date = datetime.datetime.now()
            release = "%s:%s" %(self.sbhour.get_text(), self.sbminute.get_text())
            info = [date.strftime("%Y-%m-%d"), release, self.sbdist.get_value_as_int()]

            PrintVelocity(self.main.main, data, info)

    # Data
    def on_cbdata_changed(self, widget):
        datatype = widget.get_active_text()
        self.fill_item_combo(datatype)

    def fill_item_combo(self, datatype):
        '''
        Fill the item combobox with available items for the selected data
        '''

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

        if widgets.message_dialog('question', messages.MSG_REMOVE_ITEM, self.toolsdialog, (item, dataset)):
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

    def on_dataadd_clicked(self, widget):
        datatype = self.cbdata2.get_active_text()
        item = (self.entryData.get_text(), )

        if datatype == _("Colours"):
            self.main.database.insert_colour(item)
        elif datatype == _("Sectors"):
            self.main.database.insert_sector(item)
        elif datatype == _("Racepoints"):
            self.main.database.insert_racepoint(item)
        elif datatype == _("Strains"):
            self.main.database.insert_strain(item)
        elif datatype == _("Lofts"):
            self.main.database.insert_loft(item)

        self.entryData.set_text('')

        if datatype == self.cbdata.get_active_text():
            self.fill_item_combo(datatype)

    def on_entryData_changed(self, widget):
        if len(widget.get_text()) > 0:
            self.dataadd.set_sensitive(True)
        else:
            self.dataadd.set_sensitive(False)

    # Addresses
    def fill_address_view(self):
        '''
        Fill the treeview with available addresses
        ''' 

        self.ls_address.clear()

        for item in self.main.database.get_all_addresses():
            self.ls_address.append([item[1]])

        self.ls_address.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def adselection_changed(self, selection):
        model, path = selection.get_selected()

        self.empty_adentrys()

        if path:
            widgets.set_multiple_sensitive({self.adremove: True, self.adedit: True})
        else:
            widgets.set_multiple_sensitive({self.adremove: False, self.adedit: False})
            return

        self.set_data()

    def set_data(self):
        model, path = self.sel_address.get_selected()

        name = model[path][0]

        data = self.main.database.get_address(name)

        self.adentryname.set_text(name)
        self.adentrystreet.set_text(data[2])
        self.adentryzip.set_text(data[3])
        self.adentrycity.set_text(data[4])
        self.adentrycountry.set_text(data[5])
        self.adentryphone.set_text(data[6])
        self.adentrymail.set_text(data[7])
        self.adentrycomment.set_text(data[8])

    def on_adadd_clicked(self, widget, pedigree_call=False):
        self.pedigree_call = pedigree_call

        self.admode = 'add'

        self.start_add()

    def on_adedit_clicked(self, widget):
        self.pedigree_call = False

        self.admode = 'edit'

        self.start_add()

    def on_btnadd_clicked(self, widget):
        data = self.get_entry_data()

        if not data[0]:
            widgets.message_dialog('error', messages.MSG_NAME_EMPTY, self.toolsdialog)
            return

        if self.admode == 'add':
            for ad in self.main.database.get_all_addresses():
                if data[0] == ad[1]:
                    widgets.message_dialog('error', messages.MSG_NAME_EXISTS, self.toolsdialog)
                    return

            self.main.database.insert_address(data)
        else:
            data += (self.get_name(), )
            self.main.database.update_address(data)

        self.fill_address_view()

        self.finish_add()

    def on_btncancel_clicked(self, widget):
        self.finish_add()

    def start_add(self):
        for entry in self.get_entrys():
            entry.set_property('editable', True)

        widgets.set_multiple_sensitive({self.treeview: False, self.vboxtv: False})

        alreadyMe = False
        for item in self.main.database.get_all_addresses():
            if item[9]:
                alreadyMe = True
                self.me = item[1]
                break

        if alreadyMe:
            widgets.set_multiple_visible({self.btnadd: True, self.btncancel: True})
            if self.admode == 'edit' and self.me == self.get_name():
                widgets.set_multiple_visible({self.chkme: True})
                self.chkme.set_active(True)
        else:
            widgets.set_multiple_visible({self.btnadd: True, self.btncancel: True, self.chkme: True})

        self.adentryname.grab_focus()

    def finish_add(self):
        self.empty_adentrys()

        for entry in self.get_entrys():
            entry.set_property('editable', False)

        self.chkme.set_active(False)

        widgets.set_multiple_visible({self.btnadd: False, self.btncancel: False, self.chkme: False})
        widgets.set_multiple_sensitive({self.treeview: True, self.vboxtv: True})

        if self.pedigree_call:
            self.toolsdialog.destroy()

    def on_adremove_clicked(self, widget):
        if not widgets.message_dialog('warning', messages.MSG_REMOVE_ADDRESS, self.toolsdialog, self.get_name()):
            return

        self.main.database.delete_address(self.get_name())

        model, path = self.sel_address.get_selected()
        self.ls_address.remove(path)

        if len(self.ls_address) > 0:
            self.tvaddress.set_cursor((0,))

    def get_name(self):
        '''
        Return the name of the selected person
        '''

        model, path = self.sel_address.get_selected()
        if not path:
            return None
        else:
            return model[path][0]

    def get_entry_data(self):
        '''
        Return the text of all the entry's
        '''

        return (self.adentryname.get_text(),\
                self.adentrystreet.get_text(),\
                self.adentryzip.get_text(),\
                self.adentrycity.get_text(),\
                self.adentrycountry.get_text(),\
                self.adentryphone.get_text(),\
                self.adentrymail.get_text(),\
                self.adentrycomment.get_text(),\
                int(self.chkme.get_active()))

    def get_entrys(self):
        '''
        Return all entry's
        '''

        entrys = []
        for widget in self.wTree.get_widget_prefix("adentry"):
            entrys.append(getattr(self, widget.get_name()))

        return entrys

    def empty_adentrys(self):
        '''
        Clear all entry's
        '''

        for entry in self.get_entrys():
            entry.set_text('')

    # Statistics
    def on_btnsearchdb_clicked(self, widget):
        cocks = 0
        hens = 0
        ybirds = 0
        ptotal = 0
        for pigeon in self.main.database.get_pigeons():
            if not pigeon[5]: continue # Pigeon is not shown, don't count it

            ptotal += 1

            if pigeon[4] == '0':
                cocks += 1
            elif pigeon[4] == '1':
                hens += 1
            elif pigeon[4] == '2':
                ybirds += 1

        items = {_("Number of pigeons"): ptotal,
                 _("Number of cocks"): cocks,
                 _("Number of hens"): hens,
                 _("Number of young birds"): ybirds,
                 _("Number of results"): len(self.main.database.get_all_results())
                }

        self.ls_stats.clear()

        for item in sorted(items, key=items.__getitem__):
            self.ls_stats.append([item, items[item]])

    # Database
    def on_dboptimize_clicked(self, widget):
        self.toolsdialog.set_sensitive(False)
        self.main.database.optimize_db()
        self.toolsdialog.set_sensitive(True)
        widgets.message_dialog('info', messages.MSG_OPTIMIZE_FINISH, self.toolsdialog)

    def on_dbremove_clicked(self, widget):
        if widgets.message_dialog('warning', messages.MSG_REMOVE_DATABASE, self.toolsdialog):
            logger.debug("Start deleting the database")
            try:
                os.remove(const.DATABASE)
            except Exception, msg:
                logger.error("Deleting database: %s" % msg)
            else:
                widgets.message_dialog('info', messages.MSG_RMDB_FINISH, self.toolsdialog)
                self.close_clicked()
                self.main.quit_program(bckp=False)

    # Backup
    def on_makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            if backup.make_backup(folder):
                widgets.message_dialog('info', messages.MSG_BACKUP_SUCCES, self.main.main)
            else:
                widgets.message_dialog('info', messages.MSG_BACKUP_FAILED, self.main.main)

    def on_restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            if backup.restore_backup(zipfile):
                widgets.message_dialog('info', messages.MSG_RESTORE_SUCCES, self.main.main)
            else:
                widgets.message_dialog('info', messages.MSG_RESTORE_FAILED, self.main.main)

    # Update
    def on_btnupdate_clicked(self, widget):
        gobject.idle_add(self.update_check)

    def update_check(self):
        msg, new = update.update()

        self.labelversion.set_text(msg)

        if new:
            self.linkbutton.set_property('visible', True)

