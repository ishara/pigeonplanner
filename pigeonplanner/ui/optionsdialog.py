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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.ui.messagedialog import InfoDialog, WarningDialog
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import config
from pigeonplanner.reportlib import report, PRINT_ACTION_PREVIEW
from pigeonplanner.reports import get_pedigree


class OptionsDialog(builder.GtkBuilder, GObject.GObject):
    __gsignals__ = {
        "interface-changed": (GObject.SIGNAL_RUN_LAST, None, (bool, bool, bool, bool)),
    }

    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "OptionsDialog.ui")
        GObject.GObject.__init__(self)

        # Build main treeview
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)

        # Add the categories
        # [(Category, image, [children]), ]
        categories = [
            (_("General"), "document-properties", []),
            (_("Appearance"), "document-page-setup", []),
            (_("Columns"), "icon_columns", []),
            (_("Printing"), "document-print",
                [_("Pedigree"), _("Pigeons"), _("Results")]),
            (_("Advanced"), "preferences-system", []),
        ]
        i = 0
        for par, icon_name, children in categories:
            p_iter = self.widgets.treestore.append(None, [i, icon_name, par])
            for child in children:
                i += 1
                self.widgets.treestore.append(p_iter, [i, None, child])
            i += 1
        self.widgets.selection.select_path(0)
        self.widgets.treeview.expand_all()

        # Fill language combobox with available languages
        try:
            self.languages = os.listdir(const.LANGDIR)
            self.languages.sort()
        except OSError:
            # There are no compiled mo-files
            self.languages = []
        self.languages.insert(0, "Default")
        for language in self.languages:
            self.widgets.combolangs.append_text(language)

        # Only show theme selection on Windows
        if const.WINDOWS:
            self.widgets.frametheme.show()

        self._set_options()

        self.widgets.optionsdialog.set_transient_for(parent)
        self.widgets.optionsdialog.show()

    # Callbacks
    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        if rowiter is None:
            return

        try:
            self.widgets.notebook.set_current_page(model[rowiter][0])
        except TypeError:
            pass

    def on_close_dialog(self, _widget, _event=None):
        self.widgets.optionsdialog.destroy()

    def on_checkbackup_toggled(self, widget):
        self.widgets.alignbackup.set_sensitive(widget.get_active())

    # noinspection PyMethodMayBeStatic
    def on_spinday_changed(self, widget):
        value = widget.get_value_as_int()
        dstring = _("day") if value == 1 else _("days")
        widget.set_text("%s %s" % (value, dstring))

    def on_chkShowHidden_toggled(self, widget):
        self.widgets.hboxColorHidden.set_sensitive(not widget.get_active())

    def on_chkSex_toggled(self, widget):
        self.widgets.vboxSexCol.set_sensitive(widget.get_active())

    def on_chkPigOptExtraLine_toggled(self, widget):
        self.widgets.align_extra_line.set_sensitive(widget.get_active())

    def on_btnPreview_clicked(self, _widget):
        selected = self.widgets.cbLayout.get_active()
        userinfo = common.get_own_address()
        pedigree_report, pedigree_report_options = get_pedigree(layout=selected)
        psize = common.get_pagesize_from_opts()
        opts = pedigree_report_options(psize, print_action=PRINT_ACTION_PREVIEW,
                                       parent=self.widgets.optionsdialog)
        report(pedigree_report, opts, None, userinfo)

    def on_buttondefault_clicked(self, _widget):
        if WarningDialog(messages.MSG_DEFAULT_OPTIONS, self.widgets.optionsdialog).run():
            config.save_backup()
            config.reset()
            self._set_options()
            self._finish_options(False, True)

    def on_buttoncancel_clicked(self, _widget):
        self.widgets.optionsdialog.destroy()

    def on_buttonok_clicked(self, _widget):
        restart = self.widgets.combolangs.get_active_text() != config.get("options.language")

        if self.widgets.radioSexText.get_active():
            sexcoltype = 1
        elif self.widgets.radioSexImage.get_active():
            sexcoltype = 2
        elif self.widgets.radioSexTextImage.get_active():
            sexcoltype = 3

        if not self.widgets.chkPigOptExtraLine.get_active():
            extra_line_type = 0
        elif self.widgets.radioPigeonExtraColour.get_active():
            extra_line_type = 1
        elif self.widgets.radioPigeonExtraStrain.get_active():
            extra_line_type = 2
        elif self.widgets.radioPigeonExtraLoft.get_active():
            extra_line_type = 3

        settings = [
                ("options.check-for-updates", self.widgets.chkUpdate.get_active()),
                ("options.check-for-dev-updates", self.widgets.chkDevUpdate.get_active()),
                ("options.language", self.widgets.combolangs.get_active_text()),
                ("options.coef-multiplier", self.widgets.spincoef.get_value_as_int()),
                ("options.distance-unit", self.widgets.combodistance.get_active()),
                ("options.speed-unit", self.widgets.combospeed.get_active()),
                ##("options.format-date", self.entrydate.get_text()),

                ("interface.arrows", self.widgets.chkArrows.get_active()),
                ("interface.stats", self.widgets.chkStats.get_active()),
                ("interface.toolbar", self.widgets.chkToolbar.get_active()),
                ("interface.statusbar", self.widgets.chkStatusbar.get_active()),
                ("interface.pigeon-sort", self.widgets.cbSortPigeons.get_active()),
                ("interface.results-mode", self.widgets.cbResultsMode.get_active()),
                ("interface.missing-pigeon-hide", self.widgets.chkShowHidden.get_active()),
                ("interface.missing-pigeon-color", self.widgets.chkColorHidden.get_active()),
                ("interface.missing-pigeon-color-value",
                    self.widgets.chkColorHiddenValue.get_color().to_string()),
                ("interface.theme-name", self.widgets.cbThemeName.get_active_text()),

                ("backup.automatic-backup", self.widgets.checkbackup.get_active()),
                ("backup.interval", self.widgets.spinday.get_value_as_int()),
                ("backup.location", self.widgets.fcbutton.get_filename()),

                ("columns.pigeon-name", self.widgets.chkName.get_active()),
                ("columns.pigeon-band-country", self.widgets.chkCountry.get_active()),
                ("columns.pigeon-colour", self.widgets.chkColour.get_active()),
                ("columns.pigeon-sex", self.widgets.chkSex.get_active()),
                ("columns.pigeon-sex-type", sexcoltype),
                ("columns.pigeon-sire", self.widgets.chkSire.get_active()),
                ("columns.pigeon-dam", self.widgets.chkDam.get_active()),
                ("columns.pigeon-strain", self.widgets.chkStrain.get_active()),
                ("columns.pigeon-status", self.widgets.chkStatus.get_active()),
                ("columns.pigeon-loft", self.widgets.chkLoft.get_active()),
                ("columns.result-coef", self.widgets.chkCoef.get_active()),
                ("columns.result-speed", self.widgets.chkSpeed.get_active()),
                ("columns.result-sector", self.widgets.chkSector.get_active()),
                ("columns.result-category", self.widgets.chkCategory.get_active()),
                ("columns.result-type", self.widgets.chkType.get_active()),
                ("columns.result-weather", self.widgets.chkWeather.get_active()),
                ("columns.result-temperature", self.widgets.chkTemperature.get_active()),
                ("columns.result-wind", self.widgets.chkWind.get_active()),
                ("columns.result-windspeed", self.widgets.chkWindspeed.get_active()),
                ("columns.result-comment", self.widgets.chkComment.get_active()),

                ("printing.general-paper", self.widgets.cbPaper.get_active()),
                ("printing.pedigree-layout", self.widgets.cbLayout.get_active()),
                ("printing.pedigree-use-box-color", self.widgets.chkBoxColor.get_active()),
                ("printing.pedigree-use-box-fill-color", self.widgets.chkBoxFillColor.get_active()),
                ("printing.pedigree-box-extra-line", extra_line_type),
                ("printing.pedigree-name", self.widgets.chkPigName.get_active()),
                ("printing.pedigree-colour", self.widgets.chkPigColour.get_active()),
                ("printing.pedigree-sex", self.widgets.chkPigSex.get_active()),
                ("printing.pedigree-extra", self.widgets.chkPigExtra.get_active()),
                ("printing.pedigree-image", self.widgets.chkPigImage.get_active()),
                ("printing.pigeon-colnames", self.widgets.chkPigColumnNames.get_active()),
                ("printing.pigeon-sex", self.widgets.chkPigOptSex.get_active()),
                ("printing.result-colnames", self.widgets.chkResColumnNames.get_active()),
                ("printing.result-date", self.widgets.chkResDate.get_active()),
                ("printing.user-name", self.widgets.chkPerName.get_active()),
                ("printing.user-address", self.widgets.chkPerAddress.get_active()),
                ("printing.user-phone", self.widgets.chkPerPhone.get_active()),
                ("printing.user-email", self.widgets.chkPerEmail.get_active()),
            ]

        config.save_backup()
        for option, value in settings:
            config.set(option, value)
        config.save()
        self._finish_options(restart)

    # Internal methods
    def _set_options(self):
        # General
        self.widgets.chkUpdate.set_active(config.get("options.check-for-updates"))
        self.widgets.chkDevUpdate.set_active(config.get("options.check-for-dev-updates"))

        self.widgets.combolangs.set_active(0)
        for index, lang in enumerate(self.languages):
            if config.get("options.language") == lang:
                self.widgets.combolangs.set_active(index)
                break

        self.widgets.checkbackup.set_active(config.get("backup.automatic-backup"))
        self.widgets.spinday.set_value(config.get("backup.interval"))
        self.widgets.fcbutton.set_current_folder(config.get("backup.location"))
        self.widgets.combodistance.set_active(config.get("options.distance-unit"))
        self.widgets.combospeed.set_active(config.get("options.speed-unit"))
        self.widgets.spincoef.set_value(config.get("options.coef-multiplier"))
        ##self.widgets.entrydate.set_text(config.get("options.format-date"))

        # Appearance
        self.widgets.chkName.set_active(config.get("columns.pigeon-name"))
        self.widgets.chkCountry.set_active(config.get("columns.pigeon-band-country"))
        self.widgets.chkColour.set_active(config.get("columns.pigeon-colour"))
        self.widgets.chkSex.set_active(config.get("columns.pigeon-sex"))
        self.widgets.chkLoft.set_active(config.get("columns.pigeon-loft"))
        self.widgets.chkSire.set_active(config.get("columns.pigeon-sire"))
        self.widgets.chkDam.set_active(config.get("columns.pigeon-dam"))
        self.widgets.chkStrain.set_active(config.get("columns.pigeon-strain"))
        self.widgets.chkStatus.set_active(config.get("columns.pigeon-status"))
        self.widgets.chkCoef.set_active(config.get("columns.result-coef"))
        self.widgets.chkSpeed.set_active(config.get("columns.result-speed"))
        self.widgets.chkSector.set_active(config.get("columns.result-sector"))
        self.widgets.chkCategory.set_active(config.get("columns.result-category"))
        self.widgets.chkType.set_active(config.get("columns.result-type"))
        self.widgets.chkWeather.set_active(config.get("columns.result-weather"))
        self.widgets.chkTemperature.set_active(config.get("columns.result-temperature"))
        self.widgets.chkWind.set_active(config.get("columns.result-wind"))
        self.widgets.chkWindspeed.set_active(config.get("columns.result-windspeed"))
        self.widgets.chkComment.set_active(config.get("columns.result-comment"))

        sexcoltype = config.get("columns.pigeon-sex-type")
        if sexcoltype == 1:
            self.widgets.radioSexText.set_active(True)
        elif sexcoltype == 2:
            self.widgets.radioSexImage.set_active(True)
        elif sexcoltype == 3:
            self.widgets.radioSexTextImage.set_active(True)

        self.widgets.chkArrows.set_active(config.get("interface.arrows"))
        self.widgets.chkStats.set_active(config.get("interface.stats"))
        self.widgets.chkToolbar.set_active(config.get("interface.toolbar"))
        self.widgets.chkStatusbar.set_active(config.get("interface.statusbar"))
        self.widgets.cbSortPigeons.set_active(config.get("interface.pigeon-sort"))
        self.widgets.cbResultsMode.set_active(config.get("interface.results-mode"))
        self.widgets.chkShowHidden.set_active(config.get("interface.missing-pigeon-hide"))
        self.widgets.chkColorHidden.set_active(config.get("interface.missing-pigeon-color"))
        self.widgets.chkColorHiddenValue.set_color(
                Gdk.color_parse(config.get("interface.missing-pigeon-color-value")))
        self.widgets.cbThemeName.set_active_id(config.get("interface.theme-name"))

        # Printing
        extra_line_type = config.get("printing.pedigree-box-extra-line")
        if extra_line_type == 0:
            self.widgets.chkPigOptExtraLine.set_active(False)
        elif extra_line_type == 1:
            self.widgets.chkPigOptExtraLine.set_active(True)
            self.widgets.radioPigeonExtraColour.set_active(True)
        elif extra_line_type == 2:
            self.widgets.chkPigOptExtraLine.set_active(True)
            self.widgets.radioPigeonExtraStrain.set_active(True)
        elif extra_line_type == 3:
            self.widgets.chkPigOptExtraLine.set_active(True)
            self.widgets.radioPigeonExtraLoft.set_active(True)

        self.widgets.cbPaper.set_active(config.get("printing.general-paper"))
        self.widgets.cbLayout.set_active(config.get("printing.pedigree-layout"))
        self.widgets.chkBoxColor.set_active(config.get("printing.pedigree-use-box-color"))
        self.widgets.chkBoxFillColor.set_active(config.get("printing.pedigree-use-box-fill-color"))

        self.widgets.chkPerName.set_active(config.get("printing.user-name"))
        self.widgets.chkPerAddress.set_active(config.get("printing.user-address"))
        self.widgets.chkPerPhone.set_active(config.get("printing.user-phone"))
        self.widgets.chkPerEmail.set_active(config.get("printing.user-email"))

        self.widgets.chkPigName.set_active(config.get("printing.pedigree-name"))
        self.widgets.chkPigColour.set_active(config.get("printing.pedigree-colour"))
        self.widgets.chkPigSex.set_active(config.get("printing.pedigree-sex"))
        self.widgets.chkPigExtra.set_active(config.get("printing.pedigree-extra"))
        self.widgets.chkPigImage.set_active(config.get("printing.pedigree-image"))

        self.widgets.chkPigColumnNames.set_active(config.get("printing.pigeon-colnames"))
        self.widgets.chkPigOptSex.set_active(config.get("printing.pigeon-sex"))

        self.widgets.chkResColumnNames.set_active(config.get("printing.result-colnames"))
        self.widgets.chkResDate.set_active(config.get("printing.result-date"))

    def _finish_options(self, restart=False, set_default=False):
        arrows = self.widgets.chkArrows.get_active()
        stats = self.widgets.chkStats.get_active()
        toolbar = self.widgets.chkToolbar.get_active()
        statusbar = self.widgets.chkStatusbar.get_active()
        self.emit("interface-changed", arrows, stats, toolbar, statusbar)

        if const.WINDOWS:
            theme_name = self.widgets.cbThemeName.get_active_text()
            gtksettings = Gtk.Settings.get_default()
            gtksettings.set_property("gtk-theme-name", theme_name)

        if restart:
            InfoDialog(messages.MSG_RESTART_APP, self.widgets.optionsdialog)

        if not set_default:
            self.widgets.optionsdialog.destroy()
