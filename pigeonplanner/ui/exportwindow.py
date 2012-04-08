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


import os.path

import gtk

import builder
import filechooser
from export import get_exporters
from ui.messagedialog import ErrorDialog
from translation import gettext as _


class ExportWindow(builder.GtkBuilder):
    def __init__(self, parent, parser):
        builder.GtkBuilder.__init__(self, "ExportWindow.ui")

        self._parent = parent
        self.parser = parser

        for exporter in get_exporters():
            self.typelist.append([exporter, exporter.name])
        self.combotype.set_active(0)

        self.window.set_transient_for(parent)
        self.window.show_all()

    def on_window_delete_event(self, widget, event):
        self.window.destroy()
        return False

    def on_buttonclose_clicked(self, widget):
        self.window.destroy()
        return False

    def on_buttonexport_clicked(self, widget):
        filepath = self.entrypath.get_text()
        path = os.path.dirname(filepath)
        if not os.path.exists(path) or os.path.isdir(filepath):
            ErrorDialog((_('Invalid input!'), None, _('Error')), self.window)
            return
        self.imageprogress.hide()
        self.spinner.show()
        self.spinner.start()

        treeview = self._parent.get_treeview()
        if self.radioselected.get_active():
            pigeons = treeview.get_selected_pigeon()
            # pigeons can be a list of selected or just one pigeon object.
            if not isinstance(pigeons, list):
                pigeons = [pigeons]
        elif self.radiovisible.get_active():
            pigeons = treeview.get_pigeons(True)
        else:
            pigeons = self.parser.pigeons.values()
        exporter = self.__get_exporter()
        exporter.run(filepath, pigeons)

        self.spinner.hide()
        self.spinner.stop()
        self.imageprogress.show()

    def on_entrypath_changed(self, widget):
        value = widget.get_text_length() != 0
        self.buttonexport.set_sensitive(value)

    def on_entrypath_icon_press(self, widget, icon_pos, event):
        exporter = self.__get_exporter()
        dialog = filechooser.ExportChooser(self.window, exporter.extension,
                                                        exporter.filefilter)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            widget.set_text(dialog.get_filename())
        dialog.destroy()

    def __get_exporter(self):
        ls_iter = self.combotype.get_active_iter()
        return self.typelist.get(ls_iter, 0)[0]

