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

import gtk

import const
import common
import thumbnail
from translation import gettext as _


class PedigreeBox(gtk.DrawingArea):
    def __init__(self, pigeon=None, child=None, detailed=False):
        gtk.DrawingArea.__init__(self)

        if not detailed:
            self.set_property("can-focus", True)
        self.set_has_tooltip(True)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.add_events(gtk.gdk.ENTER_NOTIFY_MASK)
        self.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect("expose-event", self.expose)
        self.connect("realize", self.realize)
        self.connect("enter-notify-event", self.on_enter_event)
        self.connect("leave-notify-event", self.on_leave_event)
        self.connect("state-changed", self.state_changed)
        self.connect("query-tooltip", self.on_query_tooltip)
        self.pigeon = pigeon
        self.child = child
        self.sex = None
        self.editable = False
        self.highlight = False

        self.text = ''
        if self.pigeon:
            self.editable = True
            self.text = self.pigeon.get_band_string(True)
            if int(self.pigeon.get_sex()) == const.SIRE:
                self.bgcolor = (185/256.0, 207/256.0, 231/256.0)
                self.bordercolor = (32/256.0, 74/256.0, 135/256.0)
            elif int(self.pigeon.get_sex()) == const.DAM:
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
                tform = "<span style='italic' foreground='#6a6a6a'>%s</span>"
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
        if widget.state == gtk.STATE_INSENSITIVE:
            self.text = "<span foreground='#6a6a6a'>%s</span>" % self.text
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
        self.queue_draw()

    def on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        if self.pigeon is None:
            return False
        path = self.pigeon.get_image()
        # Path can be None or '', ignore both
        if path:
            tooltip.set_icon(thumbnail.get_image(path))
            return True
        return False

    def realize(self, widget):
        # Class needs a context
        self.context = self.window.cairo_create()
        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)
        size = self.textlayout.get_pixel_size()
        xmin = size[0] + 12
        ymin = size[1] + 11
        self.set_size_request(max(xmin, 155), max(ymin, 25))

    def expose(self, widget, event):
        alloc = self.get_allocation()
        context = self.window.cairo_create()

        context.move_to(0, 5)
        context.curve_to(0, 2, 2, 0, 5, 0)
        context.line_to(alloc.width-8, 0)
        context.curve_to(alloc.width-5, 0, alloc.width-3, 2,
                              alloc.width-3, 5)
        context.line_to(alloc.width-3, alloc.height-8)
        context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5,
                              alloc.height-3, alloc.width-8, alloc.height-3)
        context.line_to(5, alloc.height-3)
        context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0,
                              alloc.height-8)
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
        context.show_layout(self.textlayout)

        width = 5 if self.highlight else 2
        context.set_line_width(width)
        context.append_path(path)
        context.set_source_rgb(*self.bordercolor)
        context.stroke()


class ExtraBox(gtk.DrawingArea):
    def __init__(self, pigeon, lines):
        gtk.DrawingArea.__init__(self)
        self.connect("expose-event", self.expose)
        self.connect("realize", self.realize)

        self.text = ''
        if pigeon is not None:
            extra = pigeon.get_extra()
            self.text = common.escape_text('\n'.join(extra[:lines]))
            self.bgcolor = (240/256.0, 230/256.0, 140/256.0)
            self.bordercolor = (0, 0, 0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0, 0, 0)

    def realize(self, widget):
        self.set_size_request(max(12, 220), max(28, 25))
        
    def expose(self, widget, event):
        alloc = self.get_allocation()
        self.context = self.window.cairo_create()

        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)

        self.context.move_to(0, 5)
        self.context.curve_to(0, 2, 2, 0, 5, 0)
        self.context.line_to(alloc.width-8, 0)
        self.context.curve_to(alloc.width-5, 0, alloc.width-3, 2,
                              alloc.width-3, 5)
        self.context.line_to(alloc.width-3, alloc.height-8)
        self.context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5,
                              alloc.height-3, alloc.width-8, alloc.height-3)
        self.context.line_to(5, alloc.height-3)
        self.context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0,
                              alloc.height-8)
        self.context.close_path()
        path = self.context.copy_path()

        self.context.save()
        self.context.translate(3, 3)
        self.context.new_path()
        self.context.append_path(path)
        self.context.set_source_rgba(self.bordercolor[0], self.bordercolor[1],
                                     self.bordercolor[2], 0.4)
        self.context.fill_preserve()
        self.context.set_line_width(0)
        self.context.stroke()
        self.context.restore()

        self.context.append_path(path)
        self.context.clip()

        self.context.append_path(path)
        self.context.set_source_rgb(*self.bgcolor)
        self.context.fill_preserve()
        self.context.stroke()

        self.context.move_to(5, 4)
        self.context.set_source_rgb(0, 0, 0)
        self.context.show_layout(self.textlayout)

        self.context.set_line_width(2)
        self.context.append_path(path)
        self.context.set_source_rgb(*self.bordercolor)
        self.context.stroke()


class PedigreeCross(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("expose-event", self.expose)

    def expose(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
            area.window.draw_line(gc, alloc.width/2, alloc.height/2,
                                  alloc.width, alloc.height/2)
        else:
            area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2,
                                  alloc.height/2)
        area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2,
                              alloc.height)


class PedigreeLine(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("expose-event", self.expose)

    def expose(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        idx = area.get_data("idx")
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        x1 = 0 if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL else alloc.width
        if idx % 2 == 0:
            area.window.draw_line(gc, x1, alloc.height/2, alloc.width/2,
                                  alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2,
                                  alloc.height/2)
        else:
            area.window.draw_line(gc, x1, alloc.height/2, alloc.width/2,
                                  alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, alloc.height,
                                  alloc.width/2, alloc.height/2)


