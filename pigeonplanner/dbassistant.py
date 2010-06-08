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

import gtk
import gtk.glade

import const
import backup


class DBAssistant:
    def __init__(self, db, version):
        self.wTree = gtk.glade.XML(const.GLADEASSIST)
        self.wTree.signal_autoconnect(self)

        for widget in self.wTree.get_widget_prefix(''):
            name = widget.get_name()
            setattr(self, name, widget)

        self.db = db
        self.version = version
        self.cancelled = False
        self.error = None

    def on_next_clicked(self, widget):
        page = self.notebook.get_current_page()

        if page == 0:
            self.notebook.set_current_page(1)
            self.next.hide()
            self.start.show()
        elif page == 1:
            if self.error:
                self.next.hide()
                self.close.show()
                self.notebook.set_current_page(3)
            else:
                self.next.hide()
                self.ok.show()
                self.notebook.set_current_page(2)

    def on_ok_clicked(self, widget):
        self.dbassistant.destroy()

        gtk.main_quit()

    def on_cancel_clicked(self, widget):
        self.cancelled = True

        self.dbassistant.destroy()

        gtk.main_quit()

    def on_close_clicked(self, widget):
        self.dbassistant.destroy()

        gtk.main_quit()

    def on_start_clicked(self, widget):
        self.set_busy_cursor(True)
        # Backup
        backup.make_backup(const.TEMPDIR)
        self.img1.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)

        while gtk.events_pending():
            gtk.main_iteration()

        # Database operations
        if self.version == 0: # 0.6.0 to 0.7.0
            success, exception = self.db_060_to_070()
            success, exception = self.db_070_to_090()
        elif self.version == 2: # 0.7.0 to 0.9.0
            success, exception = self.db_070_to_090()

        if success:
            self.img2.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        else:
            self.upgrade_failed(exception)
            return

        while gtk.events_pending():
            gtk.main_iteration()

        # Cleanup
        try:
            os.remove(os.path.join(const.TEMPDIR, 'PigeonPlannerBackup.zip'))
        except:
            pass
        self.db.optimize_db()
        self.img3.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)

        while gtk.events_pending():
            gtk.main_iteration()

        # Set completed
        self.img4.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        self.set_busy_cursor(False)

        self.cancel.hide()
        self.start.hide()
        self.next.show()

    def set_busy_cursor(self, value):
        if value:
            self.dbassistant.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.start.set_sensitive(False)
            self.cancel.set_sensitive(False)
        else:
            self.dbassistant.window.set_cursor(None)
            self.start.set_sensitive(True)
            self.cancel.set_sensitive(True)

        while gtk.events_pending():
            gtk.main_iteration()

    def upgrade_failed(self, exception):
        self.error = True

        self.img2.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON)

        while gtk.events_pending():
            gtk.main_iteration()

        self.set_busy_cursor(False)
        self.cancel.hide()
        self.start.hide()
        self.next.show()

        logfile = open(const.LOGFILE, "a")
        logfile.write("CRITICAL: %s" %exception)
        logfile.close()

        backup.restore_backup(os.path.join(const.TEMPDIR, 'PigeonPlannerBackup.zip'))

    def db_060_to_070(self):
        try:
            # Add new tables
            for table in ['Version', 'Weather', 'Wind', 'Sold', 'Lost', 'Dead', 'Types', 'Categories']:
                self.db.add_table_from_schema(table)

            # Add the database version
            self.db.insert_db_version(2)

            # Change the results table
            self.db.rename_table('Results', 'Results_tmp')
            self.db.add_table_from_schema('Results')
            self.db.copy_table2('Results_tmp', 'Results')
            self.db.drop_table('Results_tmp')

            # Change the racepoints table
            self.db.rename_table('Racepoints', 'Racepoints_tmp')
            self.db.add_table_from_schema('Racepoints')
            self.db.copy_table('Racepoints_tmp', 'Racepoints')
            self.db.drop_table('Racepoints_tmp')

            # Change the pigeons table
            self.db.rename_table('Pigeons', 'Pigeons_tmp')
            self.db.add_table_from_schema('Pigeons')
            self.db.copy_table('Pigeons_tmp', 'Pigeons')
            self.db.drop_table('Pigeons_tmp')
        except Exception, e:
            return False, e

        return True, None

    def db_070_to_090(self):
        try:
            # Add new tables
            for table in ['Medication']:
                self.db.add_table_from_schema(table)

            # Change database version
            self.db.change_db_version(3)
        except Exception, e:
            return False, e

        return True, None

