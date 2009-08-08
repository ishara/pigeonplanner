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
import sys
import shutil

import gtk
import gtk.glade

import Const
import Widgets
import Configuration


class ParsedOptions:
    def __init__(self, theme, column, columntype, columnposition, arrows, toolbar, statusbar, update):
        self.theme = theme
        self.column = column
        self.columntype = columntype
        self.columnposition = columnposition
        self.arrows = arrows
        self.toolbar = toolbar
        self.statusbar = statusbar
        self.update = update


class GetOptions:
    def __init__(self):
        self.conf = Configuration.ConfigurationParser()

        self.optionList = []

        p = ParsedOptions(self.conf.getint('Options', 'theme'),
                          self.conf.getboolean('Options', 'column'),
                          self.conf.get('Options', 'columntype'),
                          self.conf.getint('Options', 'columnposition'),
                          self.conf.getboolean('Options', 'arrows'),
                          self.conf.getboolean('Options', 'toolbar'),
                          self.conf.getboolean('Options', 'statusbar'),
                          self.conf.getboolean('Options', 'update'))

        self.optionList = p

    def write_default(self):
        '''
        Write the default configuration file
        '''

        self.conf.generateDefaultFile()
        self.conf.copyNew(default=True)

    def write_options(self, dic):
        '''
        Write the options to the configuration file

        @param dic: a dictionary of options ({section : {key : value}}) 
        '''

        self.conf.generateNewFile(dic)
        self.conf.copyNew(new=True)

    def set_option(self, section, option, value):
        '''
        Set a single option to the configuration file

        @param section: The section of the option
        @param option: The option to change
        @param value: The value for the option
        '''

        self.conf.set_option(section, option, value)


class OptionsDialog:
    def __init__(self, main):

        self.gladefile = Const.GLADEDIR + "OptionsDialog.glade"
        self.wTree = gtk.glade.XML(self.gladefile)

        signalDic = { 'on_chkColumn_toggled'     : self.chkColumn_toggled,
                      'on_columnOpt_changed'     : self.columnOpt_changed,
                      'on_cancel_clicked'        : self.cancel_clicked,
                      'on_ok_clicked'            : self.ok_clicked,
                      'on_default_clicked'       : self.default_clicked,
                      'on_dialog_destroy'        : self.close_clicked}
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            setattr(self, name, w)

        self.main = main

        self.optionsdialog.set_transient_for(self.main.main)

        self.opt = GetOptions()

        self.create_columntype_combo()

        # Show the theme changer on Windows
        self.win32 = sys.platform.startswith("win")
        if self.win32:
            self.hboxThemes.show()

            themes = os.listdir('./share/themes/')
            themes.sort()
            for theme in themes:
                self.cbThemes.append_text(theme)

            number = len(self.cbThemes.get_model())
            if number > 10 and number <= 30:
                self.cbThemes.set_wrap_width(2)
            elif number > 30:
                self.cbThemes.set_wrap_width(3)

        self.set_options()
        if not self.chkColumn.get_active():
            self.aligncolumn.set_sensitive(False)

        self.treeviewOptsChanged = False

    def create_columntype_combo(self):
        self.typeStore = gtk.ListStore(str, str)
        for key in self.main.columnValueDic.keys():
            self.typeStore.insert(int(key), [key, self.main.columnValueDic[key]])
        self.cbColumn = gtk.ComboBox(self.typeStore)
        cell = gtk.CellRendererText()
        self.cbColumn.pack_start(cell, True)
        self.cbColumn.add_attribute(cell, 'text', 1)
        self.cbColumn.show()

        self.cbColumn.connect('changed', self.columnOpt_changed)

        self.aligntype.add(self.cbColumn)

    def set_options(self):
        self.cbThemes.set_active(self.opt.optionList.theme)

        self.chkColumn.set_active(self.opt.optionList.column)

        self.cbColumn.set_active(int(self.opt.optionList.columntype))
        self.sbColumn.set_value(self.opt.optionList.columnposition)

        self.chkArrows.set_active(self.opt.optionList.arrows)
        self.chkToolbar.set_active(self.opt.optionList.toolbar)
        self.chkStatusbar.set_active(self.opt.optionList.statusbar)
        self.chkUpdate.set_active(self.opt.optionList.update)

        self.treeviewOptsChanged = False

    def columnOpt_changed(self, widget):
        self.treeviewOptsChanged = True

    def chkColumn_toggled(self, widget):
        self.treeviewOptsChanged = True

        if widget.get_active():
            self.aligncolumn.set_sensitive(True)
        else:
            self.aligncolumn.set_sensitive(False)

    def close_clicked(self, widget, event=None):
        self.optionsdialog.destroy()

    def cancel_clicked(self, widget):
        self.optionsdialog.destroy()

    def default_clicked(self, widget):
        answer = Widgets.message_dialog('warning', Const.MSG_DEFAULT_OPTIONS, self.optionsdialog)
        if answer:
            self.opt.write_default()
            self.opt = GetOptions()
            self.set_options()

    def ok_clicked(self, widget):
        dic = {"Options" : {'theme': self.cbThemes.get_active(),
                            'column': str(self.chkColumn.get_active()),
                            'columntype': self.cbColumn.get_active_text(),
                            'columnposition': self.sbColumn.get_value_as_int(),
                            'arrows': str(self.chkArrows.get_active()),
                            'toolbar': str(self.chkToolbar.get_active()),
                            'statusbar': str(self.chkStatusbar.get_active()),
                            'update': str(self.chkUpdate.get_active())
                           }
              }

        self.opt.write_options(dic)

        self.main.options = GetOptions()

        if self.win32 and self.cbThemes.get_active() != self.opt.optionList.theme:
            shutil.copy(os.path.join('./share/themes', self.cbThemes.get_active_text(), 'gtk-2.0/gtkrc'),
                                     './etc/gtk-2.0/')

            gtk.rc_parse('./etc/gtk-2.0/')
            screen = self.main.main.get_screen()
            settings = gtk.settings_get_for_screen(screen)
            gtk.rc_reparse_all_for_settings(settings, True)

        if self.treeviewOptsChanged:
            self.main.build_treeview()
            self.main.fill_treeview()

        if self.chkArrows.get_active():
            self.main.alignarrows.show()

            self.main.blockMenuCallback = True
            self.main.MenuArrows.set_active(True)
            self.main.blockMenuCallback = False
        else:
            self.main.alignarrows.hide()

            self.main.blockMenuCallback = True
            self.main.MenuArrows.set_active(False)
            self.main.blockMenuCallback = False

        if self.chkToolbar.get_active():
            self.main.toolbar.show()

            self.main.blockMenuCallback = True
            self.main.MenuToolbar.set_active(True)
            self.main.blockMenuCallback = False
        else:
            self.main.toolbar.hide()

            self.main.blockMenuCallback = True
            self.main.MenuToolbar.set_active(False)
            self.main.blockMenuCallback = False

        if self.chkStatusbar.get_active():
            self.main.statusbar.show()

            self.main.blockMenuCallback = True
            self.main.MenuStatusbar.set_active(True)
            self.main.blockMenuCallback = False
        else:
            self.main.statusbar.hide()

            self.main.blockMenuCallback = True
            self.main.MenuStatusbar.set_active(False)
            self.main.blockMenuCallback = False

        self.optionsdialog.destroy()

