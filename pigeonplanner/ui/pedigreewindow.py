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


import os.path

import gtk

import const
import common
import printing
from ui import tools
from ui import maildialog
from translation import gettext as _


class PedigreeWindow(gtk.Window):
    ui = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""
    def __init__(self, parent, database, options, parser, pedigree, pigeon):
        gtk.Window.__init__(self)
        self.connect('delete-event', self.on_close_dialog)
        self.set_modal(True)
        self.resize(960, 600)
        self.set_transient_for(parent)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_skip_taskbar_hint(True)

        self.database = database
        self.options = options
        self.parser = parser
        self.pigeon = pigeon
        ring, year = pigeon.get_band()
        self.pdfname = "%s_%s_%s.pdf" % (_("Pedigree"), ring, year)
        self._build_ui()
        pedigree.draw_pedigree(self._get_pedigree_tables(), pigeon, True)

        name = pigeon.get_name()
        if name:
            name = ", " + name
        title = "%s: %s%s - %s" % (_("Pedigree"), pigeon.get_band_string(True),
                                   name, pigeon.get_sex_string())
        self.set_title(title)
        self.show_all()

    def _build_ui(self):
        vbox = gtk.VBox(False, 8)

        actiongroup = gtk.ActionGroup("PedigreeWindowActions")
        actiongroup.add_actions((
            ("Save", gtk.STOCK_SAVE, None, None,
                    _("Save this pedigree"), self.on_save_clicked),
            ##("Mail", 'email', None, None,
            ##        _("Email this pedigree"), self.on_mail_clicked),
            ("Preview", gtk.STOCK_PRINT_PREVIEW, None, None,
                    _("View this pedigree"), self.on_preview_clicked),
            ("Print", gtk.STOCK_PRINT, None, None,
                    _("Print this pedigree"), self.on_print_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_dialog)
           ))
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        toolbar = uimanager.get_widget('/Toolbar')
        vbox.pack_start(toolbar, False, False)

        self.notebook = notebook = gtk.Notebook()
        notebook.append_page(*self._create_notebook_page(0))
        notebook.append_page(*self._create_notebook_page(1))
        vbox.pack_start(notebook)
        self.add(vbox)

    def _create_notebook_page(self, num):
        labeltext = _("Sire") if num == 0 else _("Dam")
        imagename = "symbol_male.png" if num == 0 else "symbol_female.png"

        image = gtk.image_new_from_file(os.path.join(const.IMAGEDIR, imagename))
        label = gtk.Label(labeltext)
        hbox = gtk.HBox()
        hbox.pack_start(image, False)
        hbox.pack_start(label, False)
        hbox.show_all()

        table = gtk.Table(20, 7)
        alignment = gtk.Alignment(.5, .5)
        alignment.set_padding(4, 4, 8, 8)
        alignment.add(table)

        return alignment, hbox

    def _get_pedigree_tables(self):
        return [self.notebook.get_nth_page(x).get_child() for x in (0, 1)]

    def on_close_dialog(self, widget, event=None):
        self.destroy()

    def on_mail_clicked(self, widget):
        self.do_operation(const.MAIL)
        pedigree = os.path.join(const.TEMPDIR, self.pdfname)
        maildialog.MailDialog(self, self.database, pedigree)

    def on_save_clicked(self, widget):
        self.do_operation(const.SAVE)

    def on_preview_clicked(self, widget):
        self.do_operation(const.PREVIEW)

    def on_print_clicked(self, widget):
        self.do_operation(const.PRINT)

    def do_operation(self, op):
        userinfo = common.get_own_address(self.database)
        if not tools.check_user_info(self, self.database, userinfo['name']):
            return

        printing.PrintPedigree(self, self.pigeon, userinfo,
                               self.options, op, self.pdfname, self.parser)

