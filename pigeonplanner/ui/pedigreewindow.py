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

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import builder
from pigeonplanner import printing
from pigeonplanner.ui import tools
from pigeonplanner.ui import maildialog
from pigeonplanner.ui.widgets import menus


class PedigreeWindow(builder.GtkBuilder):
    def __init__(self, parent, database, options, parser, pedigree, pigeon):
        builder.GtkBuilder.__init__(self, const.GLADEPEDIGREE)

        self.database = database
        self.options = options
        self.parser = parser
        self.pigeon = pigeon
        ring, year = pigeon.get_band()
        self.pdfname = "%s_%s_%s.pdf" %(_("Pedigree"), ring, year)
        self.build_toolbar()

        self.labelRing.set_text(pigeon.get_band_string(True))
        self.labelSex.set_text(pigeon.get_sex_string())
        self.labelName.set_text(pigeon.get_name())

        tableSire = gtk.Table(20, 7)
        self.alignSire.add(tableSire)
        tableDam = gtk.Table(20, 7)
        self.alignDam.add(tableDam)
        pedigree.draw_pedigree([tableSire, tableDam], pigeon, True)

        self.pedigreewindow.set_transient_for(parent)
        self.pedigreewindow.show()

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_pedigreewindow)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.pedigreewindow.add_accel_group(accelgroup)

        # Hide the Mail feature for now
        uimanager.get_widget('/Toolbar/Mail').hide()

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)

    def create_action_group(self):
        action_group = gtk.ActionGroup("PedigreeWindowActions")
        action_group.add_actions((
            ("Save", gtk.STOCK_SAVE, None, None,
                    _("Save this pedigree"), self.on_save_clicked),
            ("Mail", 'email', None, None,
                    _("Email this pedigree"), self.on_mail_clicked),
            ("Preview", gtk.STOCK_PRINT_PREVIEW, None, None,
                    _("View this pedigree"), self.on_preview_clicked),
            ("Print", gtk.STOCK_PRINT, None, None,
                    _("Print this pedigree"), self.on_print_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_dialog)
           ))

        return action_group

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

