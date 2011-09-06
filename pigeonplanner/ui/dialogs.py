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
import gobject

import const
import common
import backup
import messages
from ui import filechooser
from ui.widgets import comboboxes


class MessageDialog(gtk.MessageDialog):
    def __init__(self, msgtype, data, parent=None, extra=None):
        """
        Display a message dialog.

        @param parent: The parent window
        @param msgtype: The sort of dialog
        @param data: Tuple of primary text, secondary text and dialog title
        @param extra: Extra data to use with a string formatter
        """

        head, text, title = data
        if extra:
            head = head % extra

        if msgtype == const.ERROR:
            msgtype = gtk.MESSAGE_ERROR
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)
        elif msgtype == const.WARNING:
            msgtype = gtk.MESSAGE_WARNING
            buttons = (gtk.STOCK_NO, gtk.RESPONSE_NO,
                       gtk.STOCK_YES, gtk.RESPONSE_YES)
        elif msgtype == const.QUESTION:
            msgtype = gtk.MESSAGE_QUESTION
            buttons = (gtk.STOCK_NO, gtk.RESPONSE_NO,
                       gtk.STOCK_YES, gtk.RESPONSE_YES)
            title = head + " - Pigeon Planner"
        elif msgtype == const.INFO:
            msgtype = gtk.MESSAGE_INFO
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)

        gtk.MessageDialog.__init__(self, parent, 0, msgtype, message_format=head)
        self.format_secondary_text(text)
        self.set_title(title)
        self.add_buttons(*buttons)

        response = self.run()
        self.yes = response == gtk.RESPONSE_YES
        self.destroy()


class AboutDialog(gtk.AboutDialog):
    def __init__(self, parent):
        gtk.AboutDialog.__init__(self)

        gtk.about_dialog_set_url_hook(common.url_hook)
        gtk.about_dialog_set_email_hook(common.email_hook)

        self.set_transient_for(parent)
        self.set_icon_from_file(os.path.join(const.IMAGEDIR, 'icon_logo.png'))
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
        self.set_translator_credits(_('translator-credits'))
        self.set_license(const.LICENSE)
        self.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(
                        os.path.join(const.IMAGEDIR, 'icon_logo.png'), 80, 80))
        self.run()
        self.destroy()


