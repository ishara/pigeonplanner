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

'''
A detailed pedigree of the selected pigeon.
'''


import os.path

import gtk

import const
import common
import widgets
import mailing
from pedigree import DrawPedigree
from printing import PrintPedigree
from gtkbuilderapp import GtkbuilderApp


class PedigreeWindow(GtkbuilderApp):
    def __init__(self, main, pigeoninfo):
        '''
        Constructor

        @param main: The main instance class
        @param pigeoninfo: Dictionary containing pigeon info
        '''

        GtkbuilderApp.__init__(self, const.GLADEPEDIGREE, const.DOMAIN)

        self.main = main
        self.pigeoninfo = pigeoninfo
        self.pindex = pigeoninfo['pindex']

        self.pedigreewindow.set_transient_for(self.main.main)

        self.build_toolbar()

        self.labelRing.set_text("%s / %s" %(self.pigeoninfo['ring'], self.pigeoninfo['year'][2:]))
        self.labelSex.set_text(self.pigeoninfo['sex'])
        self.labelName.set_text(self.pigeoninfo['name'])

        self.dp = DrawPedigree([self.tableSire, self.tableDam], self.pigeoninfo['pindex'],
                                True, self.main.parser.pigeons, self.main,
                                self, self.main.options.optionList.language)
        self.dp.draw_pedigree()

        self.pdfname = "%s_%s_%s.pdf" %(_("Pedigree"), pigeoninfo['ring'], pigeoninfo['year'])

        self.pedigreewindow.show()

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(widgets.pedigreeui)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.pedigreewindow.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)
        self.vbox.reorder_child(toolbar, 0)

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
        self.do_operation('mail')
        pedigree = os.path.join(const.TEMPDIR, self.pdfname)

        mailing.MailDialog(self.pedigreewindow, self.main.database, pedigree)

    def on_save_clicked(self, widget):
        self.do_operation('save')

    def on_preview_clicked(self, widget):
        self.do_operation('preview')

    def on_print_clicked(self, widget):
        self.do_operation('print')

    def do_operation(self, op):
        userinfo = common.get_own_address(self.main.database)

        if not common.check_userinfo(self.pedigreewindow, self.main, userinfo['name']): return

        PrintPedigree(self.pedigreewindow, self.pigeoninfo, userinfo, self.main.options.optionList, op, self.pdfname)

