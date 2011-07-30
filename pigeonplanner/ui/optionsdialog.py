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
Options dialog class
"""


import os

import gtk
import gobject

import const
import builder
import messages
from ui import dialogs
from ui.widgets import comboboxes


class OptionsDialog(builder.GtkBuilder):
    __gsignals__ = {'interface-changed': (gobject.SIGNAL_RUN_LAST,
                                      None, (bool, bool, bool, bool)),
                    }
    def __init__(self, parent, options):
        builder.GtkBuilder.__init__(self, "OptionsDialog.ui")

        self.options = options

        # Build main treeview
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)

        # Add the categories
        # [(Category, image, [children]), ]
        categories = [(_("General"), gtk.STOCK_PROPERTIES,
                            []),
                      (_("Appearance"), gtk.STOCK_PAGE_SETUP,
                            []),
                      (_("Printing"), gtk.STOCK_PRINT,
                            [_("Pedigree"),
                             _("Results"),
                            ]),
                    ]
        i = 0
        for par, img, children in categories:
            icon = self.treeview.render_icon(img, gtk.ICON_SIZE_LARGE_TOOLBAR)
            p_iter = self.treestore.append(None, [i, icon, par])
            for child in children:
                i += 1
                self.treestore.append(p_iter, [i, None, child])
            i += 1
        self._selection.select_path(0)

        # Show the theme changer on Windows
        if const.WINDOWS and os.path.exists('.\\share\\themes'):
            self.framethemes.show()
            themes = os.listdir('.\\share\\themes\\')
            comboboxes.fill_combobox(self.combothemes, themes)

        # Fill language combobox with available languages
        try:
            self.languages = os.listdir(const.LANGDIR)
        except OSError:
            # There are no compiled mo-files
            self.languages = []
        self.languages.insert(0, 'en')
        self.languages.sort()
        self.languages.insert(0, 'Default')
        comboboxes.fill_combobox(self.combolangs, self.languages, sort=False)

        self._set_options()

        self.optionsdialog.set_transient_for(parent)
        self.optionsdialog.show()

    # Callbacks
    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        if rowiter is None: return

        try:
            self.notebook.set_current_page(model[rowiter][0])
        except TypeError:
            pass

    def on_close_dialog(self, widget, event=None):
        self.optionsdialog.destroy()

    def on_checkbackup_toggled(self, widget):
        self.alignbackup.set_sensitive(widget.get_active())

    def on_spinday_changed(self, widget):
        value = widget.get_value_as_int()
        dstring = _("days") if value == 1 else _("day")
        widget.set_text('%s %s' % (value, dstring))

    def on_buttondefault_clicked(self, widget):
        d = dialogs.MessageDialog(const.WARNING,
                                  messages.MSG_DEFAULT_OPTIONS,
                                  self.optionsdialog)
        if d.yes:
            self.options.write_default()
            self._set_options()
            self._finish_options(False, True)

    def on_buttoncancel_clicked(self, widget):
        self.optionsdialog.destroy()

    def on_buttonok_clicked(self, widget):
        restart = self.combolangs.get_active_text() != self.options.language or\
                    (const.WINDOWS and
                     self.combothemes.get_active() != self.options.theme)

        dic = {"Options": {'theme': self.combothemes.get_active(),
                           'arrows': str(self.chkArrows.get_active()),
                           'stats': str(self.chkStats.get_active()),
                           'toolbar': str(self.chkToolbar.get_active()),
                           'statusbar': str(self.chkStatusbar.get_active()),
                           'update': str(self.chkUpdate.get_active()),
                           'language': self.combolangs.get_active_text()
                          },
               "Window": {'window_x': self.options.window_x,
                          'window_y': self.options.window_y,
                          'window_w': self.options.window_w,
                          'window_h': self.options.window_h
                         },
               "Backup": {'backup': str(self.checkbackup.get_active()),
                          'interval': self.spinday.get_value_as_int(),
                          'location': self.fcbutton.get_current_folder(),
                          'last': self.options.last
                         },
               "Columns": {'name': str(self.chkName.get_active()),
                           'colour': str(self.chkColour.get_active()),
                           'sex': str(self.chkSex.get_active()),
                           'loft': str(self.chkLoft.get_active()),
                           'strain': str(self.chkStrain.get_active()),
                           'coef': str(self.chkCoef.get_active()),
                           'sector': str(self.chkSector.get_active()),
                           'category': str(self.chkCategory.get_active()),
                           'type': str(self.chkType.get_active()),
                           'weather': str(self.chkWeather.get_active()),
                           'wind': str(self.chkWind.get_active()),
                           'comment': str(self.chkComment.get_active()),
                          },
               "Printing": {
                    "paper": self.cbPaper.get_active(),
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
                    "resColumnNames": str(self.chkResColumnNames.get_active()),
                    "resDate": str(self.chkResDate.get_active()),
                   }
              }

        self.options.write_options(dic)
        self._finish_options(restart)

    # Internal methods
    def _set_options(self):
        # General
        self.chkUpdate.set_active(self.options.update)

        for index, lang in enumerate(self.languages):
            if self.options.language == lang:
                self.combolangs.set_active(index)
                break

        self.checkbackup.set_active(self.options.backup)
        self.spinday.set_value(self.options.interval)
        self.fcbutton.set_current_folder(self.options.location)

        # Appearance
        self.chkName.set_active(self.options.colname)
        self.chkColour.set_active(self.options.colcolour)
        self.chkSex.set_active(self.options.colsex)
        self.chkLoft.set_active(self.options.colloft)
        self.chkStrain.set_active(self.options.colstrain)
        self.chkCoef.set_active(self.options.colcoef)
        self.chkSector.set_active(self.options.colsector)
        self.chkCategory.set_active(self.options.colcategory)
        self.chkType.set_active(self.options.coltype)
        self.chkWeather.set_active(self.options.colweather)
        self.chkWind.set_active(self.options.colwind)
        self.chkComment.set_active(self.options.colcomment)

        self.combothemes.set_active(self.options.theme)

        self.chkArrows.set_active(self.options.arrows)
        self.chkStats.set_active(self.options.stats)
        self.chkToolbar.set_active(self.options.toolbar)
        self.chkStatusbar.set_active(self.options.statusbar)

        # Printing
        self.cbPaper.set_active(self.options.paper)
        self.cbLayout.set_active(self.options.layout)

        self.chkPerName.set_active(self.options.perName)
        self.chkPerAddress.set_active(self.options.perAddress)
        self.chkPerPhone.set_active(self.options.perPhone)
        self.chkPerEmail.set_active(self.options.perEmail)

        self.chkPigName.set_active(self.options.pigName)
        self.chkPigColour.set_active(self.options.pigColour)
        self.chkPigSex.set_active(self.options.pigSex)
        self.chkPigExtra.set_active(self.options.pigExtra)
        self.chkPigImage.set_active(self.options.pigImage)

        self.chkResColumnNames.set_active(self.options.resColumnNames)
        self.chkResDate.set_active(self.options.resDate)

    def _finish_options(self, restart=False, set_default=False):
        arrows = self.chkArrows.get_active()
        stats = self.chkStats.get_active()
        toolbar = self.chkToolbar.get_active()
        statusbar = self.chkStatusbar.get_active()
        self.emit('interface-changed', arrows, stats, toolbar, statusbar)

        if restart:
            dialogs.MessageDialog(const.INFO, messages.MSG_RESTART_APP,
                                  self.optionsdialog)

        if not set_default:
            self.optionsdialog.destroy()

