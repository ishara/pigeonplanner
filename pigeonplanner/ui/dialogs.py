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


import os.path

import gtk

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import checks
from pigeonplanner import backup
from pigeonplanner import messages
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.ui.widgets import filefilters


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
            head = head %extra

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
                                                os.path.join(const.IMAGEDIR,
                                                             'icon_logo.png'),
                                                80, 80))

        result = self.run()
        self.destroy()


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
            title = _("Select a directory")
            self.fcButtonCreate = gtk.FileChooserButton(title)
            self.fcButtonCreate.set_action(
                                        gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

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
            title = _("Select a valid backup file")
            self.fcButtonRestore = gtk.FileChooserButton(title)
            self.fcButtonRestore.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            self.fcButtonRestore.add_filter(filefilters.BackupFilter())

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


class EditPedigreeDialog(gtk.Dialog):
    def __init__(self, parent, main, pindex, sex, kinfo, draw):
        gtk.Dialog.__init__(self, _("Insert a pigeon"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_property("skip-taskbar-hint", True)
        self.connect('response', self.on_dialog_response)

        self.main = main
        self.draw = draw
        self.pindex = pindex
        self.sex = sex
        self.kinfo = kinfo
        if kinfo is not None:
            self.kindex = kinfo[0]

        table = gtk.Table(2, 2)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        table.set_homogeneous(False)
        self.vbox.pack_start(table, False, True)

        label = gtk.Label(_("Band no."))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 0, 1)

        hbox = gtk.HBox()
        self.entryRing = gtk.Entry()
        self.entryRing.set_width_chars(15)
        self.entryRing.set_alignment(0.5)
        self.entryRing.set_activates_default(True)
        hbox.pack_start(self.entryRing, False, True)
        label = gtk.Label("/")
        hbox.pack_start(label, False, True)
        self.entryYear = gtk.Entry(4)
        self.entryYear.set_width_chars(4)
        self.entryYear.set_activates_default(True)
        hbox.pack_start(self.entryYear, False, True)
        table.attach(hbox, 1, 2, 0, 1)

        viewport = gtk.Viewport()
        vbox = gtk.VBox()
        for x in range(1, 7):
            entry = gtk.Entry(28)
            entry.set_has_frame(False)
            entry.set_activates_default(True)
            setattr(self, 'entryExtra'+str(x), entry)
            vbox.pack_start(entry)

        viewport.add(vbox)
        table.attach(viewport, 0, 2, 1, 2)

        self.vbox.show_all()

        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b = self.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_APPLY)
        b.set_property('can-default', True)
        b.set_property('has-default', True)

    def run(self, widget, ring, year, details):
        if ring and year:
            self.entryRing.set_text(ring)
            self.entryYear.set_text(year)
            self.entryExtra1.set_text(details[0])
            self.entryExtra2.set_text(details[1])
            self.entryExtra3.set_text(details[2])
            self.entryExtra4.set_text(details[3])
            self.entryExtra5.set_text(details[4])
            self.entryExtra6.set_text(details[5])

        if not self.kindex in self.main.parser.pigeons:
            data = (self.kinfo[0], self.kinfo[1], self.kinfo[2], self.kinfo[3],
                    0, 1, '', '', '', '', '', '', '', '', '',
                    self.kinfo[4], self.kinfo[5], self.kinfo[6],
                    self.kinfo[7], self.kinfo[8], self.kinfo[9])
            self.main.database.insert_into_table(self.main.database.PIGEONS,
                                                 data)

        self.entryRing.grab_focus()
        self.entryRing.set_position(-1)

        self.show_all()

    def on_dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_APPLY:
            self.save_pigeon_data()

        self.destroy()

    def save_pigeon_data(self):
        ring = self.entryRing.get_text()
        year = self.entryYear.get_text()

        try:
            checks.check_ring_entry(ring, year)
        except checks.InvalidInputError, msg:
            MessageDialog(const.ERROR, msg.value, self)
            return False

        pindex = common.get_pindex_from_band(ring, year)

        if self.pindex and self.pindex in self.main.parser.pigeons:
            data = (pindex, ring, year,
                    self.entryExtra1.get_text(),
                    self.entryExtra2.get_text(),
                    self.entryExtra3.get_text(),
                    self.entryExtra4.get_text(),
                    self.entryExtra5.get_text(),
                    self.entryExtra6.get_text(),
                    self.pindex)
            self.edit_pigeon(data)
        else:
            data = (pindex, ring, year, self.sex , 0, 1,
                    '', '', '', '', '', '', '', '', '',
                    self.entryExtra1.get_text(),
                    self.entryExtra2.get_text(),
                    self.entryExtra3.get_text(),
                    self.entryExtra4.get_text(),
                    self.entryExtra5.get_text(),
                    self.entryExtra6.get_text())
            self.add_pigeon(data)

        return True

    def edit_parent(self, kindex, band, year, sex):
        if sex == '0':
            self.main.database.update_table(self.main.database.PIGEONS,
                                            (band, year, kindex), 12, 1)
        else:
            self.main.database.update_table(self.main.database.PIGEONS,
                                            (band, year, kindex), 14, 1)

    def edit_pigeon(self, data):
        self.main.database.update_pedigree_pigeon(data)
        self.edit_parent(self.kindex, data[1], data[2], self.sex)

        self.redraw_pedigree()

    def add_pigeon(self, data):
        self.main.database.insert_into_table(self.main.database.PIGEONS, data)
        self.edit_parent(self.kindex, data[1], data[2], self.sex)

        self.redraw_pedigree()

    def remove_pigeon(self, widget, pindex):
        self.main.database.delete_from_table(self.main.database.PIGEONS, pindex)
        self.edit_parent(self.kindex, '', '', self.sex)

        self.redraw_pedigree()

    def clear_box(self, widget=None):
        self.edit_parent(self.kindex, '', '', self.sex)

        self.redraw_pedigree()

    def redraw_pedigree(self):
        self.main.parser.get_pigeons()
        model, paths = self.main.selection.get_selected_rows()
        self.main.selection.unselect_path(paths[0])
        self.main.selection.select_path(paths[0])

        mainpindex = self.main.get_main_ring()[0]
        self.draw.draw_pedigree(self.main.parser.pigeons,
                                [self.draw.pedigree.tableSire,
                                 self.draw.pedigree.tableDam],
                                mainpindex, True)


class FilterDialog(gtk.Dialog):
    def __init__(self, parent, title, fill_treeview_cb):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        self.fill_treeview_cb = fill_treeview_cb
        self.checkboxes = []
        self.active = False
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

    def run(self):
        """
        Implement a non-blocking dialog so the user can browse through
        the pigeons while seeing the filters.
        """

        self.connect('response', self.on_dialog_response)
        self.show_all()

    def on_dialog_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE or \
           response_id == gtk.RESPONSE_DELETE_EVENT:
            self.clear_filters()
            dialog.destroy()

    def on_btnclear_clicked(self, widget):
        self.clear_filters()
        self.active = False

    def on_btnapply_clicked(self, widget):
        self.fill_treeview_cb(filter_active=True)
        self.active = True

    def on_spinbutton_changed(self, widget, value, text):
        if widget.get_value_as_int() == value:
            widget.set_text(text)

    def clear_filters(self):
        for checkbox in self.checkboxes:
            checkbox.set_active(False)

        if self.active:
            self.fill_treeview_cb()

    def __add_filter(self, widget, label):
        self.sizegroup.add_widget(widget)
        check = gtk.CheckButton(_("Only show:"))
        hbox = gtk.HBox()
        hbox.pack_start(check, False, True, 8)
        hbox.pack_start(widget, True, True)
        align = gtk.Alignment()
        align.set_padding(0, 0, 12, 0)
        align.add(hbox)
        frame = gtk.Frame(label)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.add(align)
        self.vbox.pack_start(frame, False, False, 8)
        self.checkboxes.append(check)

        return check

    def add_filter_custom(self, label, widget):
        return self.__add_filter(widget, label)

    def add_filter_combobox(self, label, items):
        combobox = gtk.combo_box_new_text()
        comboboxes.fill_combobox(combobox, items)

        return self.__add_filter(combobox, label), combobox

    def add_filter_spinbutton(self, label, lowest=0, lowest_text=None):
        adj = gtk.Adjustment(lowest, lowest, 4000, 1, 10, 0)
        spinbutton = gtk.SpinButton(adj, 4)
        if lowest_text:
            spinbutton.set_text(lowest_text)
            spinbutton.connect('changed', self.on_spinbutton_changed, lowest,
                               lowest_text)

        return self.__add_filter(spinbutton, label), spinbutton


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

