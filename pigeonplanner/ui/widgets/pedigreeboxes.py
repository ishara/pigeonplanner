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
Classes for drawing the pedigreeboxes
"""

import gtk
import glib

from pigeonplanner import const
from pigeonplanner import messages
from pigeonplanner.ui import dialogs
from pigeonplanner.ui.widgets import menus


def format_text(text):
    if not text:
        return ""
    return glib.markup_escape_text(text)


class PedigreeBox_cairo(gtk.DrawingArea):
    def __init__(self, pindex, ring, year, sex, details, kinfo,
                 detailed, main, draw):
        gtk.DrawingArea.__init__(self)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.hightlight = False
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        self.editable = False
        if detailed:
            if kinfo:
                self.kindex = kinfo[0]
                self.connect("button-press-event", self.detail_pressed)
                self.editable = True
        else:
            self.set_property("can-focus", True)
            self.connect("button-press-event", self.pressed)
            self.connect("focus-out-event", self.focus_out)

        self.pindex = pindex
        self.ring = ring
        self.year = year
        self.sex = sex
        self.details = details
        self.kinfo = kinfo
        self.detailed = detailed
        self.main = main
        self.draw = draw

        self.text = ''
        self.set_text()

    def focus_out(self, widget, event):
        self.hightlight = False
        self.queue_draw()

    def set_text(self):
        if self.ring != '':
            self.text = self.ring + ' / ' + self.year[2:]

            if self.sex == '0':
                self.bgcolor = (185/256.0, 207/256.0, 231/256.0)
                self.bordercolor = (32/256.0, 74/256.0, 135/256.0)
            else:
                self.bgcolor = (255/256.0, 205/256.0, 241/256.0)
                self.bordercolor = (135/256.0, 32/256.0, 106/256.0)
        else:
            self.set_property("can-focus", False)
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0,0,0)

            if self.editable:
                tform = "<span style='italic' foreground='#6a6a6a'>%s</span>"
                self.text = tform %format_text(_("<edit>"))

    def detail_pressed(self, widget, event):
        editbox = dialogs.EditPedigreeDialog(
                                    self.get_toplevel(), self.main,
                                    self.pindex, self.sex, self.kinfo,
                                    self.draw)

        if event.button == 1:
            editbox.run(None, self.ring, self.year, self.details)
        elif event.button == 3:
            try:
                show = self.main.parser.pigeons[self.pindex].show
            except KeyError:
                show = 0

            entries = [(gtk.STOCK_EDIT, editbox.run,
                                        (self.ring, self.year, self.details)
                )]

            if self.ring and self.year and show == 0:
                entries.append((gtk.STOCK_CLEAR, editbox.clear_box, None))
                entries.append((gtk.STOCK_REMOVE,
                                editbox.remove_pigeon, (self.pindex,)))

            menus.popup_menu(event, entries)

    def pressed(self, widget, event):
        if self.textlayout.get_text() == '':
            return

        self.hightlight = True
        self.queue_draw()
        self.grab_focus()

        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.select_pigeon()
        elif event.button == 3:
            menus.popup_menu(event, [
                                     (gtk.STOCK_INFO,
                                      self.main.show_pigeon_details,
                                      (self.pindex,)),
                                     (gtk.STOCK_JUMP_TO,
                                      self.select_pigeon, None),
                                    ])

    def select_pigeon(self, widget=None):
        if self.main.search_pigeon(None, self.pindex):
            # Pigeon is found in the list
            return

        if self.pindex in self.main.parser.pigeons:
            # Pigeon exists, so it isn't shown in the list
            d = dialogs.MessageDialog(const.WARNING,
                                      messages.MSG_SHOW_PIGEON,
                                      self.main.mainwindow)
            if d.response == gtk.RESPONSE_YES:
                self.main.database.update_table(self.main.database.PIGEONS,
                                                (1, self.pindex), 5, 1)
                self.main.parser.get_pigeons()
                self.main.fill_treeview()
        else:
            # Pigeon doesn't exist in the database
            d = dialogs.MessageDialog(const.QUESTION,
                                      messages.MSG_ADD_PIGEON,
                                      self.main.mainwindow)
            if d.response == gtk.RESPONSE_YES:
                self.main.menuadd_activate(None)
                self.main.entryRing1.set_text(self.ring)
                self.main.entryYear1.set_text(self.year)
                self.main.cbsex.set_active(int(self.sex))

    def realize(self, widget):
        if self.detailed:
            y = 34
        else:
            y = 25

        self.set_size_request(max(12, 150), max(28, y))

    def expose(self, widget, event):
        alloc = self.get_allocation()
        self.context = self.window.cairo_create()

        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)

        self.context.move_to(0, 5)
        self.context.curve_to(0, 2, 2,0, 5,0)
        self.context.line_to(alloc.width-8,0)
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

        if self.hightlight:
            self.context.set_line_width(5)
        else:
            self.context.set_line_width(2)
        self.context.append_path(path)
        self.context.set_source_rgb(*self.bordercolor)
        self.context.stroke()


class ExtraBox_cairo(gtk.DrawingArea):
    def __init__(self, details, rows):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = '\n'.join(details[:rows])
        if self.text != '':
            self.text = format_text(self.text)
            self.bgcolor = (240/256.0, 230/256.0, 140/256.0)
            self.bordercolor = (0,0,0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0,0,0)

    def realize(self, widget):
        self.set_size_request(max(12, 220), max(28, 25))
        
    def expose(self, widget, event):
        alloc = self.get_allocation()
        self.context = self.window.cairo_create()

        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)

        self.context.move_to(0, 5)
        self.context.curve_to(0, 2, 2,0, 5,0)
        self.context.line_to(alloc.width-8,0)
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
    def __init__(self, pindex, ring, year, sex, details, kinfo,
                 detailed, main, draw):
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        self.editable = False
        if detailed:
            if kinfo:
                self.kindex = kinfo[0]
                self.connect("button-press-event", self.detail_pressed)
                self.editable = True
        else:
            self.set_property("can-focus", True)
            self.connect("button-press-event", self.pressed)
            self.connect("focus-in-event", self.focus_in)
            self.connect("focus-out-event", self.focus_out)

        self.pindex = pindex
        self.ring = ring
        self.year = year
        self.sex = sex
        self.details = details
        self.kinfo = kinfo
        self.detailed = detailed
        self.main = main
        self.draw = draw

        text = ''

        if ring != '':
            text = ring + ' / ' + year[2:]

        self.textlayout = self.create_pango_layout(text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        if detailed:
            y = 34
        else:
            y = 25
        self.set_size_request(max(xmin, 150), max(ymin, y))

    def focus_in(self, widget, event):
        self.queue_draw()

    def focus_out(self, widget, event):
        self.queue_draw()

    def detail_pressed(self, widget, event):
        editbox = dialogs.EditPedigreeDialog(
                                    self.get_toplevel(), self.main,
                                    self.pindex, self.sex, self.kinfo,
                                    self.draw)

        if event.button == 1:
            editbox.run(self.ring, self.year, self.details)
        elif event.button == 3:
            try:
                show = self.main.parser.pigeons[self.pindex].show
            except KeyError:
                show = 0

            entries = [(gtk.STOCK_EDIT, editbox.run,
                                        (self.ring, self.year, self.details)
                )]

            if self.ring and self.year and show == 0:
                entries.append((gtk.STOCK_CLEAR, editbox.clear_box, None))
                entries.append((gtk.STOCK_REMOVE,
                                editbox.remove_pigeon, (self.pindex,)))

            menus.popup_menu(event, entries)

    def pressed(self, widget, event):
        if self.textlayout.get_text():
            self.hightlight = True
            self.queue_draw()
            self.grab_focus()

            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                if self.main.search_pigeon(None, self.pindex):
                    return

                if self.pindex in self.main.parser.pigeons:
                    d = dialogs.MessageDialog(const.WARNING,
                                              messages.MSG_SHOW_PIGEON,
                                              self.main.mainwindow)
                    if d.response == gtk.RESPONSE_YES:
                        self.main.database.update_table(self.main.database.PIGEONS,
                                                        (1, self.pindex), 5, 1)
                        self.main.parser.get_pigeons()
                        self.main.fill_treeview()
                        return
                else:
                    d = dialogs.MessageDialog(const.QUESTION,
                                              messages.MSG_ADD_PIGEON,
                                              self.main.mainwindow)
                    if d.response == gtk.RESPONSE_YES:
                        self.main.menuadd_activate(None)
                        self.main.entryRing1.set_text(self.ring)
                        self.main.entryYear1.set_text(self.year)
                        self.main.cbsex.set_active(int(self.sex))
    
    def realize(self, widget):
        self.bg_gc = self.window.new_gc()
        self.text_gc = self.window.new_gc()
        self.border_gc = self.window.new_gc()
        self.border_gc.line_style = gtk.gdk.LINE_SOLID
        self.border_gc.line_width = 1
        self.shadow_gc = self.window.new_gc()
        self.shadow_gc.line_style = gtk.gdk.LINE_SOLID
        self.shadow_gc.line_width = 4
        if self.pindex:
            if self.sex == '0':
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

    def expose(self,widget,event):
        alloc = self.get_allocation()

        self.window.draw_line(self.shadow_gc, 3, alloc.height-1,
                              alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3,
                              alloc.width-1, alloc.height)

        self.window.draw_rectangle(self.bg_gc, True, 1, 1,
                                   alloc.width-5, alloc.height-5)

        if self.pindex:
            self.window.draw_layout(self.text_gc, 5, 4, self.textlayout)

        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1,
                                       alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0,
                                       alloc.width-4, alloc.height-4)


class ExtraBox(gtk.DrawingArea):
    def __init__(self, details, rows):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = '\n'.join(details[:rows])

        if self.text != '':
            self.text = format_text(self.text)

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

    def expose(self,widget,event):
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
        self.set_size_request(20,-1)
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
        self.set_size_request(20,-1)
        self.connect("expose_event", self.expose)

    def expose(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        idx = area.get_data("idx")
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        if idx %2 == 0:
            if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
                area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2,
                                      alloc.height/2)
            else:
                area.window.draw_line(gc, alloc.width, alloc.height/2,
                                      alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2,
                                  alloc.height/2)
        else:
            if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
                area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2,
                                      alloc.height/2)
            else:
                area.window.draw_line(gc, alloc.width, alloc.height/2,
                                      alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, alloc.height,
                                  alloc.width/2, alloc.height/2)


