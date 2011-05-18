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


import gtk


class BackupFilter(gtk.FileFilter):
    def __init__(self):
        gtk.FileFilter.__init__(self)

        self.set_name("PP Backups")
        self.add_mime_type("zip/zip")
        self.add_pattern("*PigeonPlannerBackup.zip")


class ImageFilter(gtk.FileFilter):
    def __init__(self):
        gtk.FileFilter.__init__(self)

        self.set_name(_("Images"))
        self.add_pixbuf_formats()


class PdfFilter(gtk.FileFilter):
    def __init__(self):
        gtk.FileFilter.__init__(self)

        self.set_name("PDF")
        self.add_pattern("*.pdf")


class TxtFilter(gtk.FileFilter):
    def __init__(self):
        gtk.FileFilter.__init__(self)

        self.set_name("Text (.txt)")
        self.add_pattern("*.txt")
        self.add_pattern("*.TXT")

