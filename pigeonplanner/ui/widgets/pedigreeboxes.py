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
import glib

from pigeonplanner import const


def format_text(text):
    if not text:
        return ""
    return glib.markup_escape_text(text)


class PedigreeBox_cairo(gtk.DrawingArea):
    def __init__(self, pigeon=None, child=None, detailed=False):
        gtk.DrawingArea.__init__(self)

        if not detailed:
            self.set_property("can-focus", True)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.add_events(gtk.gdk.ENTER_NOTIFY_MASK)
        self.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        self.connect('enter-notify-event', self.on_enter_event)
        self.connect('leave-notify-event', self.on_leave_event)
        self.connect("state_changed", self.state_changed)
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
            else:
                self.bgcolor = (255/256.0, 205/256.0, 241/256.0)
                self.bordercolor = (135/256.0, 32/256.0, 106/256.0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0, 0, 0)
            if detailed and child is not None:
                self.editable = True
                tform = "<span style='italic' foreground='#6a6a6a'>%s</span>"
                self.text = tform % format_text(_("<edit>"))

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

    def realize(self, widget):
        self.set_size_request(max(12, 150), max(28, 25))

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

        width = 5 if self.highlight else 2
        self.context.set_line_width(width)
        self.context.append_path(path)
        self.context.set_source_rgb(*self.bordercolor)
        self.context.stroke()


class ExtraBox_cairo(gtk.DrawingArea):
    def __init__(self, pigeon, lines):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = ''
        if pigeon is not None:
            extra = pigeon.get_extra()
            self.text = format_text('\n'.join(extra[:lines]))
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


class PedigreeBox(gtk.DrawingArea):
    def __init__(self, pigeon, child, detailed):
        gtk.DrawingArea.__init__(self)

        if not detailed:
            self.set_property("can-focus", True)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.add_events(gtk.gdk.ENTER_NOTIFY_MASK)
        self.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        self.connect('enter-notify-event', self.on_enter_event)
        self.connect('leave-notify-event', self.on_leave_event)
        self.connect("state_changed", self.state_changed)
        self.pigeon = pigeon
        self.child = child
        self.sex = None
        self.editable = False
        self.highlight = False

        text = ''
        if self.pigeon:
            self.editable = True
            text = self.pigeon.get_band_string(True)
        else:
            if detailed and child is not None:
                self.editable = True
                tform = "<span style='italic' foreground='#6a6a6a'>%s</span>"
                text = tform % format_text(_("<edit>"))

        self.textlayout = self.create_pango_layout('')
        self.textlayout.set_markup(text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        y = 34 if detailed else 25
        self.set_size_request(max(xmin, 150), max(ymin, y))

    def get_sex(self):
        return self.sex

    def set_sex(self, value):
        self.sex = value

    def set_highlight(self, value):
        width = 3 if value else 1
        self.border_gc.line_width = width
        self.queue_draw()

    def on_enter_event(self, widget, event):
        if self.editable:
            self.set_highlight(True)

    def on_leave_event(self, widget, event):
        self.set_highlight(False)

    def state_changed(self, widget, prev_state):
        #TODO
        pass
    
    def realize(self, widget):
        self.bg_gc = self.window.new_gc()
        self.text_gc = self.window.new_gc()
        self.border_gc = self.window.new_gc()
        self.border_gc.line_style = gtk.gdk.LINE_SOLID
        self.border_gc.line_width = 1
        self.shadow_gc = self.window.new_gc()
        self.shadow_gc.line_style = gtk.gdk.LINE_SOLID
        self.shadow_gc.line_width = 4
        if self.pigeon:
            if self.pigeon.get_sex() == '0':
                self.bg_gc.set_foreground(
                        self.get_colormap().alloc_color("#b9cfe7"))
                self.border_gc.set_foreground(
                        self.get_colormap().alloc_color("#204a87"))
            else:
                self.bg_gc.set_foreground(
                        self.get_colormap().alloc_color("#ffcdf1"))
                self.border_gc.set_foreground(
                        self.get_colormap().alloc_color("#87206a"))
        else:
            self.bg_gc.set_foreground(
                        self.get_colormap().alloc_color("#eeeeee"))
            self.border_gc.set_foreground(
                        self.get_colormap().alloc_color("#777777"))
        self.shadow_gc.set_foreground(
                        self.get_colormap().alloc_color("#999999"))

    def expose(self, widget, event):
        alloc = self.get_allocation()

        self.window.draw_line(self.shadow_gc, 3, alloc.height-1,
                              alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3,
                              alloc.width-1, alloc.height)

        self.window.draw_rectangle(self.bg_gc, True, 1, 1,
                                   alloc.width-5, alloc.height-5)

        if self.pigeon or self.editable:
            self.window.draw_layout(self.text_gc, 5, 4, self.textlayout)

        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1,
                                       alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0,
                                       alloc.width-4, alloc.height-4)


class ExtraBox(gtk.DrawingArea):
    def __init__(self, pigeon, lines):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = ''
        if pigeon is not None:
            extra = pigeon.get_extra()
            self.text = format_text('\n'.join(extra[:lines]))
        self.textlayout = self.create_pango_layout(self.text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        self.set_size_request(max(xmin, 220), max(ymin, 25))

    def realize(self, widget):
        self.bg_gc = self.window.new_gc()
        self.text_gc = self.window.new_gc()
        self.border_gc = self.window.new_gc()
        self.border_gc.line_style = gtk.gdk.LINE_SOLID
        self.border_gc.line_width = 1
        self.shadow_gc = self.window.new_gc()
        self.shadow_gc.line_style = gtk.gdk.LINE_SOLID
        self.shadow_gc.line_width = 4
        if self.text != '':
            self.bg_gc.set_foreground(
                            self.get_colormap().alloc_color("#f0e68c"))
            self.border_gc.set_foreground(
                            self.get_colormap().alloc_color("#777777"))
        else:
            self.bg_gc.set_foreground(
                            self.get_colormap().alloc_color("#eeeeee"))
            self.border_gc.set_foreground(
                            self.get_colormap().alloc_color("#777777"))
        self.shadow_gc.set_foreground(
                            self.get_colormap().alloc_color("#999999"))

    def expose(self, widget, event):
        alloc = self.get_allocation()

        self.window.draw_line(self.shadow_gc, 3, alloc.height-1,
                              alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3,
                              alloc.width-1, alloc.height)

        self.window.draw_rectangle(self.bg_gc, True, 1, 1, alloc.width-5,
                                   alloc.height-5)

        if self.text:
            self.window.draw_layout(self.text_gc, 5, 4, self.textlayout)

        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1,
                                       alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0,
                                       alloc.width-4, alloc.height-4)


class PedigreeCross(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("expose_event", self.expose)

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
        self.connect("expose_event", self.expose)

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


