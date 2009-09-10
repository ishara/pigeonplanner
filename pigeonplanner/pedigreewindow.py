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


import gtk
import gtk.glade

import const
import widgets
from pedigree import DrawPedigree
from printing import PrintPedigree
from toolswindow import ToolsWindow


class PedigreeWindow:
    def __init__(self, main, pigeoninfo):
        '''
        Constructor

        @param main: The main instance class
        @param pigeoninfo: Dictionary containing pigeon info
        ''' 

        self.wTree = gtk.glade.XML(const.GLADEPEDIGREE)

        signalDic = { 'on_print_clicked'     : self.print_clicked,
                      'on_dialog_destroy'    : self.close_clicked,
                      'on_close_clicked'     : self.close_clicked }
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        self.main = main
        self.pigeoninfo = pigeoninfo
        self.pindex = pigeoninfo['pindex']
        self.ring = pigeoninfo['ring']
        self.year = pigeoninfo['year']
        self.sex = pigeoninfo['sex']
        self.colour = pigeoninfo['colour']
        self.name = pigeoninfo['name']

        self.pedigreewindow.set_transient_for(self.main.main)

        self.labelRing.set_text("%s / %s" %(self.ring, self.year[2:]))
        self.labelSex.set_text(self.sex)
        self.labelName.set_text(self.name)

        self.dp = DrawPedigree([self.tableSire, self.tableDam], self.pindex,
                                True, None,
                                self.main.parser.pigeons, self.main, self)
        self.dp.draw_pedigree()

    def close_clicked(self, widget=None, event=None):
        self.pedigreewindow.destroy()

    def print_clicked(self, widget):
        userinfo = {'name': '', 'street': '', 'code': '', 'city': '', 'phone': ''}

        for address in self.main.database.get_all_addresses():
            if address[9]:
                userinfo['name'] = address[1]
                userinfo['street'] = address[2]
                userinfo['code'] = address[3]
                userinfo['city'] = address[4]
                userinfo['phone'] = address[6]

                break

        if not userinfo['name']:
            if widgets.message_dialog('question', const.MSG_NO_INFO, self.pedigreewindow):
                tw = ToolsWindow(self.main)
                tw.toolsdialog.set_keep_above(True)
                tw.treeview.set_cursor(2)
                tw.adadd_clicked(None, pedigree_call=True)
                tw.chkme.set_active(True)

                return

        PrintPedigree(self.pedigreewindow, self.pigeoninfo, userinfo)

