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
import gtk.gdk
import gobject

import const
import backup
import messages


uistring = '''
<ui>
   <menubar name="MenuBar">
      <menu action="FileMenu">
         <menuitem action="Add"/>
         <menuitem action="Addrange"/>
         <separator/>
         <menuitem action="Tools"/>
         <menuitem action="Album"/>
         <menuitem action="Log"/>
         <separator/>
         <menu action="PrintMenu">
            <menuitem action="PrintPedigree"/>
            <menuitem action="PrintBlank"/>
         </menu>
         <separator/>
         <menu action="BackupMenu">
            <menuitem action="Backup"/>
            <menuitem action="Restore"/>
         </menu>
         <separator/>
         <menuitem action="Quit"/>
      </menu>
      <menu action="EditMenu">
         <menuitem action="Search"/>
         <separator/>
         <menuitem action="Preferences"/>
      </menu>
      <menu action="ViewMenu">
         <menuitem action="Filter"/>
         <separator/>
         <menuitem action="Arrows"/>
         <menuitem action="Stats"/>
         <menuitem action="Toolbar"/>
         <menuitem action="Statusbar"/>
      </menu>
      <menu action="PigeonMenu">
         <menuitem action="Edit"/>
         <menuitem action="Remove"/>
         <menuitem action="Pedigree"/>
         <menuitem action="Addresult"/>
      </menu>
      <menu action="HelpMenu">
         <menuitem action="Home"/>
         <menuitem action="Forum"/>
         <separator/>
         <menuitem action="About"/>
      </menu>
   </menubar>

   <toolbar name="Toolbar">
      <toolitem action="Add"/>
      <separator/>
      <toolitem action="Edit"/>
      <toolitem action="Remove"/>
      <toolitem action="Pedigree"/>
      <separator/>
      <toolitem action="Preferences"/>
      <toolitem action="Tools"/>
      <separator/>
      <toolitem action="About"/>
      <toolitem action="Quit"/>
   </toolbar>
</ui>
'''

photoalbumui = '''
<ui>
   <toolbar name="Toolbar">
      <toolitem action="First"/>
      <toolitem action="Prev"/>
      <toolitem action="Next"/>
      <toolitem action="Last"/>
      <separator/>
      <toolitem action="Slide"/>
      <separator/>
      <toolitem action="Screen"/>
      <separator/>
      <toolitem action="Fit"/>
      <toolitem action="In"/>
      <toolitem action="Out"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
'''

pedigreeui = '''
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <toolitem action="Mail"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
'''

resultui = '''
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <toolitem action="Mail"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Filter"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
'''

previewui = '''
<ui>
   <toolbar name="Toolbar">
      <toolitem action="First"/>
      <toolitem action="Prev"/>
      <toolitem action="Next"/>
      <toolitem action="Last"/>
      <separator/>
      <toolitem action="Fit"/>
      <toolitem action="In"/>
      <toolitem action="Out"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
'''


def get_backup_filefilter():
    backupFileFilter = gtk.FileFilter()
    backupFileFilter.set_name("PP Backups")
    backupFileFilter.add_mime_type("zip/zip")
    backupFileFilter.add_pattern("*PigeonPlannerBackup.zip")

    return backupFileFilter

def message_dialog(msgtype, data, parent=None, extra=None):
    '''
    Display a message dialog.

    @param parent: The parent window
    @param msgtype: The sort of dialog
    @param data: Tuple of primary text, secondary text and dialog title
    @param extra: Extra data to use with a string formatter
    '''

    if extra:
        head = data[0] %extra
    else:
        head = data[0]
    text = data[1]
    title = data[2]

    if msgtype == 'error':
        msgtype = gtk.MESSAGE_ERROR
        buttons = gtk.BUTTONS_OK
    elif msgtype == 'warning':
        msgtype = gtk.MESSAGE_WARNING
        buttons = gtk.BUTTONS_YES_NO
    elif msgtype == 'question':
        msgtype = gtk.MESSAGE_QUESTION
        buttons = gtk.BUTTONS_YES_NO
        title = head + " - Pigeon Planner"
    elif msgtype == 'info':
        msgtype = gtk.MESSAGE_INFO
        buttons = gtk.BUTTONS_OK

    dialog = gtk.MessageDialog(parent=parent, type=msgtype, message_format=head, buttons=buttons)
    dialog.format_secondary_text(text)
    dialog.set_title(title)
    result = dialog.run()
    if result == -9:
        dialog.destroy()
        return False
    elif result == -8:
        dialog.destroy()
        return True
    dialog.destroy()

def about_dialog(parent):
    '''
    Build and show the about dialog

    @param parent: Parent for the dialog
    '''

    dialog = gtk.AboutDialog()
    dialog.set_transient_for(parent)
    dialog.set_icon_from_file(os.path.join(const.IMAGEDIR, 'icon_logo.png'))
    dialog.set_modal(True)
    dialog.set_property("skip-taskbar-hint", True)

    dialog.set_name(const.NAME)
    dialog.set_version(const.VERSION)
    dialog.set_copyright(const.COPYRIGHT)
    dialog.set_comments(const.DESCRIPTION)
    dialog.set_website(const.WEBSITE)
    dialog.set_website_label("Pigeon Planner website")
    dialog.set_authors(const.AUTHORS)
    dialog.set_artists(const.ARTISTS)
    dialog.set_translator_credits(_('translator-credits'))
    dialog.set_license(const.LICENSE)
    dialog.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(const.IMAGEDIR, 'icon_logo.png'), 80, 80))

    result = dialog.run()
    dialog.destroy()

