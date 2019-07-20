# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.
# Parts taken and inspired by Tucan.

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

"""
Logdialog class
"""

import glob
import os.path

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from pigeonplanner.core import const


SEVERITY = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "TRACEBACK"]
COLORS = {
    "DEBUG": "grey",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "white",
    "TRACEBACK": "white"
}


class LogDialog(Gtk.Dialog):
    def __init__(self,):
        Gtk.Dialog.__init__(self)
        self.set_title(_("Logfile Viewer"))
        self.set_size_request(700, 500)
        self.set_icon(self.render_icon(Gtk.STOCK_FILE, Gtk.IconSize.MENU))

        self.set_logfile()

        frame = Gtk.Frame()
        self.vbox.pack_start(frame, True, True, 0)
        frame.set_border_width(10)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        frame.add(hbox)

        # auto scroll
        scroll = Gtk.ScrolledWindow()
        hbox.pack_start(scroll, True, True, 0)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.get_vadjustment().connect("changed", self.changed)
        scroll.get_vadjustment().connect("value-changed", self.value_changed)

        # textview
        self.textview = Gtk.TextView()
        scroll.add(self.textview)
        self.textview.set_wrap_mode(Gtk.WrapMode.NONE)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_name("logfile-textview")

        for name, color in COLORS.items():
            self.textview.get_buffer().create_tag(name, foreground=color, left_margin=10, right_margin=10)

        # combo
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        align = Gtk.Alignment.new(.0, .0, .0, .0)
        align.add(vbox)
        self.vbox.pack_start(align, False, False, 0)
        label = Gtk.Label("Minimum severity shown:")
        label.set_alignment(0, .5)
        vbox.pack_start(label, False, False, 0)

        # combo severity
        self.combo = Gtk.ComboBoxText()
        vbox.pack_start(self.combo, False, False, 0)
        self.combo.connect("changed", self.reload_view)

        for s in SEVERITY:
            self.combo.append_text(s)
        self.combo.set_active(0)

        # combo logs
        self.combo_logs = Gtk.ComboBoxText()
        vbox.pack_start(self.combo_logs, False, False, 0)
        self.combo_logs.connect("changed", self.set_logfile)
        self.combo_logs.connect("changed", self.reload_view)

        logs = sorted(glob.glob(const.LOGFILE + "*"))
        for log in logs:
            self.combo_logs.append_text(os.path.basename(log))
        self.combo_logs.set_active(0)

        # action area
        button_close = Gtk.Button.new_from_stock(Gtk.STOCK_CLOSE)
        button_close.connect("clicked", self.close)
        self.action_area.pack_start(button_close, False, False, 0)

        self.connect("response", self.close)
        self.show_all()

        GLib.timeout_add(1000, self.update)
        self.run()

    def set_logfile(self, widget=None):
        if widget is not None:
            logfile = os.path.join(const.PREFDIR, widget.get_active_text())
        else:
            logfile = const.LOGFILE
        self.file = open(logfile, "r")
        self.back_buffer = Gtk.TextBuffer()
        self.back_buffer.set_text(self.file.read())

    def insert_color(self, bffr, line):
        for s in SEVERITY[self.combo.get_active():]:
            if s in line:
                bffr.insert_with_tags(bffr.get_end_iter(), "%s\n" % line,
                                      bffr.get_tag_table().lookup(s))
                break

    def reload_view(self, textview):
        bffr = self.textview.get_buffer()
        bffr.set_text("")
        start, end = self.back_buffer.get_bounds()
        for line in self.back_buffer.get_text(start, end, True).split("\n"):
            self.insert_color(bffr, line)

    def update(self):
        try:
            bffr = self.textview.get_buffer()
            for line in self.file.readlines():
                self.back_buffer.insert(self.back_buffer.get_end_iter(), line)
                self.insert_color(bffr, line.strip())
        except:
            pass
        else:
            return True

    def changed(self, vadjust):
        if not hasattr(vadjust, "need_scroll") or vadjust.need_scroll:
            vadjust.set_value(vadjust.get_upper()-vadjust.get_page_size())
            vadjust.need_scroll = True

    def value_changed(self, vadjust):
        vadjust.need_scroll = abs(vadjust.get_value() + vadjust.get_page_size() -
                                  vadjust.get_upper()) < vadjust.get_step_increment()

    def close(self, widget=None, other=None):
        self.file.close()
        self.destroy()
