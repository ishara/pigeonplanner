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

from gi.repository import Gtk
from gi.repository import Gdk

from pigeonplanner import main
from pigeonplanner.core import enums
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.database.models import Pigeon, Status, Result, Breeding


class RemovePigeonDialog(Gtk.MessageDialog):
    RESPONSE_CANCEL = 1
    RESPONSE_REMOVE = 2
    RESPONSE_HIDE = 3

    def __init__(self, parent, multiple):
        message = _("Remove selected pigeons?") if multiple else _("Remove selected pigeon?")
        button_hide_label = _("Hide pigeons") if multiple else _("Hide pigeon")
        Gtk.MessageDialog.__init__(self, parent=parent,
                                   flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   type=Gtk.MessageType.WARNING,
                                   message_format=message)
        self.set_transient_for(parent)
        secondary_1 = _("Remove with data will permanently delete the pigeon with all its "
                        "data like pedigree, results and breeding details.")
        secondary_2 = _("Hide the pigeon to keep it in the pedigrees.")
        self.format_secondary_text("%s\n\n%s" % (secondary_1, secondary_2))

        button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        button_cancel.connect("clicked", self.on_button_cancel_clicked)
        button_remove = Gtk.Button(label=_("Remove with data"))
        button_remove.connect("clicked", self.on_button_remove_clicked)
        button_remove.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON))
        button_hide = Gtk.Button(label=button_hide_label)
        button_hide.connect("clicked", self.on_button_hide_clicked)
        button_hide.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON))

        action_area = self.get_action_area()
        action_area.add(button_cancel)
        action_area.add(button_remove)
        action_area.add(button_hide)

        self.show_all()

    def on_button_cancel_clicked(self, _widget):
        self.response(self.RESPONSE_CANCEL)

    def on_button_remove_clicked(self, _widget):
        self.response(self.RESPONSE_REMOVE)

    def on_button_hide_clicked(self, _widget):
        self.response(self.RESPONSE_HIDE)


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.set_transient_for(parent)

        self.set_program_name(const.NAME)
        self.set_version(const.VERSION)
        self.set_copyright(const.COPYRIGHT)
        self.set_comments(const.DESCRIPTION)
        self.set_website(const.WEBSITE)
        self.set_website_label("Pigeon Planner website")
        self.set_authors(const.AUTHORS)
        self.set_artists(const.ARTISTS)
        self.set_translator_credits(_("translator-credits"))
        self.set_license_type(Gtk.License.GPL_3_0)

        self.run()
        self.destroy()


class InformationDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, _("General information"), parent,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            ("gtk-close", Gtk.ResponseType.CLOSE))
        self.set_default_response(Gtk.ResponseType.CLOSE)
        self.resize(440, 380)

        treeview = Gtk.TreeView()
        treeview.set_headers_visible(False)
        selection = treeview.get_selection()
        selection.set_select_function(self._select_func)
        liststore = Gtk.ListStore(str, str, str)
        columns = ["Item", "Value"]
        for index, column in enumerate(columns):
            textrenderer = Gtk.CellRendererText()
            tvcolumn = Gtk.TreeViewColumn(column, textrenderer, markup=index, background=2)
            tvcolumn.set_sort_column_id(index)
            treeview.append_column(tvcolumn)
        treeview.set_model(liststore)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(treeview)
        self.vbox.pack_start(sw, True, True, 0)
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

    # noinspection PyMethodMayBeStatic
    def get_versions(self):
        operatingsystem, distribution = main.get_operating_system()
        return (("Pigeon Planner", str(const.VERSION)),
                ("Python", str(sys.version).replace("\n", "")),
                ("LANG", os.environ.get("LANG", "")),
                ("OS", operatingsystem),
                ("Distribution", distribution))

    def get_data(self):
        total, cocks, hens, ybirds, unknown = common.count_active_pigeons()
        data = [
            (_("Number of pigeons"), str(total)),
            ("    %s" % _("Cocks"), "%s\t(%s %%)" % (cocks, self.get_percentage(cocks, total))),
            ("    %s" % _("Hens"), "%s\t(%s %%)" % (hens, self.get_percentage(hens, total))),
            ("    %s" % _("Young birds"), "%s\t(%s %%)" % (ybirds, self.get_percentage(ybirds, total))),
            ("    %s" % _("Unknown"), "%s\t(%s %%)" % (unknown, self.get_percentage(unknown, total)))
        ]
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

    # noinspection PyMethodMayBeStatic
    def get_percentage(self, value, total):
        if total == 0:
            return "0"
        return "%.2f" % ((value / float(total)) * 100)

    # noinspection PyMethodMayBeStatic
    def _select_func(self, _selection, _model, _path, _is_selected, _data=None):
        return False


class PigeonListDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, _("Search a pigeon"), parent,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_modal(True)
        self.set_skip_taskbar_hint(True)
        self.resize(400, 400)
        self.buttonadd = self.add_button(Gtk.STOCK_ADD, Gtk.ResponseType.APPLY)
        self.buttonadd.set_sensitive(False)

        self._liststore = Gtk.ListStore(object, str, str, str)
        modelfilter = self._liststore.filter_new()
        modelfilter.set_visible_func(self._visible_func)
        self._treeview = Gtk.TreeView(modelfilter)
        self._treeview.connect("button-press-event", self.on_treeview_press)
        columns = (_("Band no."), _("Year"), _("Name"))
        for index, column in enumerate(columns):
            textrenderer = Gtk.CellRendererText()
            tvcolumn = Gtk.TreeViewColumn(column, textrenderer, text=index+1)
            tvcolumn.set_sort_column_id(index+1)
            tvcolumn.set_resizable(True)
            self._treeview.append_column(tvcolumn)
        self._selection = self._treeview.get_selection()
        self._selection.connect("changed", self.on_selection_changed)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self._treeview)

        frame = Gtk.Frame()
        frame.add(sw)
        self.vbox.pack_start(frame, True, True, 0)

        self.checkbutton = Gtk.CheckButton(_("Show all pigeons"))
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

        if event.button == Gdk.BUTTON_PRIMARY and event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            self.response(Gtk.ResponseType.APPLY)

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
        self._liststore.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self._liststore.set_sort_column_id(2, Gtk.SortType.ASCENDING)
        self._treeview.get_selection().select_path(0)

    def get_selected(self):
        model, rowiter = self._treeview.get_selection().get_selected()
        if not rowiter:
            return
        return model[rowiter][0]

    def _visible_func(self, model, rowiter, _data=None):
        if self.checkbutton.get_active():
            # Show everything
            return True
        # Only show visible pigeons
        pigeon = model.get_value(rowiter, 0)
        return pigeon.visible
