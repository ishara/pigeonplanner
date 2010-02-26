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
import widgets
import options
import messages


class OptionsDialog:
    def __init__(self, main):
        self.wTree = gtk.glade.XML(const.GLADEOPTIONS)
        self.wTree.signal_autoconnect(self)

        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            setattr(self, name, w)

        self.main = main

        self.optionsdialog.set_transient_for(self.main.main)

        self.opt = options.GetOptions()

        # Show the theme changer on Windows
        if const.WINDOWS:
            self.framethemes.show()

            themes = os.listdir('./share/themes/')
            themes.sort()
            for theme in themes:
                self.cbThemes.append_text(theme)

            number = len(self.cbThemes.get_model())
            if number > 10 and number <= 30:
                self.cbThemes.set_wrap_width(2)
            elif number > 30:
                self.cbThemes.set_wrap_width(3)

            # Page setup icon is available since PyGTK 2.14
            # We only use 2.12 on Windows (missing binaries)
            self.imagePage.set_from_file(os.path.join(const.IMAGEDIR, 'gtk_pagesetup.png'))

        # Fill language combobox with available languages
        self.languagelookup = [
                ('Default', 'def'),
                ('Arabic', 'ar'),
                ('Bosnian', 'bs'),
                ('Dutch', 'nl'),
                ('English', 'en'),
                ('Russian', 'ru'),
                ('Spanish', 'es')
                ]
        for name, code in self.languagelookup:
            self.cbLang.append_text(name)

        self.set_options()

        # Set the default button as secondary. This option is broken in Glade.
        self.action_area.set_child_secondary(self.default, True)

        self.optionsdialog.show()

    def set_options(self):
        # General
        self.chkUpdate.set_active(self.opt.optionList.update)

        for i in xrange(0, len(self.languagelookup)):
            name, code = self.languagelookup[i]
            if self.opt.optionList.language == code:
                self.cbLang.set_active(i)
                break

        self.chkBackup.set_active(self.opt.optionList.backup)
        self.sbDay.set_value(self.opt.optionList.interval)
        self.fcbutton.set_current_folder(self.opt.optionList.location)

        # Appearance
        self.chkName.set_active(self.opt.optionList.colname)
        self.chkColour.set_active(self.opt.optionList.colcolour)
        self.chkSex.set_active(self.opt.optionList.colsex)
        self.chkLoft.set_active(self.opt.optionList.colloft)
        self.chkStrain.set_active(self.opt.optionList.colstrain)

        self.cbThemes.set_active(self.opt.optionList.theme)

        self.chkArrows.set_active(self.opt.optionList.arrows)
        self.chkStats.set_active(self.opt.optionList.stats)
        self.chkToolbar.set_active(self.opt.optionList.toolbar)
        self.chkStatusbar.set_active(self.opt.optionList.statusbar)

        # Printing
        self.cbPaper.set_active(self.opt.optionList.paper)
        self.cbLayout.set_active(self.opt.optionList.layout)

        self.chkPerName.set_active(self.opt.optionList.perName)
        self.chkPerAddress.set_active(self.opt.optionList.perAddress)
        self.chkPerPhone.set_active(self.opt.optionList.perPhone)
        self.chkPerEmail.set_active(self.opt.optionList.perEmail)

        self.chkPigName.set_active(self.opt.optionList.pigName)
        self.chkPigColour.set_active(self.opt.optionList.pigColour)
        self.chkPigSex.set_active(self.opt.optionList.pigSex)
        self.chkPigExtra.set_active(self.opt.optionList.pigExtra)
        self.chkPigImage.set_active(self.opt.optionList.pigImage)

    def on_close_dialog(self, widget, event=None):
        self.optionsdialog.destroy()

    def on_cancel_clicked(self, widget):
        self.optionsdialog.destroy()

    def on_chkBackup_toggled(self, widget):
        self.alignbackup.set_sensitive(widget.get_active())

    def on_sbDay_changed(self, widget):
        value = widget.get_value_as_int()

        dstring = _("days")
        if value == 1:
            dstring = _("day")

        widget.set_text('%s %s' % (value, dstring))

    def on_default_clicked(self, widget):
        if widgets.message_dialog('warning', messages.MSG_DEFAULT_OPTIONS, self.optionsdialog):
            self.opt.write_default()
            self.opt = options.GetOptions()
            self.set_options()

            self.finish_options(True)

    def on_ok_clicked(self, widget):
        dic = {"Options": {'theme': self.cbThemes.get_active(),
                           'arrows': str(self.chkArrows.get_active()),
                           'stats': str(self.chkStats.get_active()),
                           'toolbar': str(self.chkToolbar.get_active()),
                           'statusbar': str(self.chkStatusbar.get_active()),
                           'update': str(self.chkUpdate.get_active()),
                           'language': self.languagelookup[self.cbLang.get_active()][1],
                           'runs': self.opt.optionList.runs
                          },
               "Backup": {'backup': str(self.chkBackup.get_active()),
                          'interval': self.sbDay.get_value_as_int(),
                          'location': self.fcbutton.get_current_folder(),
                          'last': self.opt.optionList.last
                         },
               "Columns": {'name': str(self.chkName.get_active()),
                           'colour': str(self.chkColour.get_active()),
                           'sex': str(self.chkSex.get_active()),
                           'loft': str(self.chkLoft.get_active()),
                           'strain': str(self.chkStrain.get_active())
                          },
                "Printing": {"paper": self.cbPaper.get_active(),
                             "layout": self.cbLayout.get_active(),
                             "perName": str(self.chkPerName.get_active()),
                             "perAddress": str(self.chkPerAddress.get_active()),
                             "perPhone": str(self.chkPerPhone.get_active()),
                             "perEmail": str(self.chkPerEmail.get_active()),
                             "pigName": str(self.chkPigName.get_active()),
                             "pigColour": str(self.chkPigColour.get_active()),
                             "pigSex": str(self.chkPigSex.get_active()),
                             "pigExtra": str(self.chkPigExtra.get_active()),
                             "pigImage": str(self.chkPigImage.get_active()),
                            }
              }

        self.opt.write_options(dic)

        self.finish_options()

    def finish_options(self, set_default=False):

        self.main.options = options.GetOptions()

        if self.languagelookup[self.cbLang.get_active()][1] != self.opt.optionList.language or\
           const.WINDOWS and self.cbThemes.get_active() != self.opt.optionList.theme:
            widgets.message_dialog('info', messages.MSG_RESTART_APP, self.optionsdialog)

        self.main.set_treeview_columns()

        if self.chkArrows.get_active():
            self.main.vboxButtons.show()

            self.main.blockMenuCallback = True
            self.main.MenuArrows.set_active(True)
            self.main.blockMenuCallback = False
        else:
            self.main.vboxButtons.hide()

            self.main.blockMenuCallback = True
            self.main.MenuArrows.set_active(False)
            self.main.blockMenuCallback = False

        if self.chkStats.get_active():
            self.main.tableStatistics.show()

            self.main.blockMenuCallback = True
            self.main.MenuStats.set_active(True)
            self.main.blockMenuCallback = False
        else:
            self.main.tableStatistics.hide()

            self.main.blockMenuCallback = True
            self.main.MenuStats.set_active(False)
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

        if not set_default:
            self.optionsdialog.destroy()

