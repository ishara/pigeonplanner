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
from xml.sax.saxutils import escape

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GdkPixbuf

from pigeonplanner.ui import mime
from pigeonplanner.core import const


LAST_FOLDER = None


########
# Main filechooser
class _FileChooser:#Gtk.FileChooser):  # TODO GTK3: why does this fail?
    def _update_preview_cb(self, filechooser):
        filename = filechooser.get_preview_filename()
        if filename is None:
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 128, 128)
            self.preview_image.set_from_pixbuf(pixbuf)
        except GLib.Error:
            if os.path.isdir(filename):
                self.preview_image.set_from_icon_name("folder", Gtk.IconSize.DIALOG)
            else:
                mimetype = mime.get_type(filename)
                icon = mime.get_icon(mimetype)
                self.preview_image.set_from_gicon(icon, Gtk.IconSize.DIALOG)
        filechooser.set_preview_widget_active(True)

    def _create_preview_widget(self):
        self.preview_image = Gtk.Image()
        frame = Gtk.Frame(label=_("Preview"))
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame.add(self.preview_image)
        frame.show_all()
        return frame

    def set_preview(self, value):
        if not value:
            return
        self.connect("update-preview", self._update_preview_cb)
        self.set_preview_widget(self._create_preview_widget())
        self.set_use_preview_label(False)

    def add_image_filter(self):
        filter_ = Gtk.FileFilter()
        filter_.set_name(_("Images"))
        filter_.add_pixbuf_formats()
        self.add_filter(filter_)

    def add_pdf_filter(self):
        filter_ = Gtk.FileFilter()
        filter_.set_name("PDF")
        filter_.add_pattern("*.pdf")
        self.add_filter(filter_)

    def add_text_filter(self):
        filter_ = Gtk.FileFilter()
        filter_.set_name("Text (.txt)")
        filter_.add_pattern("*.txt")
        filter_.add_pattern("*.TXT")
        self.add_filter(filter_)

    def add_backup_filter(self):
        filter_ = Gtk.FileFilter()
        filter_.set_name("Zip (.zip)")
        filter_.add_mime_type("zip/zip")
        filter_.add_pattern("*.zip")
        self.add_filter(filter_)

    def add_custom_filter(self, filter_):
        class Filter(Gtk.FileFilter):
            def __init__(self, name, pattern):
                Gtk.FileFilter.__init__(self)
                self.set_name(name)
                self.add_pattern(pattern)
        name, pattern = filter_
        filefilter = Filter(name, pattern)
        self.add_filter(filefilter)


########
# Dialogs
class _FileChooserDialog(Gtk.FileChooserDialog, _FileChooser):
    def __init__(self, parent=None, folder=const.HOMEDIR,
                 action=Gtk.FileChooserAction.OPEN, preview=True):
        super(_FileChooserDialog, self).__init__(parent=parent, action=action)
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.set_preview(preview)
        if LAST_FOLDER is not None:
            folder = LAST_FOLDER
        if folder is None:
            folder = const.HOMEDIR
        self.set_current_folder(folder)

    def do_response(self, response):
        if response == Gtk.ResponseType.OK:
            global LAST_FOLDER
            LAST_FOLDER = self.get_current_folder()


class ImageChooser(_FileChooserDialog):

    __gtype_name__ = "ImageChooser"

    RESPONSE_CLEAR = -40

    def __init__(self, parent):
        super(ImageChooser, self).__init__(parent, GLib.get_user_special_dir(GLib.USER_DIRECTORY_PICTURES))
        self.set_title(_("Select an image..."))
        self.add_image_filter()
        self.add_button(_("OK"), Gtk.ResponseType.OK)


class MediaChooser(_FileChooserDialog):

    __gtype_name__ = "MediaChooser"

    def __init__(self, parent):
        super(MediaChooser, self).__init__(parent)
        self.connect("selection-changed", self._selection_changed_cb)
        self.set_title(_("Select a file..."))
        self.add_button(_("OK"), Gtk.ResponseType.OK)
        self.set_extra_widget(self._create_extra_widget())

    def _selection_changed_cb(self, filechooser):
        fname = self.get_filename()
        if fname is None:
            return
        self.entrytitle.set_text(os.path.splitext(os.path.basename(fname))[0])

    def _create_extra_widget(self):
        labeltitle = Gtk.Label(_("Title"))
        labeltitle.set_alignment(0, .5)
        self.entrytitle = Gtk.Entry()

        labeldesc = Gtk.Label(_("Description"))
        labeldesc.set_alignment(0, .5)
        self.entrydescription = Gtk.Entry()

        table = Gtk.Table(2, 2, False)
        table.set_row_spacings(4)
        table.set_col_spacings(8)
        table.attach(labeltitle, 0, 1, 0, 1, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entrytitle, 1, 2, 0, 1)
        table.attach(labeldesc, 0, 1, 1, 2, Gtk.AttachOptions.FILL, 0)
        table.attach(self.entrydescription, 1, 2, 1, 2)
        table.show_all()
        return table

    def get_filetitle(self):
        return self.entrytitle.get_text()

    def get_filedescription(self):
        return self.entrydescription.get_text()

    def get_filetype(self):
        return mime.get_type(self.get_filename())


