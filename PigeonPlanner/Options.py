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
import Widgets
import Configuration


class ParsedOptions:
    def __init__(self, column, columntype, columnposition, arrows, name, street, code, city, tel):
        self.column = column
        self.columntype = columntype
        self.columnposition = columnposition
        self.arrows = arrows
        self.name = name
        self.street = street
        self.code = code
        self.city = city
        self.tel = tel


class GetOptions:
    def __init__(self):
        self.conf = Configuration.ConfigurationParser()

        self.optionList = []

        p = ParsedOptions(self.conf.getboolean('Options', 'column'),
                          self.conf.get('Options', 'columntype'),
                          self.conf.getint('Options', 'columnposition'),
                          self.conf.getboolean('Options', 'arrows'),
                          self.conf.get('personal', 'name'),
                          self.conf.get('personal', 'street'),
                          self.conf.get('personal', 'code'),
                          self.conf.get('personal', 'city'),
                          self.conf.get('personal', 'tel'))

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


class OptionsDialog:
    def __init__(self, main, personal=False):

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

        self.columnValueDic = {_("Colour") : 0, _("Sex") : 1}

        for item in sorted(self.columnValueDic, key=self.columnValueDic.__getitem__):
            self.cbColumn.get_model().append([item])

        self.set_options()
        if not self.chkColumn.get_active():
            self.aligncolumn.set_sensitive(False)

        self.treeviewOptsChanged = False

        if personal:
            self.notebook.get_nth_page(0).set_sensitive(0)
            self.notebook.set_current_page(1)

    def set_options(self):
        self.chkColumn.set_active(self.opt.optionList.column)

        self.cbColumn.set_active(self.columnValueDic[_(self.opt.optionList.columntype)])
        self.sbColumn.set_value(self.opt.optionList.columnposition)

        self.chkArrows.set_active(self.opt.optionList.arrows)

        self.entryName.set_text(self.opt.optionList.name),
        self.entryStreet.set_text(self.opt.optionList.street),
        self.entryCode.set_text(self.opt.optionList.code),
        self.entryCity.set_text(self.opt.optionList.city),
        self.entryTel.set_text(self.opt.optionList.tel),

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
        answer = Widgets.message_dialog('warning', Const.MSGDEFAULT, self.optionsdialog)
        if answer:
            self.opt.write_default()
            self.opt = GetOptions()
            self.set_options()
#            self.treeviewOptsChanged = True

    def ok_clicked(self, widget):
        dic = {"Options" : {'column' : str(self.chkColumn.get_active()),
                            'columntype' : self.cbColumn.get_active_text(),
                            'columnposition' : self.sbColumn.get_value_as_int(),
                            'arrows' : str(self.chkArrows.get_active())
                           },
               "personal" : {'name' : self.entryName.get_text(),
                             'street' : self.entryStreet.get_text(),
                             'code' : self.entryCode.get_text(),
                             'city' : self.entryCity.get_text(),
                             'tel' : self.entryTel.get_text(),
                            }
              }

        self.opt.write_options(dic)

        self.main.options = GetOptions()
        if self.treeviewOptsChanged:
            self.main.build_treeview()
            self.main.fill_treeview()

        if self.chkArrows.get_active():
            self.main.alignarrows.show()
        else:
            self.main.alignarrows.hide()

        self.optionsdialog.destroy()

