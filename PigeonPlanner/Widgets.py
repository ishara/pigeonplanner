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


def message_dialog(sort, text, parent=None):
    '''
    Display a message dialog.

    @param parent: The parent window
    @param sort: The sort of dialog
    @param text: The text to display
    '''

    if sort == 'error':
        sort = gtk.MESSAGE_ERROR
        buttons = gtk.BUTTONS_OK
    elif sort == 'warning':
        sort = gtk.MESSAGE_WARNING
        buttons = gtk.BUTTONS_YES_NO
    elif sort == 'question':
        sort = gtk.MESSAGE_QUESTION
        buttons = gtk.BUTTONS_YES_NO
    elif sort == 'info':
        sort = gtk.MESSAGE_INFO
        buttons = gtk.BUTTONS_OK

    dialog = gtk.MessageDialog(parent=parent, type=sort, message_format=text, buttons=buttons)
    result = dialog.run()
    if result == -9:
        dialog.destroy()
        return False
    elif result == -8:
        dialog.destroy()
        return True
    dialog.destroy()

def setup_treeview(treeview, columns, column_types, changed_callback=None, resizeable=True, sortable=True):
    '''
    Create a ListStore and TreeViewSelection for the given treeview

    @param columns         : List of column names
    @param column_types    : List of variable types for each column
    @param changed_callback: the callback function for the "changed" signal
    @param resizeable_cols : True to allow columns to be resizable
    @param sortable_cols   : True to allow user to sort columns
    '''

    liststore = gtk.ListStore(*column_types)

    for i in range(len(columns)):
        rendererText = gtk.CellRendererText()
        rendererText.set_property('yalign', 0.0)

        column = gtk.TreeViewColumn(columns[i], rendererText, text=i)

        if sortable:
            column.set_sort_column_id(i)

        if resizeable:
            column.set_resizable(True)

        treeview.append_column(column)

    tvSelection = treeview.get_selection()
    if changed_callback:
        tvSelection.connect('changed', changed_callback)

    treeview.set_model(liststore)

    return liststore, tvSelection

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

def fill_list(widget, items):
    '''
    Fill the comboboxentry's with their data

    @param widget: the comboboxentry
    @param items: list of items to add
    '''

    model = widget.get_model()
    model.clear()
    items.sort()
    for item in items:
        model.append([item])

    number = len(model)
    if number > 10 and number <= 30:
        widget.set_wrap_width(2)
    elif number > 30:
        widget.set_wrap_width(3)

def popup_menu(event, entries):
    menu = gtk.Menu()
    for stock_id, callback in entries:
        item = gtk.ImageMenuItem(stock_id)
        if callback:
            item.connect("activate", callback)
        item.show()
        menu.append(item)
    menu.popup(None, None, None, 0, event.time)


class ImageWindow(gtk.Window):
    def __init__(self, imagepath, main):
        gtk.Window.__init__(self)
        self.set_title(_("View image: ") + os.path.split(imagepath)[-1])
        self.set_default_size(1000, 825)
        self.set_transient_for(main)
        self.set_modal(True)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.connect("delete_event", self.exit_window)

        sw = gtk.ScrolledWindow()
        eventbox = gtk.EventBox()
        eventbox.connect('button-release-event', self.eventbox_press)
        viewport = gtk.Viewport()
        tooltips = gtk.Tooltips()
        image = gtk.Image()
        image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(imagepath))
        tooltips.set_tip(image, _("Click to close this window"))
        eventbox.add(image)
        viewport.add(eventbox)
        sw.add(viewport)
        self.add(sw)
        self.show_all()

    def eventbox_press(self, widget, event):
        self.exit_window(self)

    def exit_window(self, widget, event=None):
        self.hide()
        return False