class InfoDialog(gtk.Dialog):
    def __init__(self, parent, database):
        gtk.Dialog.__init__(self, _("General information"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-close", gtk.RESPONSE_CLOSE))
        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.resize(440, 380)
        self.database = database

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
        liststore.append([template %_("Technical details"), "", "#dcdcdc"])
        for item, value in self.get_versions():
            liststore.append([item, value, "#ffffff"])
        liststore.append([template %_("Data information"), "", "#dcdcdc"])
        for item, value in self.get_data():
            liststore.append([item, value, "#ffffff"])

        self.run()
        self.destroy()

    def get_versions(self):
        operatingsystem, distribution = common.get_operating_system()
        return (("Pigeon Planner", str(const.VERSION)),
                ("Python", str(sys.version).replace('\n','')),
                ("LANG", os.environ.get('LANG','')),
                ("OS", operatingsystem),
                ("Distribution", distribution))

    def get_data(self):
        total, cocks, hens, ybirds = common.count_active_pigeons(self.database)
        return ((_("Number of pigeons"), total),
                (_("Number of cocks"), "%s (%s %%)"
                                %(cocks, self.get_percentage(cocks, total))),
                (_("Number of hens"), "%s (%s %%)"
                                %(hens, self.get_percentage(hens, total))),
                (_("Number of young birds"), "%s (%s %%)"
                                %(ybirds, self.get_percentage(ybirds, total))),
                (_("Number of results"),
                                    len(self.database.get_all_results())))

    def get_percentage(self, value, total):
        if total == 0: return "0"
        return "%.2f" % ((value/float(total))*100)

    def _select_func(self, data):
        return False


class BackupDialog(gtk.Dialog):
    def __init__(self, parent, backuptype):
        gtk.Dialog.__init__(self, None, parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-close", gtk.RESPONSE_CLOSE))
        self.par = parent

        self.set_resizable(False)
        self.set_has_separator(False)

        if backuptype == const.CREATE:
            self.set_title(_("Create backup"))
            label = gtk.Label(_("Choose a directory where to save the backup"))
            label.set_padding(30, 0)
            self.fcButtonCreate = filechooser.BackupSaver()
            self.vbox.pack_start(label, False, True, 8)
            self.vbox.pack_start(self.fcButtonCreate, False, True, 12)

            button = gtk.Button(_("Backup"))
            button.connect('clicked', self.makebackup_clicked)
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
            button.connect('clicked', self.restorebackup_clicked)
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
            MessageDialog(const.INFO, msg, self.par)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            if backup.restore_backup(zipfile):
                msg = messages.MSG_RESTORE_SUCCES
            else:
                msg = messages.MSG_RESTORE_FAILED
            MessageDialog(const.INFO, msg, self.par)


class FilterDialog(gtk.Dialog):
    __gsignals__ = {'apply-clicked': (gobject.SIGNAL_RUN_LAST,
                                      None, ()),
                    'clear-clicked': (gobject.SIGNAL_RUN_LAST,
                                      None, ()),
                    }
    def __init__(self, parent, title):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        self.filters = []
        self.sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        btnapply = gtk.Button(stock=gtk.STOCK_APPLY)
        btnapply.connect("clicked", self.on_btnapply_clicked)
        btnclear = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        btnclear.set_image(image)
        btnclear.connect("clicked", self.on_btnclear_clicked)
        hbox = gtk.HBox()
        hbox.pack_start(btnapply, False, False)
        hbox.pack_start(btnclear, False, False, 4)
        self.vbox.pack_end(hbox, False, False)

    # Callbacks
    def on_dialog_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE or \
           response_id == gtk.RESPONSE_DELETE_EVENT:
            self._clear_filters()
            self.emit('clear-clicked')
            dialog.destroy()

    def on_btnclear_clicked(self, widget):
        self._clear_filters()
        self.emit('clear-clicked')

    def on_btnapply_clicked(self, widget):
        self.emit('apply-clicked')

    def on_spinbutton_changed(self, widget, value, text):
        if widget.get_value_as_int() == value:
            widget.set_text(text)

    # Public methods
    def run(self):
        self.connect('response', self.on_dialog_response)
        self.show_all()

    def get_filters(self):
        return self.filters

    def add_custom(self, name, label, widget, get_data_func):
        widget.get_data = get_data_func
        self._add_filter(name, label, widget)

    def add_combobox(self, name, label, data):
        combobox = gtk.combo_box_new_text()
        combobox.get_data = combobox.get_active_text
        comboboxes.fill_combobox(combobox, data)
        self._add_filter(name, label, combobox)

    def add_spinbutton(self, name, label, lowest=0, lowest_text=None):
        adj = gtk.Adjustment(lowest, lowest, 4000, 1, 10, 0)
        spinbutton = gtk.SpinButton(adj, 4)
        spinbutton.get_data = spinbutton.get_value_as_int
        if lowest_text:
            spinbutton.set_text(lowest_text)
            spinbutton.connect('changed', self.on_spinbutton_changed, lowest,
                               lowest_text)
        self._add_filter(name, label, spinbutton)

    # Internal methods
    def _add_filter(self, name, label, widget):
        self.sizegroup.add_widget(widget)
        check = gtk.CheckButton(_("Only show:"))
        hbox = gtk.HBox()
        hbox.pack_start(check, False, True, 8)
        hbox.pack_start(widget, True, True)
        align = gtk.Alignment()
        align.set_padding(0, 0, 4, 0)
        align.add(hbox)
        frame = gtk.Frame(label)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.add(align)
        self.vbox.pack_start(frame, False, False, 0)
        self.filters.append((name, check, widget))

    def _clear_filters(self):
        for name, checkbox, widget in self.filters:
            checkbox.set_active(False)


class SearchDialog(gtk.Dialog):
    __gsignals__ = {'search': (gobject.SIGNAL_RUN_LAST, None, (object, str)),
                    'clear': (gobject.SIGNAL_RUN_LAST, None, ()),
                    }
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _("Search a pigeon"), parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        self.button = gtk.Button(stock=gtk.STOCK_FIND)
        self.button.set_sensitive(False)
        self.button.connect('clicked', self.on_button_clicked)
        self.action_area.pack_start(self.button)

        label = gtk.Label(_("Search for:"))
        self.entry = gtk.Entry()
        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('icon-press', self.on_entryicon_press)
        hbox = gtk.HBox(False, 8)
        hbox.pack_start(label, False, True, 0)
        hbox.pack_start(self.entry, False, True, 0)

        label = gtk.Label(_("Search in:"))
        check1 = gtk.CheckButton(_("Band numbers"))
        check2 = gtk.CheckButton(_("Names"))
        table = gtk.Table(2, 2)
        table.set_col_spacings(12)
        table.attach(label, 0, 1, 0, 1, gtk.FILL)
        table.attach(check1, 1, 2, 0, 1)
        table.attach(check2, 1, 2, 1, 2)
        self.results = [check1, check2]

        self.vbox.set_spacing(8)
        self.vbox.pack_start(hbox, False, False, 0)
        self.vbox.pack_start(table, False, True, 0)
        self.vbox.show_all()

    def on_entry_changed(self, widget):
        has_text = widget.get_text() != ''
        icon = gtk.STOCK_CLEAR if has_text else None
        self.button.set_sensitive(has_text)
        widget.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, icon)

    def on_entryicon_press(self, widget, icon, event):
        self.emit('clear')
        widget.set_text('')
        widget.grab_focus()

    def on_button_clicked(self, widget):
        self.emit('search', self.results, self.entry.get_text())


class MedicationRemoveDialog(gtk.Dialog):
    def __init__(self, parent, multiple=False):
        gtk.Dialog.__init__(self, '', parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_NO, gtk.RESPONSE_NO,
                             gtk.STOCK_YES, gtk.RESPONSE_YES))

        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        text = _("Removing the selected medication entry")
        self.set_title(text + " - Pigeon Planner")
        self.check = gtk.CheckButton(_("Remove this entry for all pigeons?"))
        label1 = gtk.Label()
        label1.set_markup("<b>%s</b>" %text)
        label1.set_alignment(0.0, 0.5)
        label2 = gtk.Label(_("Are you sure?"))
        label2.set_alignment(0.0, 0.5)
        vbox = gtk.VBox()
        vbox.pack_start(label1, False, False, 8)
        vbox.pack_start(label2, False, False, 8)
        if multiple:
            vbox.pack_start(self.check, False, False, 12)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        hbox = gtk.HBox()
        hbox.pack_start(image, False, False, 12)
        hbox.pack_start(vbox, False, False, 12)
        self.vbox.pack_start(hbox, False, False)
        self.vbox.show_all()


class PigeonListDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _('Search a pigeon'), parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_modal(True)
        self.set_skip_taskbar_hint(True)
        self.resize(400, 400)
        self.buttonadd = self.add_button(gtk.STOCK_ADD, gtk.RESPONSE_APPLY)
        self.buttonadd.set_sensitive(False)

        self._liststore = gtk.ListStore(object, str, str, str)
        self._treeview = gtk.TreeView(self._liststore)
        columns = (_("Band no."), _("Year"), _("Name"))
        for index, column in enumerate(columns):
            textrenderer = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(column, textrenderer, text=index+1)
            tvcolumn.set_sort_column_id(index+1)
            tvcolumn.set_resizable(True)
            self._treeview.append_column(tvcolumn)
        self._selection = self._treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self._treeview)

        frame = gtk.Frame()
        frame.add(sw)
        self.vbox.pack_start(frame)
        self.show_all()

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        self.buttonadd.set_sensitive(not rowiter is None)

    def fill_treeview(self, parser, pindex=None, sex=None, year=None):
        self._liststore.clear()
        for pigeon in parser.pigeons.values():
            # If pindex is given, exclude it
            if pindex is not None and pindex == pigeon.get_pindex():
                continue
            # If sex is given, only include these
            if sex is not None and not sex == int(pigeon.get_sex()):
                continue
            # If year is given, exclude older pigeons
            if year is not None and int(year) < int(pigeon.year):
                continue
            self._liststore.insert(0, [pigeon, pigeon.ring, pigeon.year,
                                       pigeon.get_name()])
        self._liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self._liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self._treeview.get_selection().select_path(0)

    def get_selected(self):
        model, rowiter = self._treeview.get_selection().get_selected()
        if not rowiter: return
        return model[rowiter][0]

