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
import os.path
import sys

import gtk
import gtk.gdk

from pigeonplanner import main
from pigeonplanner import messages
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.messagedialog import InfoDialog
from pigeonplanner.core import enums
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import backup
from pigeonplanner.database.models import Pigeon, Status, Result, Breeding


class RemovePigeonDialog(gtk.MessageDialog):
    RESPONSE_CANCEL = 1
    RESPONSE_REMOVE = 2
    RESPONSE_HIDE = 3

    def __init__(self, parent, multiple):
        message = _("Remove selected pigeons?") if multiple else _("Remove selected pigeon?")
        button_hide_label = _("Hide pigeons") if multiple else _("Hide pigeon")
        gtk.MessageDialog.__init__(self, parent=parent,
                                   flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_WARNING,
                                   message_format=message)
        self.set_transient_for(parent)
        secondary_1 = _("Remove with data will permanently delete the pigeon with all its "
                        "data like pedigree, results and breeding details.")
        secondary_2 = _("Hide the pigeon to keep it in the pedigrees.")
        self.format_secondary_text("%s\n\n%s" % (secondary_1, secondary_2))

        button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_cancel.connect("clicked", self.on_button_cancel_clicked)
        button_remove = gtk.Button(label=_("Remove with data"))
        button_remove.connect("clicked", self.on_button_remove_clicked)
        button_remove.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        button_hide = gtk.Button(label=button_hide_label)
        button_hide.connect("clicked", self.on_button_hide_clicked)
        button_hide.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))

        action_area = self.get_action_area()
        action_area.add(button_cancel)
        action_area.add(button_remove)
        action_area.add(button_hide)

        self.show_all()

    def on_button_cancel_clicked(self, widget):
        self.response(self.RESPONSE_CANCEL)

    def on_button_remove_clicked(self, widget):
        self.response(self.RESPONSE_REMOVE)

    def on_button_hide_clicked(self, widget):
        self.response(self.RESPONSE_HIDE)


class AboutDialog(gtk.AboutDialog):
    def __init__(self, parent):
        gtk.AboutDialog.__init__(self)

        gtk.about_dialog_set_url_hook(common.url_hook)
        gtk.about_dialog_set_email_hook(common.email_hook)

        self.set_transient_for(parent)
        self.set_icon_from_file(os.path.join(const.IMAGEDIR, "icon_logo.png"))
        self.set_modal(True)
        self.set_property("skip-taskbar-hint", True)

        self.set_name(const.NAME)
        self.set_version(const.VERSION)
        self.set_copyright(const.COPYRIGHT)
        self.set_comments(const.DESCRIPTION)
        self.set_website(const.WEBSITE)
        self.set_website_label("Pigeon Planner website")
        self.set_authors(const.AUTHORS)
        self.set_artists(const.ARTISTS)
        self.set_translator_credits(_("translator-credits"))
        self.set_license(const.LICENSE)
        self.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(
                        os.path.join(const.IMAGEDIR, "icon_logo.png"), 80, 80))
        self.run()
        self.destroy()


class InformationDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _("General information"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-close", gtk.RESPONSE_CLOSE))
        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.resize(440, 380)

        treeview = gtk.TreeView()
        treeview.set_headers_visible(False)
        selection = treeview.get_selection()
        selection.set_select_function(self._select_func)
        liststore = gtk.ListStore(str, str, str)
        columns = ["Item", "Value"]
        for index, column in enumerate(columns):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(column, textrenderer, markup=index, background=2)
            tvcolumn.set_sort_column_id(index)
            treeview.append_column(tvcolumn)
        treeview.set_model(liststore)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(treeview)
        self.vbox.pack_start(sw)
        self.vbox.show_all()

        template = "<b>%s</b>"
        liststore.append([template % _("Technical details"), "", "#dcdcdc"])
        for item, value in self.get_versions():
            liststore.append([item, value, "#ffffff"])
        liststore.append([template % _("Data information"), "", "#dcdcdc"])
        for item, value in self.get_data():
            liststore.append([item, value, "#ffffff"])

        self.run()
        self.destroy()

    def get_versions(self):
        operatingsystem, distribution = main.get_operating_system()
        return (("Pigeon Planner", str(const.VERSION)),
                ("Python", str(sys.version).replace("\n", "")),
                ("LANG", os.environ.get("LANG", "")),
                ("OS", operatingsystem),
                ("Distribution", distribution))

    def get_data(self):
        total, cocks, hens, ybirds, unknown = common.count_active_pigeons()
        data = [(_("Number of pigeons"), str(total))]
        data.append(("    %s" % _("Cocks"),
                     "%s\t(%s %%)" % (cocks, self.get_percentage(cocks, total))))
        data.append(("    %s" % _("Hens"),
                     "%s\t(%s %%)" % (hens, self.get_percentage(hens, total))))
        data.append(("    %s" % _("Young birds"),
                     "%s\t(%s %%)" % (ybirds, self.get_percentage(ybirds, total))))
        data.append(("    %s" % _("Unknown"),
                     "%s\t(%s %%)" % (unknown, self.get_percentage(unknown, total))))
        for status in range(7):
            n_status = (Status.select()
                        .join(Pigeon, on=Status.pigeon)
                        .where((Status.status_id == status) & (Pigeon.visible == True))
                        .count())
            data.append(("    %s" % enums.Status.get_string(status),
                         "%s\t(%s %%)" % (n_status, self.get_percentage(n_status, total))))
        n_results = Result.select().count()
        n_breeding = Breeding.select().count()
        data.append((_("Number of results"), str(n_results)))
        data.append((_("Number of couples"), str(n_breeding)))
        return data

    def get_percentage(self, value, total):
        if total == 0:
            return "0"
        return "%.2f" % ((value / float(total)) * 100)

    def _select_func(self, data):
        return False


class BackupDialog(gtk.Dialog):
    def __init__(self, parent, backuptype):
        gtk.Dialog.__init__(self, None, parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-close", gtk.RESPONSE_CLOSE))
        self._parent = parent

        self.set_resizable(False)
        self.set_has_separator(False)

        if backuptype == enums.Backup.create:
            self.set_title(_("Create backup"))
            label = gtk.Label(_("Choose a directory where to save the backup"))
            label.set_padding(30, 0)
            self.fcButtonCreate = filechooser.PathChooser()
            self.vbox.pack_start(label, False, True, 8)
            self.vbox.pack_start(self.fcButtonCreate, False, True, 12)

            button = gtk.Button(_("Backup"))
            button.connect("clicked", self.makebackup_clicked)
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)
            self.action_area.pack_start(button)
            self.action_area.reorder_child(button, 0)

        else:
            self.set_title(_("Restore backup"))
            text = _("Choose a Pigeon Planner backup file to restore")
            label = gtk.Label(text)
            label.set_padding(30, 0)
            text2 = _("Warning! This will overwrite the existing database!")
            label2 = gtk.Label(text2)
            label2.set_padding(30, 0)
            self.fcButtonRestore = filechooser.BackupChooser()
            self.vbox.pack_start(label, False, True, 8)
            self.vbox.pack_start(label2, False, True, 8)
            self.vbox.pack_start(self.fcButtonRestore, False, True, 12)

            button = gtk.Button(_("Restore"))
            button.connect("clicked", self.restorebackup_clicked)
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)
            self.action_area.pack_start(button)
            self.action_area.reorder_child(button, 0)

        self.show_all()

    def makebackup_clicked(self, widget):
        folder = self.fcButtonCreate.get_current_folder()
        if folder:
            if backup.make_backup(folder):
                msg = messages.MSG_BACKUP_SUCCES
            else:
                msg = messages.MSG_BACKUP_FAILED
            InfoDialog(msg, self._parent)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            if backup.restore_backup(zipfile):
                msg = messages.MSG_RESTORE_SUCCES
                InfoDialog(msg, self._parent)
                gtk.main_quit()
            else:
                msg = messages.MSG_RESTORE_FAILED
                InfoDialog(msg, self._parent)


class PigeonListDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _("Search a pigeon"), parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_modal(True)
        self.set_skip_taskbar_hint(True)
        self.resize(400, 400)
        self.buttonadd = self.add_button(gtk.STOCK_ADD, gtk.RESPONSE_APPLY)
        self.buttonadd.set_sensitive(False)

        self._liststore = gtk.ListStore(object, str, str, str)
        modelfilter = self._liststore.filter_new()
        modelfilter.set_visible_func(self._visible_func)
        self._treeview = gtk.TreeView(modelfilter)
        self._treeview.connect("button-press-event", self.on_treeview_press)
        columns = (_("Band no."), _("Year"), _("Name"))
        for index, column in enumerate(columns):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(column, textrenderer, text=index+1)
            tvcolumn.set_sort_column_id(index+1)
            tvcolumn.set_resizable(True)
            self._treeview.append_column(tvcolumn)
        self._selection = self._treeview.get_selection()
        self._selection.connect("changed", self.on_selection_changed)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self._treeview)

        frame = gtk.Frame()
        frame.add(sw)
        self.vbox.pack_start(frame, True, True, 0)

        self.checkbutton = gtk.CheckButton(_("Show all pigeons"))
        self.checkbutton.connect("toggled", lambda widget: modelfilter.refilter())
        self.vbox.pack_start(self.checkbutton, False, False, 0)
        self.show_all()

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        self.buttonadd.set_sensitive(rowiter is not None)

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return

        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.response(gtk.RESPONSE_APPLY)

    def fill_treeview(self, band_tuple=None, sex=None, year=None):
        self._liststore.clear()
        for pigeon in Pigeon.select():
            # If a band_tuple is given, exclude it
            if band_tuple is not None and band_tuple == pigeon.band_tuple:
                continue
            # If sex is given, only include these
            if sex is not None and not sex == pigeon.sex:
                continue
            # If year is given, exclude older pigeons
            if year is not None and int(year) < int(pigeon.band_year):
                continue
            self._liststore.insert(0, [pigeon, pigeon.band, pigeon.band_year, pigeon.name])
        self._liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self._liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self._treeview.get_selection().select_path(0)

    def get_selected(self):
        model, rowiter = self._treeview.get_selection().get_selected()
        if not rowiter:
            return
        return model[rowiter][0]

    def _visible_func(self, model, rowiter):
        if self.checkbutton.get_active():
            # Show everything
            return True
        # Only show visible pigeons
        pigeon = model.get_value(rowiter, 0)
        return pigeon.visible