def set_multiple_sensitive(widgets):
    ''' 
    Set multiple widgets sensitive at once

    @param widgets: dic of widgets with booleans
    '''

    for key in widgets.keys():
        key.set_sensitive(widgets[key])

def set_multiple_visible(widgets):
    ''' 
    Set multiple widgets visible at once

    @param widgets: dic of widgets with booleans
    '''

    for key in widgets.keys():
        if widgets[key]:
            key.show()
        else:
            key.hide()

def popup_menu(event, entries):
    '''
    Make a right click menu

    @param entries: List of wanted menuentries
    '''

    menu = gtk.Menu()
    for stock_id, callback, data in entries:
        item = gtk.ImageMenuItem(stock_id)
        if data:
            item.connect("activate", callback, data)
        else:
            item.connect("activate", callback)
        item.show()
        menu.append(item)
    menu.popup(None, None, None, 0, event.time)

def set_completion(widget):
    '''
    Set entrycompletion on given widget

    @param widget: the widget to set entrycompletion
    '''

    completion = gtk.EntryCompletion()
    completion.set_model(widget.get_model())
    completion.set_minimum_key_length(1)
    completion.set_text_column(0)
    widget.child.set_completion(completion)

def set_combobox_wrap(combobox):
    '''
    Wrap the columns of a combobox depending on the number of items

    @param combobox: the combobox
    '''

    length = len(combobox.get_model())
    if length > 10 and length <= 30:
        combobox.set_wrap_width(2)
    elif length > 30:
        combobox.set_wrap_width(3)

def fill_combobox(combobox, items, active=0):
    '''
    Fill a combobox with the given data

    @param widget: the combobox
    @param items: list of items to add
    @param active: index of the active value
    '''

    model = combobox.get_model()
    model.clear()
    items.sort()
    for item in items:
        model.append([item])

    set_combobox_wrap(combobox)
    combobox.set_active(active)

def create_sex_combobox(sexdic):
    store = gtk.ListStore(str, str)
    for key, value in sexdic.items():
        store.insert(int(key), [key, value])
    cell = gtk.CellRendererText()
    combobox = gtk.ComboBox(store)
    combobox.pack_start(cell, True)
    combobox.add_attribute(cell, 'text', 1)
    combobox.set_active(0)

    return combobox

def create_status_combobox():
    store = gtk.ListStore(str)
    for item in [_("Dead"), _("Active"), _("Sold"), _("Lost")]:
        store.append([item])
    cell = gtk.CellRendererText()
    combobox = gtk.ComboBox(store)
    combobox.pack_start(cell, True)
    combobox.add_attribute(cell, 'text', 0)
    combobox.set_active(0)

    return combobox


class Statusbar:
    def __init__(self, statusbar):
        self.statusbar = statusbar

    def get_id(self, text):
        return self.statusbar.get_context_id(text)

    def push_message(self, context_id, message):
        self.statusbar.push(context_id, message)

    def pop_message(self, context_id):
        self.statusbar.pop(context_id)


class BackupDialog(gtk.Dialog):
    def __init__(self, parent, title, backuptype):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-close", gtk.RESPONSE_CLOSE))

        self.par = parent

        self.set_resizable(False)
        self.set_has_separator(False)

        if backuptype == 'create':
            label = gtk.Label(_("Choose a directory where to save the backup"))
            label.set_padding(30, 0)
            self.fcButtonCreate = gtk.FileChooserButton(_("Select a directory"))
            self.fcButtonCreate.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

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
            label = gtk.Label(_("Choose a Pigeon Planner backup file to restore"))
            label.set_padding(30, 0)
            label2 = gtk.Label(_("Warning! This will overwrite the existing database!"))
            label2.set_padding(30, 0)
            self.fcButtonRestore = gtk.FileChooserButton(_("Select a valid backup file"))
            self.fcButtonRestore.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            self.fcButtonRestore.add_filter(get_backup_filefilter())

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
            success = backup.make_backup(folder)
            if success:
                message_dialog('info', messages.MSG_BACKUP_SUCCES, self.par)
            else:
                message_dialog('info', messages.MSG_BACKUP_FAILED, self.par)

    def restorebackup_clicked(self, widget):
        zipfile = self.fcButtonRestore.get_filename()
        if zipfile:
            success = backup.restore_backup(zipfile)
            if success:
                message_dialog('info', messages.MSG_RESTORE_SUCCES, self.par)
            else:
                message_dialog('info', messages.MSG_RESTORE_FAILED, self.par)

class EditPedigreeDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _("Insert a pigeon"), parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_property("skip-taskbar-hint", True)

        table = gtk.Table(2,2)
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


class FilterDialog(gtk.Dialog):
    def __init__(self, parent, title, fill_treeview_cb):
        gtk.Dialog.__init__(self, title, parent, gtk.DIALOG_DESTROY_WITH_PARENT,
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
        '''
        Implement a non-blocking dialog so the user can browse through
        the pigeons while seeing the filters.
        '''

        self.connect('response', self.on_dialog_response)
        self.show_all()

    def on_dialog_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE or response_id == gtk.RESPONSE_DELETE_EVENT:
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
        fill_combobox(combobox, items)

        return self.__add_filter(combobox, label), combobox

    def add_filter_spinbutton(self, label, lowest=0, lowest_text=None):
        adj = gtk.Adjustment(lowest, lowest, 4000, 1, 10, 0)
        spinbutton = gtk.SpinButton(adj, 4)
        if lowest_text:
            spinbutton.set_text(lowest_text)
            spinbutton.connect('changed', self.on_spinbutton_changed, lowest, lowest_text)

        return self.__add_filter(spinbutton, label), spinbutton

