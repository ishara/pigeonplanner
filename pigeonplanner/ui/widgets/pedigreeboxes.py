# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Parts taken and inspired by Gramps

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
Pedigree widgets
"""

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import PangoCairo

from pigeonplanner import thumbnail
from pigeonplanner.core import common


class PedigreeBox(Gtk.DrawingArea):
    def __init__(self, pigeon=None, child=None, detailed=False):
        Gtk.DrawingArea.__init__(self)

        self.textlayout = None

        if not detailed:
            self.set_property("can-focus", True)
        self.set_has_tooltip(True)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self.draw)
        self.connect("enter-notify-event", self.on_enter_event)
        self.connect("leave-notify-event", self.on_leave_event)
        self.connect("state-changed", self.state_changed)
        self.connect("query-tooltip", self.on_query_tooltip)
        self.pigeon = pigeon
        self.child = child
        self.sex = None
        self.editable = False
        self.highlight = False

        self.text = ""
        if self.pigeon:
            self.editable = True
            self.text = self.pigeon.band
            if self.pigeon.is_cock():
                self.bgcolor = (185/256.0, 207/256.0, 231/256.0)
                self.bordercolor = (32/256.0, 74/256.0, 135/256.0)
            elif self.pigeon.is_hen():
                self.bgcolor = (255/256.0, 205/256.0, 241/256.0)
                self.bordercolor = (135/256.0, 32/256.0, 106/256.0)
            else:
                self.bgcolor = (200/256.0, 200/256.0, 200/256.0)
                self.bordercolor = (100/256.0, 100/256.0, 100/256.0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0, 0, 0)
            if detailed and child is not None:
                self.editable = True
                tform = "<span style=\"italic\" foreground=\"#6a6a6a\">%s</span>"
                self.text = tform % common.escape_text(_("<edit>"))

    def get_sex(self):
        return self.sex

    def set_sex(self, value):
        self.sex = value

    def set_highlight(self, value):
        self.highlight = value
        self.queue_draw()

    def on_enter_event(self, widget, event):
        if self.editable:
            self.set_highlight(True)

    def on_leave_event(self, widget, event):
        self.set_highlight(False)

    def state_changed(self, widget, prev_state):
        if widget.get_state() == Gtk.StateType.INSENSITIVE:
            self.text = "<span foreground=\"#6a6a6a\">%s</span>" % self.text
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
        self.queue_draw()

    def on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        if self.pigeon is None:
            return False
        image = self.pigeon.main_image
        if image is not None:
            tooltip.set_icon(thumbnail.get_image(image.path))
            return True
        return False

    def draw(self, widget, context):
        alloc = self.get_allocation()

        minw = 155
        minh = 25
        if not self.textlayout:
            self.textlayout = PangoCairo.create_layout(context)
            font_desc = self.get_style_context().get_font(Gtk.StateFlags.NORMAL)
            self.textlayout.set_font_description(font_desc)
            self.textlayout.set_markup(self.text, -1)
        size = self.textlayout.get_pixel_size()
        xmin = size[0] + 12
        ymin = size[1] + 11
        self.set_size_request(max(xmin, minw), max(ymin, minh))

        context.move_to(0, 5)
        context.curve_to(0, 2, 2, 0, 5, 0)
        context.line_to(alloc.width-8, 0)
        context.curve_to(alloc.width-5, 0, alloc.width-3, 2, alloc.width-3, 5)
        context.line_to(alloc.width-3, alloc.height-8)
        context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5,
                         alloc.height-3, alloc.width-8, alloc.height-3)
        context.line_to(5, alloc.height-3)
        context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0, alloc.height-8)
        context.close_path()
        path = context.copy_path()

        context.save()
        context.translate(3, 3)
        context.new_path()
        context.append_path(path)
        context.set_source_rgba(self.bordercolor[0], self.bordercolor[1],
                                self.bordercolor[2], 0.4)
        context.fill_preserve()
        context.set_line_width(0)
        context.stroke()
        context.restore()

        context.append_path(path)
        context.clip()

        context.append_path(path)
        context.set_source_rgb(*self.bgcolor)
        context.fill_preserve()
        context.stroke()

        context.move_to(5, 4)
        context.set_source_rgb(0, 0, 0)
        PangoCairo.show_layout(context, self.textlayout)

        width = 5 if self.highlight else 2
        context.set_line_width(width)
        context.append_path(path)
        context.set_source_rgb(*self.bordercolor)
        context.stroke()


class ExtraBox(Gtk.DrawingArea):
    def __init__(self, pigeon, lines):
        Gtk.DrawingArea.__init__(self)

        self.textlayout = None

        self.connect("draw", self.draw)

        self.text = ""
        if pigeon is not None:
            self.text = common.escape_text("\n".join(pigeon.extra[:lines]))
            self.bgcolor = (240/256.0, 230/256.0, 140/256.0)
            self.bordercolor = (0, 0, 0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0, 0, 0)
        
    def draw(self, widget, context):
        alloc = self.get_allocation()

        minw = 220
        minh = 25
        if not self.textlayout:
            self.textlayout = PangoCairo.create_layout(context)
            font_desc = self.get_style_context().get_font(Gtk.StateFlags.NORMAL)
            self.textlayout.set_font_description(font_desc)
            self.textlayout.set_markup(self.text, -1)
        size = self.textlayout.get_pixel_size()
        xmin = size[0] + 12
        ymin = size[1] + 8
        self.set_size_request(max(xmin, minw), max(ymin, minh))

        context.move_to(0, 5)
        context.curve_to(0, 2, 2, 0, 5, 0)
        context.line_to(alloc.width-8, 0)
        context.curve_to(alloc.width-5, 0, alloc.width-3, 2, alloc.width-3, 5)
        context.line_to(alloc.width-3, alloc.height-8)
        context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5,
                         alloc.height-3, alloc.width-8, alloc.height-3)
        context.line_to(5, alloc.height-3)
        context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0, alloc.height-8)
        context.close_path()
        path = context.copy_path()

        context.save()
        context.translate(3, 3)
        context.new_path()
        context.append_path(path)
        context.set_source_rgba(self.bordercolor[0], self.bordercolor[1],
                                self.bordercolor[2], 0.4)
        context.fill_preserve()
        context.set_line_width(0)
        context.stroke()
        context.restore()

        context.append_path(path)
        context.clip()

        context.append_path(path)
        context.set_source_rgb(*self.bgcolor)
        context.fill_preserve()
        context.stroke()

        context.move_to(5, 4)
        context.set_source_rgb(0, 0, 0)
        PangoCairo.show_layout(context, self.textlayout)

        context.set_line_width(2)
        context.append_path(path)
        context.set_source_rgb(*self.bordercolor)
        context.stroke()


class PedigreeCross(Gtk.DrawingArea):
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("draw", self.draw)

    def draw(self, area, context):
        alloc = area.get_allocation()
        context.set_dash([], 0)
        context.set_line_width(2)
        if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL:
            context.move_to(alloc.width/2, alloc.height/2)
            context.line_to(alloc.width, alloc.height/2)
        else:
            context.move_to(0, alloc.height/2)
            context.line_to(alloc.width/2, alloc.height/2)
        context.move_to(alloc.width/2, 0)
        context.line_to(alloc.width/2, alloc.height)
        context.stroke()


class PedigreeLine(Gtk.DrawingArea):
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("draw", self.draw)

    def draw(self, area, context):
        alloc = area.get_allocation()
        context.set_dash([], 0)
        context.set_line_width(2)
        x1 = 0 if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL else alloc.width
        if area.idx % 2 == 0:
            context.move_to(x1, alloc.height/2)
            context.line_to(alloc.width/2, alloc.height/2)
            context.move_to(alloc.width/2, 0)
            context.line_to(alloc.width/2, alloc.height/2)
        else:
            context.move_to(x1, alloc.height/2)
            context.line_to(alloc.width/2, alloc.height/2)
            context.move_to(alloc.width/2, alloc.height)
            context.line_to(alloc.width/2, alloc.height/2)
        context.stroke()