class PdfSaver(_FileChooserDialog):

    __gtype_name__ = "PdfSaver"

    def __init__(self, parent, pdf_name):
        super(PdfSaver, self).__init__(parent, preview=False,
                                       action=Gtk.FileChooserAction.SAVE)
        self.set_title(_("Save as..."))
        self.add_pdf_filter()
        self.add_button(_("Save"), Gtk.ResponseType.OK)
        self.set_current_name(pdf_name)


class BackupSaver(_FileChooserDialog):

    __gtype_name__ = "BackupSaver"

    def __init__(self, parent, backup_name):
        super(BackupSaver, self).__init__(parent, preview=False,
                                          action=Gtk.FileChooserAction.SAVE)
        self.set_title(_("Save as..."))
        self.add_backup_filter()
        self.add_button(_("Save"), Gtk.ResponseType.OK)
        self.set_current_name(backup_name)


class ExportChooser(_FileChooserDialog):

    __gtype_name__ = "ExportChooser"

    def __init__(self, parent, filename, filter_):
        super(ExportChooser, self).__init__(parent, preview=False,
                                            action=Gtk.FileChooserAction.SAVE)
        self.set_title(_("Save as..."))
        self.add_custom_filter(filter_)
        self.add_button(_("Save"), Gtk.ResponseType.OK)
        self.set_current_name(filename)


class PathChooserDialog(_FileChooserDialog):

    __gtype_name__ = "PathChooserDialog"

    def __init__(self, parent, folder):
        super(PathChooserDialog, self).__init__(parent, preview=False, folder=folder,
                                                action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.set_title(_("Select a folder..."))
        self.add_button(_("Save"), Gtk.ResponseType.OK)


class DatabasePathChooserDialog(_FileChooserDialog):

    __gtype_name__ = "DatabasePathChooserDialog"

    def __init__(self, parent, folder=const.PREFDIR):
        super(DatabasePathChooserDialog, self).__init__(parent, preview=False, folder=folder,
                                                        action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.set_title(_("Select a folder..."))
        self.add_button(_("Save"), Gtk.ResponseType.OK)

        image_info = Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        label_info = Gtk.Label()
        label_info.set_markup("%s <b>%s</b>" % (_("The default location is:"), escape(const.PREFDIR)))
        button_info = Gtk.Button(label=_("Select"))
        button_info.connect("clicked", self.on_button_default_path_clicked)
        box_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        box_info.pack_start(image_info, False, False, 0)
        box_info.pack_start(label_info, False, False, 0)
        box_info.pack_start(button_info, False, False, 0)
        box_info.show_all()
        self.set_extra_widget(box_info)

    def on_button_default_path_clicked(self, widget):
        self.set_current_folder(const.PREFDIR)


########
# Buttons
# General
class _FileChooserButton(Gtk.FileChooserButton, _FileChooser):
    def __init__(self, folder=const.HOMEDIR,
                 action=Gtk.FileChooserAction.OPEN, preview=True, dialog=None):
        if dialog is None:
            super(_FileChooserButton, self).__init__("")
        else:
            super(_FileChooserButton, self).__init__(dialog)
        self.set_current_folder(folder)
        self.set_preview(preview)
        self.set_action(action)


class PathChooser(_FileChooserButton):

    __gtype_name__ = "PathChooser"

    def __init__(self, title=None, dialog=None):
        super(PathChooser, self).__init__(preview=False, dialog=dialog,
                                          action=Gtk.FileChooserAction.SELECT_FOLDER)
        if title is None:
            title = _("Select a folder...")
        self.set_title(title)


class FileChooser(_FileChooserButton):

    __gtype_name__ = "FileChooser"

    def __init__(self, title=None, preview=False):
        super(FileChooser, self).__init__(preview=preview)
        if title is None:
            title = _("Select a file...")
        self.set_title(title)


# Custom
class ResultChooser(FileChooser):

    __gtype_name__ = "ResultChooser"

    def __init__(self):
        super(ResultChooser, self).__init__()
        self.add_text_filter()


class BackupChooser(_FileChooserButton):

    __gtype_name__ = "BackupChooser"

    def __init__(self):
        super(BackupChooser, self).__init__()
        self.add_backup_filter()
