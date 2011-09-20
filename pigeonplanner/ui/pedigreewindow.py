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
A detailed pedigree of the selected pigeon.
"""


import os.path

import gtk

import const
import common
import builder
import printing
from ui import tools
from ui import maildialog
from ui.widgets import menus
from translation import gettext as _


class PedigreeWindow(builder.GtkBuilder):
    def __init__(self, parent, database, options, parser, pedigree, pigeon):
        builder.GtkBuilder.__init__(self, "PedigreeWindow.ui")

        self.database = database
        self.options = options
        self.parser = parser
        self.pigeon = pigeon
        ring, year = pigeon.get_band()
        self.pdfname = "%s_%s_%s.pdf" % (_("Pedigree"), ring, year)
        self.build_toolbar()

        tableSire = gtk.Table(20, 7)
        self.alignSire.add(tableSire)
        tableDam = gtk.Table(20, 7)
        self.alignDam.add(tableDam)
        pedigree.draw_pedigree([tableSire, tableDam], pigeon, True)

        name = pigeon.get_name()
        if name:
            name = ", " + name
        title = "%s: %s%s - %s" % (_("Pedigree"), pigeon.get_band_string(True),
                                   name, pigeon.get_sex_string())
        self.pedigreewindow.set_title(title)
        self.pedigreewindow.set_transient_for(parent)
        self.pedigreewindow.show()

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_pedigreewindow)
        uimanager.insert_action_group(self.actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.pedigreewindow.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)

    def on_close_dialog(self, widget=None, event=None):
        self.pedigreewindow.destroy()

    def on_mail_clicked(self, widget):
        self.do_operation(const.MAIL)
        pedigree = os.path.join(const.TEMPDIR, self.pdfname)

        maildialog.MailDialog(self.pedigreewindow,
                              self.database, pedigree)

    def on_save_clicked(self, widget):
        self.do_operation(const.SAVE)

    def on_preview_clicked(self, widget):
        self.do_operation(const.PREVIEW)

    def on_print_clicked(self, widget):
        self.do_operation(const.PRINT)

    def do_operation(self, op):
        userinfo = common.get_own_address(self.database)
        if not tools.check_user_info(self.pedigreewindow,
                                     self.database, userinfo['name']):
            return

        printing.PrintPedigree(self.pedigreewindow, self.pigeon, userinfo,
                               self.options, op, self.pdfname, self.parser)

