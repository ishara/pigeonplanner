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


import gtk
import gobject

import const


SEVERITY = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
COLORS = {"DEBUG": "grey", "INFO": "green", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "white"}

class LogDialog(gtk.Dialog):
    def __init__(self, widget=False):
        gtk.Dialog.__init__(self)
        self.set_title(_("Logfile Viewer"))
        self.set_size_request(700,500)
        self.set_icon(self.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_MENU))

        self.file = open(const.LOGFILE, "r")
        self.back_buffer = gtk.TextBuffer()
        self.back_buffer.set_text(self.file.read())

        frame = gtk.Frame()
        self.vbox.pack_start(frame)
        frame.set_border_width(10)
        hbox = gtk.HBox()
        frame.add(hbox)

        #auto scroll 
        scroll = gtk.ScrolledWindow()
        hbox.pack_start(scroll)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.get_vadjustment().connect("changed", self.changed)
        scroll.get_vadjustment().connect("value-changed", self.value_changed)

        #textview
        buffer = gtk.TextBuffer()
        self.textview = gtk.TextView(buffer)
        scroll.add(self.textview)
        self.textview.set_wrap_mode(gtk.WRAP_NONE)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

        table = buffer.get_tag_table()
        for name, color in COLORS.items():
            tag = gtk.TextTag(name)
            tag.set_property("foreground", color)
            tag.set_property("left_margin", 10)
            tag.set_property("right_margin", 10)
            table.add(tag)

        #combo
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 10)
        buttonbox = gtk.HButtonBox()
        hbox.pack_start(buttonbox, False, False, 10)
#        label = gtk.Label("Minimum severity shown.")
#        hbox.pack_start(label, False, False, 10)
        aspect = gtk.AspectFrame()
        aspect.set_shadow_type(gtk.SHADOW_NONE)
        hbox.pack_start(aspect)

        self.combo = gtk.combo_box_new_text()
        buttonbox.pack_start(self.combo)
        self.combo.connect("changed", self.reload)

        for s in SEVERITY:
            self.combo.append_text(s)
        self.combo.set_active(0)

        #report info
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 10)
        label = gtk.Label(_("If there are any errors, make sure the box above\nis set to \"DEBUG\" and mail the entire text to:\n\ntimovwb@gmail.com"))
        label.set_justify(gtk.JUSTIFY_CENTER)
        label.set_alignment(0.50, 0)
        hbox.pack_start(label, True, True, 10)

        #action area
        button = gtk.Button(None, gtk.STOCK_CLOSE)
        self.action_area.pack_start(button)
        button.connect("clicked", self.close)

        self.connect("response", self.close)
        self.show_all()

        gobject.timeout_add(1000, self.update)
        self.run()

    def insert_color(self, buffer, line):
        for s in SEVERITY[self.combo.get_active():]:
            if s in line:
                buffer.insert_with_tags(buffer.get_end_iter(), "%s\n" % line, buffer.get_tag_table().lookup(s))
                break

    def reload(self, textview):
        buffer = self.textview.get_buffer()
        buffer.set_text("")
        ini, fin = self.back_buffer.get_bounds()
        for line in self.back_buffer.get_text(ini, fin).split("\n"):
            self.insert_color(buffer, line)

    def update(self):
        try:
            buffer = self.textview.get_buffer()
            for line in self.file.readlines():
                self.back_buffer.insert(self.back_buffer.get_end_iter(), line)
                self.insert_color(buffer, line.strip())
        except:
            pass
        else:
            return True

    def changed(self, vadjust):
        if not hasattr(vadjust, "need_scroll") or vadjust.need_scroll:
            vadjust.set_value(vadjust.upper-vadjust.page_size)
            vadjust.need_scroll = True

    def value_changed (self, vadjust):
        vadjust.need_scroll = abs(vadjust.value + vadjust.page_size - vadjust.upper) < vadjust.step_increment

    def close(self, widget=None, other=None):
        self.file.close()
        self.destroy()

if __name__ == "__main__":
    c = LogView()
