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
import common
import config
import builder
import messages
from ui.widgets import comboboxes
from ui.messagedialog import InfoDialog, WarningDialog
from translation import gettext as _
from reportlib import report, PRINT_ACTION_PREVIEW
from reports import get_pedigree


class OptionsDialog(builder.GtkBuilder, gobject.GObject):
    __gsignals__ = {'interface-changed': (gobject.SIGNAL_RUN_LAST,
                                      None, (bool, bool, bool, bool)),
                    }
    def __init__(self, parent, parser, database):
        builder.GtkBuilder.__init__(self, "OptionsDialog.ui")
        gobject.GObject.__init__(self)

        self.parser = parser
        self.database = database

        # Build main treeview
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)

        # Add the categories
        # [(Category, image, [children]), ]
        categories = [(_("General"), gtk.STOCK_PROPERTIES,
                            []),
                      (_("Appearance"), gtk.STOCK_PAGE_SETUP,
                            []),
                      (_("Columns"), 'columns',
                            []),
                      (_("Printing"), gtk.STOCK_PRINT,
                            [_("Pedigree"),
                             _("Pigeons"),
                             _("Results"),
                            ]),
                      (_("Advanced"), gtk.STOCK_PREFERENCES,
                            []),
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
        self.treeview.expand_all()

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

    def on_chkShowHidden_toggled(self, widget):
        self.hboxColorHidden.set_sensitive(not widget.get_active())

    def on_btnPreview_clicked(self, widget):
        selected = self.cbLayout.get_active()
        userinfo = common.get_own_address(self.database)
        PedigreeReport, PedigreeReportOptions = get_pedigree(layout=selected)
        psize = common.get_pagesize_from_opts()
        opts = PedigreeReportOptions(psize, print_action=PRINT_ACTION_PREVIEW,
                                            parent=self.optionsdialog)
        report(PedigreeReport, opts, self.parser, None, userinfo)

    def on_buttondefault_clicked(self, widget):
        if WarningDialog(messages.MSG_DEFAULT_OPTIONS, self.optionsdialog).run():
            config.reset()
            self._set_options()
            self._finish_options(False, True)

    def on_buttoncancel_clicked(self, widget):
        self.optionsdialog.destroy()

    def on_buttonok_clicked(self, widget):
        restart = self.combolangs.get_active_text() != config.get('options.language') or\
                    (const.WINDOWS and
                     self.combothemes.get_active() != config.get('interface.theme'))

        settings = [
                ('options.check-for-updates', self.chkUpdate.get_active()),
                ('options.check-for-dev-updates', self.chkDevUpdate.get_active()),
                ('options.language', self.combolangs.get_active_text()),
                ('options.coef-multiplier', self.spincoef.get_value_as_int()),
                ##('options.format-date', self.entrydate.get_text()),

                ('interface.arrows', self.chkArrows.get_active()),
                ('interface.stats', self.chkStats.get_active()),
                ('interface.theme', self.combothemes.get_active()),
                ('interface.toolbar', self.chkToolbar.get_active()),
                ('interface.statusbar', self.chkStatusbar.get_active()),
                ('interface.missing-pigeon-hide', self.chkShowHidden.get_active()),
                ('interface.missing-pigeon-color', self.chkColorHidden.get_active()),
                ('interface.missing-pigeon-color-value',
                                    self.chkColorHiddenValue.get_color().to_string()),

                ('backup.automatic-backup', self.checkbackup.get_active()),
                ('backup.interval', self.spinday.get_value_as_int()),
                ('backup.location', self.fcbutton.get_current_folder()),

                ('columns.pigeon-name', self.chkName.get_active()),
                ('columns.pigeon-colour', self.chkColour.get_active()),
                ('columns.pigeon-sex', self.chkSex.get_active()),
                ('columns.pigeon-strain', self.chkStrain.get_active()),
                ('columns.pigeon-status', self.chkStatus.get_active()),
                ('columns.pigeon-loft', self.chkLoft.get_active()),
                ('columns.result-coef', self.chkCoef.get_active()),
                ('columns.result-sector', self.chkSector.get_active()),
                ('columns.result-category', self.chkCategory.get_active()),
                ('columns.result-type', self.chkType.get_active()),
                ('columns.result-weather', self.chkWeather.get_active()),
                ('columns.result-wind', self.chkWind.get_active()),
                ('columns.result-comment', self.chkComment.get_active()),

                ('printing.general-paper', self.cbPaper.get_active()),
                ('printing.pedigree-layout', self.cbLayout.get_active()),
                ('printing.pedigree-box-colour', self.chkPigOptColour.get_active()),
                ('printing.pedigree-name', self.chkPigName.get_active()),
                ('printing.pedigree-colour', self.chkPigColour.get_active()),
                ('printing.pedigree-sex', self.chkPigSex.get_active()),
                ('printing.pedigree-extra', self.chkPigExtra.get_active()),
                ('printing.pedigree-image', self.chkPigImage.get_active()),
                ('printing.pigeon-colnames', self.chkPigColumnNames.get_active()),
                ('printing.pigeon-sex', self.chkPigOptSex.get_active()),
                ('printing.result-colnames', self.chkResColumnNames.get_active()),
                ('printing.result-date', self.chkResDate.get_active()),
                ('printing.user-name', self.chkPerName.get_active()),
                ('printing.user-address', self.chkPerAddress.get_active()),
                ('printing.user-phone', self.chkPerPhone.get_active()),
                ('printing.user-email', self.chkPerEmail.get_active()),
            ]

        for option, value in settings:
            config.set(option, value)
        config.save()
        self._finish_options(restart)

    # Internal methods
    def _set_options(self):
        # General
        self.chkUpdate.set_active(config.get('options.check-for-updates'))
        self.chkDevUpdate.set_active(config.get('options.check-for-dev-updates'))

        for index, lang in enumerate(self.languages):
            if config.get('options.language') == lang:
                self.combolangs.set_active(index)
                break

        self.checkbackup.set_active(config.get('backup.automatic-backup'))
        self.spinday.set_value(config.get('backup.interval'))
        self.fcbutton.set_current_folder(config.get('backup.location'))
        self.spincoef.set_value(config.get('options.coef-multiplier'))
        ##self.entrydate.set_text(config.get('options.format-date'))

        # Appearance
        self.chkName.set_active(config.get('columns.pigeon-name'))
        self.chkColour.set_active(config.get('columns.pigeon-colour'))
        self.chkSex.set_active(config.get('columns.pigeon-sex'))
        self.chkLoft.set_active(config.get('columns.pigeon-loft'))
        self.chkStrain.set_active(config.get('columns.pigeon-strain'))
        self.chkStatus.set_active(config.get('columns.pigeon-status'))
        self.chkCoef.set_active(config.get('columns.result-coef'))
        self.chkSector.set_active(config.get('columns.result-sector'))
        self.chkCategory.set_active(config.get('columns.result-category'))
        self.chkType.set_active(config.get('columns.result-type'))
        self.chkWeather.set_active(config.get('columns.result-weather'))
        self.chkWind.set_active(config.get('columns.result-wind'))
        self.chkComment.set_active(config.get('columns.result-comment'))

        self.combothemes.set_active(config.get('interface.theme'))

        self.chkArrows.set_active(config.get('interface.arrows'))
        self.chkStats.set_active(config.get('interface.stats'))
        self.chkToolbar.set_active(config.get('interface.toolbar'))
        self.chkStatusbar.set_active(config.get('interface.statusbar'))
        self.chkShowHidden.set_active(config.get('interface.missing-pigeon-hide'))
        self.chkColorHidden.set_active(config.get('interface.missing-pigeon-color'))
        self.chkColorHiddenValue.set_color(
                gtk.gdk.color_parse(config.get('interface.missing-pigeon-color-value')))

        # Printing
        self.cbPaper.set_active(config.get('printing.general-paper'))
        self.cbLayout.set_active(config.get('printing.pedigree-layout'))
        self.chkPigOptColour.set_active(config.get('printing.pedigree-box-colour'))

        self.chkPerName.set_active(config.get('printing.user-name'))
        self.chkPerAddress.set_active(config.get('printing.user-address'))
        self.chkPerPhone.set_active(config.get('printing.user-phone'))
        self.chkPerEmail.set_active(config.get('printing.user-email'))

        self.chkPigName.set_active(config.get('printing.pedigree-name'))
        self.chkPigColour.set_active(config.get('printing.pedigree-colour'))
        self.chkPigSex.set_active(config.get('printing.pedigree-sex'))
        self.chkPigExtra.set_active(config.get('printing.pedigree-extra'))
        self.chkPigImage.set_active(config.get('printing.pedigree-image'))

        self.chkPigColumnNames.set_active(config.get('printing.pigeon-colnames'))
        self.chkPigOptSex.set_active(config.get('printing.pigeon-sex'))

        self.chkResColumnNames.set_active(config.get('printing.result-colnames'))
        self.chkResDate.set_active(config.get('printing.result-date'))

    def _finish_options(self, restart=False, set_default=False):
        arrows = self.chkArrows.get_active()
        stats = self.chkStats.get_active()
        toolbar = self.chkToolbar.get_active()
        statusbar = self.chkStatusbar.get_active()
        self.emit('interface-changed', arrows, stats, toolbar, statusbar)

        if restart:
            InfoDialog(messages.MSG_RESTART_APP, self.optionsdialog)

        if not set_default:
            self.optionsdialog.destroy()

