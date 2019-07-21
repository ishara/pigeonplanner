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

import os

from gi.repository import Gtk

from pigeonplanner.ui import tools
from pigeonplanner.ui import component
from pigeonplanner.ui.filechooser import PdfSaver
from pigeonplanner.ui.messagedialog import InfoDialog, ErrorDialog
from pigeonplanner.core import common
from pigeonplanner.core import config
from pigeonplanner.reportlib import (report, ReportError, PRINT_ACTION_DIALOG,
                                     PRINT_ACTION_PREVIEW, PRINT_ACTION_EXPORT)
from pigeonplanner.reports import get_pedigree


(PREVIOUS,
 NEXT_SIRE,
 NEXT_DAM) = range(3)


class PedigreeWindow(Gtk.Window):
    ui = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Previous"/>
      <toolitem action="Home"/>
      <toolitem action="Next"/>
      <separator/>
      <toolitem action="Save"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""
    def __init__(self, parent, pedigree, pigeon):
        Gtk.Window.__init__(self)
        self.connect("delete-event", self.on_close_dialog)
        self.set_modal(True)
        self.resize(960, 600)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_skip_taskbar_hint(True)

        self.pedigree = pedigree
        self._original_pigeon = pigeon
        self._treeview = component.get("Treeview")
        self._build_ui()
        self.set_pigeon(pigeon)
        self.show_all()

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon
        self._current_pigeon = pigeon
        self._current_pigeon_path = self._treeview.get_path_for_pigeon(pigeon)
        self._previous_pigeons = []
        self.pdfname = "%s_%s.pdf" % (_("Pedigree"), pigeon.band.replace(" ", "_").replace("/", "-"))
        name = pigeon.name
        if name:
            name = ", " + name
        title = "%s: %s%s - %s" % (_("Pedigree"), pigeon.band,
                                   name, pigeon.sex_string)
        self.set_title(title)

        is_home = self._original_pigeon == pigeon
        self._home_pedigree_button.set_sensitive(not is_home)
        has_previous = self._current_pigeon_path != 0
        self._previous_pedigree_button.set_sensitive(has_previous)
        has_next = self._current_pigeon_path < len(self._treeview.get_model()) - 1
        self._next_pedigree_button.set_sensitive(has_next)

        self.pedigree.draw_pedigree(self._get_pedigree_table(), pigeon, True,
                                    self.on_pedigree_draw)

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        actiongroup = Gtk.ActionGroup("PedigreeWindowActions")
        actiongroup.add_actions((
            ("Previous", Gtk.STOCK_GO_BACK, None, None,
                    _("Go to the previous pedigree"), self.on_previous_clicked),
            ("Home", Gtk.STOCK_HOME, None, None,
                    _("Go to the first selected pedigree"), self.on_home_clicked),
            ("Next", Gtk.STOCK_GO_FORWARD, None, None,
                    _("Go to the next pedigree"), self.on_next_clicked),
            ("Save", Gtk.STOCK_SAVE, None, None,
                    _("Save this pedigree"), self.on_save_clicked),
            ##("Mail", "email", None, None,
            ##        _("Email this pedigree"), self.on_mail_clicked),
            ("Preview", Gtk.STOCK_PRINT_PREVIEW, None, None,
                    _("View this pedigree"), self.on_preview_clicked),
            ("Print", Gtk.STOCK_PRINT, None, None,
                    _("Print this pedigree"), self.on_print_clicked),
            ("Close", Gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_dialog)
            ))
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget("/Toolbar")
        vbox.pack_start(toolbar, False, False, 0)

        self._home_pedigree_button = uimanager.get_widget("/Toolbar/Home")
        self._previous_pedigree_button = uimanager.get_widget("/Toolbar/Previous")
        self._next_pedigree_button = uimanager.get_widget("/Toolbar/Next")

        self.table = table = Gtk.Table(20, 7)
        table.set_size_request(-1, 340)
        table.set_margin_top(8)
        table.set_margin_bottom(8)
        table.set_margin_start(4)
        table.set_margin_end(4)

        image = Gtk.Image.new_from_stock(Gtk.STOCK_GO_BACK, Gtk.IconSize.BUTTON)
        self.buttonprev = Gtk.Button()
        self.buttonprev.add(image)
        self.buttonprev.set_relief(Gtk.ReliefStyle.NONE)
        self.buttonprev.connect("clicked", self.on_navbutton_clicked, PREVIOUS)
        table.attach(self.buttonprev, 0, 1, 7, 8, 0, 0)
        image = Gtk.Image.new_from_stock(Gtk.STOCK_GO_FORWARD, Gtk.IconSize.BUTTON)
        self.buttonnextsire = Gtk.Button()
        self.buttonnextsire.add(image)
        self.buttonnextsire.set_relief(Gtk.ReliefStyle.NONE)
        self.buttonnextsire.connect("clicked", self.on_navbutton_clicked, NEXT_SIRE)
        table.attach(self.buttonnextsire, 8, 9, 3, 4, 0, 0)
        image = Gtk.Image.new_from_stock(Gtk.STOCK_GO_FORWARD, Gtk.IconSize.BUTTON)
        self.buttonnextdam = Gtk.Button()
        self.buttonnextdam.add(image)
        self.buttonnextdam.set_relief(Gtk.ReliefStyle.NONE)
        self.buttonnextdam.connect("clicked", self.on_navbutton_clicked, NEXT_DAM)
        table.attach(self.buttonnextdam, 8, 9, 11, 12, 0, 0)

        vbox.pack_start(table, False, False, 0)
        self.add(vbox)

    def _get_pedigree_table(self):
        return self.table

    def on_close_dialog(self, widget, event=None):
        self.destroy()
        self.pedigree.draw_cb = None
        return False

    def on_navbutton_clicked(self, widget, nav):
        if nav == PREVIOUS:
            pigeon = self._previous_pigeons.pop()
        else:
            self._previous_pigeons.append(self._current_pigeon)
            pigeon = self._current_pigeon.sire if nav == NEXT_SIRE else self._current_pigeon.dam

        self._current_pigeon = pigeon
        self.pedigree.draw_pedigree(self._get_pedigree_table(), pigeon, True)

    def on_pedigree_draw(self):
        can_prev = self._current_pigeon != self.pigeon
        self.buttonprev.set_sensitive(can_prev)

        can_next_sire = self._current_pigeon.sire is not None
        self.buttonnextsire.set_sensitive(can_next_sire)
        can_next_dam = self._current_pigeon.dam is not None
        self.buttonnextdam.set_sensitive(can_next_dam)

    def on_mail_clicked(self, widget):
        #TODO: disabled for now. Remove?
        ##self.do_operation(const.MAIL)
        ##pedigree = os.path.join(const.TEMPDIR, self.pdfname)
        ##maildialog.MailDialog(self, pedigree)
        pass

    def on_home_clicked(self, widget):
        self.set_pigeon(self._original_pigeon)

    def on_previous_clicked(self, widget):
        new_pigeon = self._treeview.get_pigeon_at_path(self._current_pigeon_path - 1)
        self.set_pigeon(new_pigeon)

    def on_next_clicked(self, widget):
        new_pigeon = self._treeview.get_pigeon_at_path(self._current_pigeon_path + 1)
        self.set_pigeon(new_pigeon)

    def on_save_clicked(self, widget):
        chooser = PdfSaver(self, self.pdfname)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            save_path = chooser.get_filename()
            self.do_operation(PRINT_ACTION_EXPORT, save_path)
        chooser.destroy()

    def on_preview_clicked(self, widget):
        self.do_operation(PRINT_ACTION_PREVIEW)

    def on_print_clicked(self, widget):
        self.do_operation(PRINT_ACTION_DIALOG)

    def do_operation(self, print_action, save_path=None):
        userinfo = common.get_own_address()
        if not tools.check_user_info(self, userinfo):
            return

        # Show a message to the user if the original image is not found and
        # can't be shown on the pedigree
        if config.get("printing.pedigree-image") and self.pigeon.main_image is not None:
            if not os.path.exists(self.pigeon.main_image.path):
                msg = (_("Cannot find image '%s'"),
                       _("You need to edit the pigeon and select the correct "
                         "path or restore the original image on your computer."),
                       "")
                # In some very old versions, an empty image was stored as an
                # empty string instead of None. Don't show this message in cases
                # like this ofcourse.
                if not self.pigeon.main_image.path == "":
                    InfoDialog(msg, self, self.pigeon.main_image.path)

        pedigree_report, pedigree_report_options = get_pedigree()
        psize = common.get_pagesize_from_opts()
        opts = pedigree_report_options(psize, print_action=print_action, filename=save_path, parent=self)
        try:
            report(pedigree_report, opts, self.pigeon, userinfo)
        except ReportError as exc:
            ErrorDialog((exc.value.split("\n")[0],
                         _("You probably don't have write permissions on this folder."),
                         _("Error"))
                        )
