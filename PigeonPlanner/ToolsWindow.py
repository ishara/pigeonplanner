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


import gtk
import gtk.glade

import Const


class ToolsWindow:
    def __init__(self, main):
        self.gladefile = Const.GLADEDIR + "ToolsWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_makebackup_clicked'    : self.makebackup_clicked,
                      'on_restorebackup_clicked' : self.restorebackup_clicked,
                      'on_window_destroy'        : self.close_clicked,
                      'on_close_clicked'         : self.close_clicked }
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        self.main = main

        self.toolsdialog.set_transient_for(self.main.main)

        # Build treeview
        self.liststore = gtk.ListStore(int, str)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Tools"), renderer, text=1)
        column.set_sort_column_id(0)
        self.treeview.set_model(self.liststore)
        self.treeview.append_column(column)

        self.selection = self.treeview.get_selection()
        self.selection.connect('changed', self.selection_changed)

        # Add the categories
        i = 0
        for category in [_("Backup")]:
            self.liststore.append([i, category])
            i += 1

        self.treeview.set_cursor(0)

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
        selected_id = model[path][0]

        try:
            self.notebook.set_current_page(selected_id)
        except TypeError:
            pass

    def makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            Backup.make_backup(folder)
            Dialog.messageDialog('info', Const.MSGBCKPOK, self.main)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            Backup.restore_backup(zipfile)
            Dialog.messageDialog('info', Const.MSGRESTOK, self.main)



