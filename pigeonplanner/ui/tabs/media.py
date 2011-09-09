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

import gtk

import mime
import common
import builder
import messages
import thumbnail
from ui import filechooser
from ui.tabs import basetab
from ui.messagedialog import QuestionDialog
from translation import gettext as _


class MediaTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, parent, database, options, parser):
        basetab.BaseTab.__init__(self, _("Media"), "icon_media.png")
        builder.GtkBuilder.__init__(self, "MediaView.ui")
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
        if mime.is_image(mimetype):
            path = unicode(model.get_value(rowiter, 2))
            self.image.set_from_pixbuf(thumbnail.get_image(path))
        else:
            try:
                image = mime.get_pixbuf(mimetype)
                self.image.set_from_pixbuf(image)
            except mime.MimeIconError:
                self.image.set_from_stock(gtk.STOCK_FILE, gtk.ICON_SIZE_DIALOG)

    def on_buttonopen_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        common.open_file(model.get_value(rowiter, 2))

    def on_buttonadd_clicked(self, widget):
        chooser = filechooser.MediaChooser(self.parent)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filepath = chooser.get_filename()
            filetype = chooser.get_filetype()
            data = [self.pigeon.get_pindex(), filetype, filepath,
                    chooser.get_filetitle(), chooser.get_filedescription()]
            rowid = self.database.insert_into_table(self.database.MEDIA, data)
            text = self._format_text(data[3], data[4])
            rowiter = self.liststore.insert(0, [rowid, filetype, filepath, text])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        chooser.destroy()

    def on_buttonremove_clicked(self, widget):
        if QuestionDialog(messages.MSG_REMOVE_MEDIA, self.parent).run():
            return

        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        rowid = model.get_value(rowiter, 0)
        filetype = model.get_value(rowiter, 1)
        filepath = model.get_value(rowiter, 2)
        if mime.is_image(filetype):
            try:
                os.remove(thumbnail.get_path(filepath))
            except:
                pass
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

