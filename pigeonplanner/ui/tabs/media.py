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
import mimetypes

import gtk
import glib

import const
import common
import builder
import messages
from ui import dialogs
from ui.tabs import basetab


def get_type_from_mime(mime):
    """
    Get the type from a mimetype of format type/subtype
    """

    if mime is None:
        return ""
    return mime.split('/')[0]


class MediaTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, parent, database, options, parser):
        basetab.BaseTab.__init__(self, _("Media"), "icon_media.png")
        builder.GtkBuilder.__init__(self, const.GLADEMEDIAVIEW)
        self._root.unparent()

        self.parent = parent
        self.database = database
        self.options = options
        self.parser = parser
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.buttonremove, self.buttonopen]
        self.set_multiple_sensitive(widgets, not rowiter is None)
        self.image.clear()
        if rowiter is None: return

        mimetype = model.get_value(rowiter, 1)
        if get_type_from_mime(mimetype) == 'image':
            path = model.get_value(rowiter, 2)
            self.image.set_from_pixbuf(common.get_thumbnail(path))

    def on_buttonopen_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        common.open_file(model.get_value(rowiter, 2))

    def on_buttonadd_clicked(self, widget):
        chooser = MediaChooser(self.parent)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filepath = chooser.get_filename()
            filetype = chooser.get_file_type()
            if get_type_from_mime(filetype) == 'image':
                common.image_to_thumb(filepath)
            data = [self.pigeon.get_pindex(), filetype, filepath,
                    chooser.get_file_title(), chooser.get_file_description()]
            rowid = self.database.insert_into_table(self.database.MEDIA, data)
            text = self._format_text(data[3], data[4])
            rowiter = self.liststore.insert(0, [rowid, filetype, filepath, text])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        chooser.destroy()

    def on_buttonremove_clicked(self, widget):
        d = dialogs.MessageDialog(const.QUESTION,
                                  messages.MSG_REMOVE_MEDIA,
                                  self.parent)
        if not d.yes:
            return

        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        rowid = model.get_value(rowiter, 0)
        filetype = model.get_value(rowiter, 1)
        filepath = model.get_value(rowiter, 2)
        if get_type_from_mime(filetype) == 'image':
            os.remove(common.get_thumb_path(filepath))
        self.database.delete_from_table(self.database.MEDIA, rowid, 0)
        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def fill_treeview(self, pigeon):
        self.pigeon = pigeon

        self.liststore.clear()
        for media in self.database.get_pigeon_media(pigeon.pindex):
            text = self._format_text(media[4], media[5])
            self.liststore.insert(0, [media[0], media[2], media[3], text])
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def _format_text(self, title, description):
        text = common.escape_text(title)
        if description:
            text += " - <span style='italic' size='smaller'>%s</span>"\
                        % common.escape_text(description)
        return text


class MediaChooser(gtk.FileChooserDialog):
    def __init__(self, parent):
        super(MediaChooser, self).__init__(parent=parent,
                                title=_("Select a file..."),
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.preview_image = gtk.Image()
        self.set_preview_widget(self.preview_image)
        table = gtk.Table(2, 2, False)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        self.set_extra_widget(table)
        self.set_use_preview_label(False)
        self.connect('selection-changed', self.on_selection_changed)
        self.connect('update-preview', self.on_update_preview)

        label = gtk.Label(_("Title"))
        label.set_alignment(0, .5)
        self.entrytitle = gtk.Entry()
        table.attach(label, 0, 1, 0, 1, gtk.FILL, 0)
        table.attach(self.entrytitle, 1, 2, 0, 1)
        label = gtk.Label(_("Description"))
        label.set_alignment(0, .5)
        self.entrydescription = gtk.Entry()
        table.attach(label, 0, 1, 1, 2, gtk.FILL, 0)
        table.attach(self.entrydescription, 1, 2, 1, 2)
        table.show_all()

    def on_selection_changed(self, filechooser):
        fname = self.get_filename()
        if fname is None: return
        self.entrytitle.set_text(os.path.splitext(os.path.basename(fname))[0])

    def on_update_preview(self, filechooser):
        filename = filechooser.get_preview_filename()
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 128, 128)
            self.preview_image.set_from_pixbuf(pixbuf)
        except:
            self.preview_image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                                              gtk.ICON_SIZE_DIALOG)
        filechooser.set_preview_widget_active(True)

    def get_file_title(self):
        return self.entrytitle.get_text()

    def get_file_description(self):
        return self.entrydescription.get_text()

    def get_file_type(self):
        return mimetypes.guess_type(self.get_filename())[0]

