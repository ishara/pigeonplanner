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
import Print
import Widgets
import Options
from Pedigree import DrawPedigree


class PedigreeWindow:
    def __init__(self, main, ring, year, name, colour, sex):
        '''
        A detailed pedigree of the selected pigeon.

        @param main: The main window to set as parent
        @param ring: The selected pigeon
        @param year: Year of the pigeon
        @param name: Name of the pigeon
        @param colour: Colour of the pigeon
        @param sex: Sex of the pigeon
        ''' 

        self.gladefile = Const.GLADEDIR + "PedigreeWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_print_clicked'     : self.print_clicked,
                      'on_dialog_destroy'    : self.close_clicked,
                      'on_close_clicked'     : self.close_clicked }
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        self.main = main
        self.ring = ring
        self.year = year
        self.name = name
        self.colour = colour
        self.sex = sex

        self.options = Options.GetOptions()

        self.pedigreewindow.set_transient_for(self.main.main)

        self.labelRing.set_text(self.ring + '/' + self.year)
        self.labelName.set_text(self.name)

        dp = DrawPedigree([self.tableSire, self.tableDam], ring, True)
        dp.draw_pedigree()

    def close_clicked(self, widget, event=None):
        self.pedigreewindow.destroy()

    def print_clicked(self, widget):
        if self.options.optionList.name == '':
            answer = Widgets.message_dialog('question', Const.MSGNOINFO, self.pedigreewindow)
            if answer:
                self.pedigreewindow.destroy()
                Options.OptionsDialog(self.main, True)
                return

        Print.PrintPedigree(self.pedigreewindow, self.ring, self.year, self.sex, self.colour, self.name)


