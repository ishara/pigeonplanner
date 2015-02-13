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

from pigeonplanner import mime
from pigeonplanner import messages
from pigeonplanner import thumbnail
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.messagedialog import QuestionDialog
from pigeonplanner.core import common
from pigeonplanner.database.models import Media


(COL_OBJECT,
 COL_TEXT,
 COL_COLOR,
 COL_SELECTABLE) = range(4)


class MediaTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self):
        builder.GtkBuilder.__init__(self, "MediaView.ui")
        basetab.BaseTab.__init__(self, "MediaTab", _("Media"), "icon_media.png")

        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.set_select_function(self._select_func, full=True)
        self.widgets.selection.connect("changed", self.on_selection_changed)

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.widgets.buttonremove, self.widgets.buttonopen]
        utils.set_multiple_sensitive(widgets, not rowiter is None)
        self.widgets.image.clear()
        if rowiter is None:
            return

        media = model.get_value(rowiter, COL_OBJECT)
        if mime.is_image(media.type):
            self.widgets.image.set_from_pixbuf(thumbnail.get_image(media.path))
        else:
            try:
                image = mime.get_pixbuf(media.type)
                self.widgets.image.set_from_pixbuf(image)
            except mime.MimeIconError:
                self.widgets.image.set_from_stock(gtk.STOCK_FILE,
                                                  gtk.ICON_SIZE_DIALOG)

    def on_buttonopen_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        media = model.get_value(rowiter, COL_OBJECT)
        common.open_file(media.path)

    def on_buttonadd_clicked(self, widget):
        chooser = filechooser.MediaChooser(self._parent)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            data = {
                "pigeon": self.pigeon,
                "path": chooser.get_filename(),
                "type": chooser.get_filetype(),
                "title": chooser.get_filetitle(),
                "description": chooser.get_filedescription()
            }
            query = Media.insert(**data)
            query.execute()
            # Hackish... Fill whole treeview again
            self.set_pigeon(self.pigeon)
        chooser.destroy()

    def on_buttonremove_clicked(self, widget):
        if not QuestionDialog(messages.MSG_REMOVE_MEDIA, self._parent).run():
            return

        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.liststore.get_path(rowiter)
        media = model.get_value(rowiter, COL_OBJECT)
        if mime.is_image(media.type):
            try:
                os.remove(thumbnail.get_path(media.path))
            except:
                pass
        media.delete_instance()
        self.widgets.liststore.remove(rowiter)
        self.widgets.selection.select_path(path)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        images = []
        other = []
        self.widgets.liststore.clear()
        for media in (Media.select()
            .where(Media.pigeon == pigeon)
            .order_by(Media.title.asc())):
            if mime.is_image(media.type):
                images.append(media)
            else:
                other.append(media)

        normal = ["#ffffff", True]
        self.widgets.liststore.append([None, _("Images"), "#dcdcdc", False])
        for media in images:
            text = self._format_text(media.title, media.description)
            self.widgets.liststore.append([media, text]+normal)
        self.widgets.liststore.append([None, _("Other"), "#dcdcdc", False])
        for media in other:
            text = self._format_text(media.title, media.description)
            self.widgets.liststore.append([media, text]+normal)

    def clear_pigeon(self):
        self.widgets.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    def _format_text(self, title, description):
        text = common.escape_text(title)
        if description:
            text += " - <span style=\"italic\" size=\"smaller\">%s</span>"\
                        % common.escape_text(description)
        return text

    def _select_func(self, selection, model, path, is_selected):
        return model[path][COL_SELECTABLE]

