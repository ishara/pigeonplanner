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


# Colors:
# http://web.njit.edu/~kevin/rgb.txt.html
# http://www.jumbo-psp.com/PSP-for-Fun/images/Color%20tabel.htm


from cgi import escape

import gtk
import gtk.glade

try:
    import cairo
    cairo_available = True
except:
    cairo_available = False

import const
import checks
import widgets
import database
import messages


# Cairo-drawn boxes don't show up
if const.OSX:
    cairo_available = False


def format_text(text):
    if not text:
        return ""

    return escape(text)


class ExtraBox(gtk.DrawingArea):
    def __init__(self, text):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = '\n'.join(text)

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
            self.bg_gc.set_foreground(self.get_colormap().alloc_color("#f0e68c"))
            self.border_gc.set_foreground(self.get_colormap().alloc_color("#777777"))
        else:
            self.bg_gc.set_foreground(self.get_colormap().alloc_color("#eeeeee"))
            self.border_gc.set_foreground(self.get_colormap().alloc_color("#777777"))
        self.shadow_gc.set_foreground(self.get_colormap().alloc_color("#999999"))

    def expose(self,widget,event):
        alloc = self.get_allocation()

        self.window.draw_line(self.shadow_gc, 3, alloc.height-1, alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3, alloc.width-1, alloc.height)

        self.window.draw_rectangle(self.bg_gc, True, 1, 1, alloc.width-5, alloc.height-5)

        if self.text:
            self.window.draw_layout(self.text_gc, 5, 4, self.textlayout)

        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1, alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0, alloc.width-4, alloc.height-4)


class ExtraBox_cairo(gtk.DrawingArea):
    def __init__(self, text):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = '\n'.join(text)

        if text != '':
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
        self.context.curve_to(alloc.width-5, 0, alloc.width-3, 2, alloc.width-3, 5)
        self.context.line_to(alloc.width-3, alloc.height-8)
        self.context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5, alloc.height-3, alloc.width-8, alloc.height-3)
        self.context.line_to(5, alloc.height-3)
        self.context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0, alloc.height-8)
        self.context.close_path()
        path = self.context.copy_path()

        self.context.save()
        self.context.translate(3, 3)
        self.context.new_path()
        self.context.append_path(path)
        self.context.set_source_rgba(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2], 0.4)
        self.context.fill_preserve()
        self.context.set_line_width(0)
        self.context.stroke()
        self.context.restore()

        self.context.append_path(path)
        self.context.clip()

        self.context.append_path(path)
        self.context.set_source_rgb(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2])
        self.context.fill_preserve()
        self.context.stroke()

        self.context.move_to(5, 4)
        self.context.set_source_rgb(0, 0, 0)
        self.context.show_layout(self.textlayout)

        self.context.set_line_width(2)
        self.context.append_path(path)
        self.context.set_source_rgb(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2])
        self.context.stroke()


class PedigreeEditBox:
    def __init__(self, pindex, ring, year, sex, details, kinfo, main, pedigree):
        self.pindex = pindex
        self.ring = ring
        self.year = year
        self.sex = sex
        self.details = details
        self.kinfo = kinfo
        self.main = main
        self.pedigree = pedigree

        if kinfo:
            self.kindex = kinfo[0]

    def detail_pressed(self, widget, event):
        if event.button == 1:
            self.edit_start()
        elif event.button == 3:
            try:
                show = self.main.parser.pigeons[self.pindex].show
            except KeyError:
                show = 0

            if self.ring and self.year and show == 0:
                entries = [
                    (gtk.STOCK_EDIT, self.edit_start, None),
                    (gtk.STOCK_CLEAR, self.clear_box, None),
                    (gtk.STOCK_REMOVE, self.remove_pigeon, None)]

                widgets.popup_menu(event, entries)
            else:
                entries = [
                    (gtk.STOCK_EDIT, self.edit_start, None)]

                widgets.popup_menu(event, entries)

    def edit_start(self, widget=None):
        self.wTree = gtk.glade.XML(const.GLADEPEDIGREE, 'editdialog')

        signalDic = { 'on_cancel_clicked'  : self.close_dialog,
                      'on_save_clicked'    : self.save_clicked,
                      'on_dialog_destroy'  : self.close_dialog }
        self.wTree.signal_autoconnect(signalDic)

        for w in self.wTree.get_widget_prefix(''):
            wname = w.get_name()
            setattr(self, wname, w)

        if self.ring and self.year:
            self.entryRing.set_text(self.ring)
            self.entryYear.set_text(self.year)
            self.entryExtra1.set_text(self.details[0])
            self.entryExtra2.set_text(self.details[1])
            self.entryExtra3.set_text(self.details[2])
            self.entryExtra4.set_text(self.details[3])
            self.entryExtra5.set_text(self.details[4])
            self.entryExtra6.set_text(self.details[5])

        if not self.kindex in self.main.parser.pigeons:
            data = (self.kinfo[0], self.kinfo[1], self.kinfo[2], self.kinfo[3], 0, 1,
                    '', '', '', '', '', '', '', '', '',
                    self.kinfo[4], self.kinfo[5], self.kinfo[6],
                    self.kinfo[7], self.kinfo[8], self.kinfo[9])
            self.main.database.insert_pigeon(data)

        self.entryRing.grab_focus()
        self.entryRing.set_position(-1)
        self.editdialog.show()

    def save_clicked(self, widget):
        ring = self.entryRing.get_text()
        year = self.entryYear.get_text()

        if not checks.check_ring_entry(self.editdialog, ring, year): return

        pindex = ring + year

        if self.pindex and self.pindex in self.main.parser.pigeons:
            data = (pindex, ring, year,
                    self.entryExtra1.get_text(),
                    self.entryExtra2.get_text(),
                    self.entryExtra3.get_text(),
                    self.entryExtra4.get_text(),
                    self.entryExtra5.get_text(),
                    self.entryExtra6.get_text(),
                    self.pindex)
            self.edit_pigeon(data)
        else:
            data = (pindex, ring, year, self.sex , 0, 1,
                    '', '', '', '', '', '', '', '', '',
                    self.entryExtra1.get_text(),
                    self.entryExtra2.get_text(),
                    self.entryExtra3.get_text(),
                    self.entryExtra4.get_text(),
                    self.entryExtra5.get_text(),
                    self.entryExtra6.get_text())
            self.add_pigeon(data)

        self.main.parser.get_pigeons()

    def edit_parent(self, kindex, band, year, sex):
        if sex == '0':
            self.main.database.update_pigeon_sire((band, year, kindex))
        else:
            self.main.database.update_pigeon_dam((band, year, kindex))

    def edit_pigeon(self, data):
        self.main.database.update_pedigree_pigeon(data)

        self.edit_parent(self.kindex, data[1], data[2], self.sex)

        self.redraw()

        self.close_dialog()

    def add_pigeon(self, data):
        self.main.database.insert_pigeon(data)

        self.edit_parent(self.kindex, data[1], data[2], self.sex)

        self.redraw()

        self.close_dialog()

    def redraw(self):
        path, focus = self.main.treeview.get_cursor()
        self.main.parser.get_pigeons()
        self.main.fill_treeview(path=path)

        dp = DrawPedigree([self.pedigree.tableSire, self.pedigree.tableDam], self.pedigree.pindex,
                          True, self.main.parser.pigeons, self.main, self.pedigree)
        dp.draw_pedigree()

    def close_dialog(self, widget=None, event=None):
        self.editdialog.hide()

    def remove_pigeon(self, widget=None):
        self.main.database.delete_pigeon(self.pindex)

        self.edit_parent(self.kindex, '', '', self.sex)

        self.redraw()

        self.main.parser.get_pigeons()

    def clear_box(self, widget=None):
        self.edit_parent(self.kindex, '', '', self.sex)

        self.redraw()


class PedigreeBox(gtk.DrawingArea, PedigreeEditBox):
    def __init__(self, pindex, ring, year, sex, details, detail=False, kinfo=None, main=None, pedigree=None):
        gtk.DrawingArea.__init__(self)
        PedigreeEditBox.__init__(self, pindex, ring, year, sex, details, kinfo, main, pedigree)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        if detail:
            if kinfo:
                self.kindex = kinfo[0]
                self.connect("button-press-event", self.detail_pressed)
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
        self.detail = detail
        self.kinfo = kinfo
        self.main = main
        self.pedigree = pedigree

        text = ''

        if ring != '':
            text = ring + ' / ' + year[2:]

        self.textlayout = self.create_pango_layout(text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        if self.detail:
            y = 34
        else:
            y = 25
        self.set_size_request(max(xmin, 150), max(ymin, y))

    def focus_in(self, widget, event):
        self.queue_draw()

    def focus_out(self, widget, event):
        self.queue_draw()

    def pressed(self, widget, event):
        self.grab_focus()
    
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
                self.bg_gc.set_foreground(self.get_colormap().alloc_color("#b9cfe7"))
                self.border_gc.set_foreground(self.get_colormap().alloc_color("#204a87"))
            else:
                self.bg_gc.set_foreground(self.get_colormap().alloc_color("#ffcdf1"))
                self.border_gc.set_foreground(self.get_colormap().alloc_color("#87206a"))
        else:
            self.bg_gc.set_foreground(self.get_colormap().alloc_color("#eeeeee"))
            self.border_gc.set_foreground(self.get_colormap().alloc_color("#777777"))
        self.shadow_gc.set_foreground(self.get_colormap().alloc_color("#999999"))

    def expose(self,widget,event):
        alloc = self.get_allocation()

        self.window.draw_line(self.shadow_gc, 3, alloc.height-1, alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3, alloc.width-1, alloc.height)

        self.window.draw_rectangle(self.bg_gc, True, 1, 1, alloc.width-5, alloc.height-5)

        if self.pindex:
            self.window.draw_layout(self.text_gc, 5, 4, self.textlayout)

        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1, alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0, alloc.width-4, alloc.height-4)


class PedigreeBox_cairo(gtk.DrawingArea, PedigreeEditBox):
    def __init__(self, pindex, ring, year, sex, details, detail=False, kinfo=None, main=None, pedigree=None):
        gtk.DrawingArea.__init__(self)
        PedigreeEditBox.__init__(self, pindex, ring, year, sex, details, kinfo, main, pedigree)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.hightlight = False
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        editable = False
        if detail:
            if kinfo:
                self.kindex = kinfo[0]
                self.connect("button-press-event", self.detail_pressed)
                editable = True
        else:
            self.set_property("can-focus", True)
            self.connect("button-press-event", self.pressed)
            self.connect("focus-out-event", self.focus_out)

        self.pindex = pindex
        self.ring = ring
        self.year = year
        self.sex = sex
        self.details = details
        self.detail = detail
        self.kinfo = kinfo
        self.main = main
        self.pedigree = pedigree

        self.text = ''

        if ring != '':
            self.text = ring + ' / ' + year[2:]

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

            if editable:
                self.text = "<span style='italic' foreground='#6a6a6a'>%s</span>" %format_text(_("<edit>"))

    def focus_out(self, widget, event):
        self.hightlight = False
        self.queue_draw()

    def pressed(self, widget, event):
        if self.textlayout.get_text():
            self.hightlight = True
            self.queue_draw()
            self.grab_focus()

            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                if self.main.search_pigeon(None, self.pindex):
                    return

                if self.pindex in self.main.parser.pigeons:
                    if widgets.message_dialog('warning', messages.MSG_SHOW_PIGEON, self.main.main):
                        self.main.database.show_pigeon(self.pindex, 1)
                        self.main.parser.get_pigeons()
                        self.main.fill_treeview()
                        return
                else:
                    if widgets.message_dialog('question', messages.MSG_ADD_PIGEON, self.main.main):
                        self.main.menuadd_activate(None)
                        self.main.entryRing1.set_text(self.ring)
                        self.main.entryYear1.set_text(self.year)
                        self.main.cbsex.set_active(int(self.sex))

    def realize(self, widget):
        if self.detail:
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
        self.context.curve_to(alloc.width-5, 0, alloc.width-3, 2, alloc.width-3, 5)
        self.context.line_to(alloc.width-3, alloc.height-8)
        self.context.curve_to(alloc.width-3, alloc.height-5, alloc.width-5, alloc.height-3, alloc.width-8, alloc.height-3)
        self.context.line_to(5, alloc.height-3)
        self.context.curve_to(2, alloc.height-3, 0, alloc.height-5, 0, alloc.height-8)
        self.context.close_path()
        path = self.context.copy_path()

        self.context.save()
        self.context.translate(3, 3)
        self.context.new_path()
        self.context.append_path(path)
        self.context.set_source_rgba(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2], 0.4)
        self.context.fill_preserve()
        self.context.set_line_width(0)
        self.context.stroke()
        self.context.restore()

        self.context.append_path(path)
        self.context.clip()

        self.context.append_path(path)
        self.context.set_source_rgb(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2])
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
        self.context.set_source_rgb(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2])
        self.context.stroke()


class DrawPedigree:
    def __init__(self, tables=None, pindex=None, detail=False, pigeons=None, main=None, pedigree=None, lang=None):

        self.pindex = pindex
        self.detail = detail
        self.pigeons = pigeons
        self.tables = tables
        self.main = main
        self.pedigree = pedigree
        self.lang = lang
        if self.tables:
            self.tableSire = tables[0]
            self.tableDam = tables[1]

    def draw_pedigree(self):
        if self.detail:
            rng = 31
            self.pos = [(),
                        ((0, 1, 7, 8), ((1,0,7),(1,8,7))),
                        ((0, 1, 7, 8), ((1,0,7),(1,8,7))),
                        ((2, 3, 3, 4), ((3,0,3),(3,4,3))),
                        ((2, 3, 11, 12), ((3,8,3),(3,12,3))),
                        ((2, 3, 3, 4), ((3,0,3),(3,4,3))),
                        ((2, 3, 11, 12), ((3,8,3),(3,12,3))),
                        ((4, 5, 1, 2), ((5,0,1),(5,2,1))),
                        ((4, 5, 5, 6), ((5,4,1),(5,6,1))),
                        ((4, 5, 9, 10), ((5,8,1),(5,10,1))),
                        ((4, 5, 13, 14), ((5,12,1),(5,14,1))),
                        ((4, 5, 1, 2), ((5,0,1),(5,2,1))),
                        ((4, 5, 5, 6), ((5,4,1),(5,6,1))),
                        ((4, 5, 9, 10), ((5,8,1),(5,10,1))),
                        ((4, 5, 13, 14), ((5,12,1),(5,14,1))),
                        ((6, 7, 0, 1), (None)),
                        ((6, 7, 2, 3), (None)),
                        ((6, 7, 4, 5), (None)),
                        ((6, 7, 6, 7), (None)),
                        ((6, 7, 8, 9), (None)),
                        ((6, 7, 10, 11), (None)),
                        ((6, 7, 12, 13), (None)),
                        ((6, 7, 14, 15), (None)),
                        ((6, 7, 0, 1), (None)),
                        ((6, 7, 2, 3), (None)),
                        ((6, 7, 4, 5), (None)),
                        ((6, 7, 6, 7), (None)),
                        ((6, 7, 8, 9), (None)),
                        ((6, 7, 10, 11), (None)),
                        ((6, 7, 12, 13), (None)),
                        ((6, 7, 14, 15), (None))]
        else:
            rng = 15
            self.pos = [(),
                        ((0, 1, 4, 5), ((1,0,3),(1,5,3))),
                        ((0, 1, 4, 5), ((1,0,3),(1,5,3))),
                        ((2, 3, 1, 2), ((3,0,1),(3,2,1))),
                        ((2, 3, 6, 7), ((3,5,1),(3,7,1))),
                        ((2, 3, 1, 2), ((3,0,1),(3,2,1))),
                        ((2, 3, 6, 7), ((3,5,1),(3,7,1))),
                        ((4, 5, 0, 1), None), ((4, 5, 2, 3), None),
                        ((4, 5, 5, 6), None), ((4, 5, 7, 8), None),
                        ((4, 5, 0, 1), None), ((4, 5, 2, 3), None),
                        ((4, 5, 5, 6), None), ((4, 5, 7, 8), None)]

        lst = [None]*rng

        try:
            ring = self.pigeons[self.pindex].ring
            year = self.pigeons[self.pindex].year
            sex = self.pigeons[self.pindex].sex
        except KeyError:
            ring = ''
            year = ''
            sex = ''

        self.build_tree(self.pindex, ring, year, sex, '', '', '', '', '', '', 0, 1, lst)

        for table in self.tables:
            for child in table.get_children():
                child.destroy()

        for i in range(1, rng):
            x = self.pos[i][0][0]
            y = self.pos[i][0][1]
            w = self.pos[i][0][2]
            h = self.pos[i][0][3]

            table = self.tableSire
            if i in [2, 5, 6, 11, 12, 13, 14, 23, 24, 25, 26, 27, 28, 29, 30]:
                table = self.tableDam

            if self.detail:
                if i <= 6:
                    height = 4
                elif i >= 7 and i <= 14:
                    height = 2
                else:
                    height = 1

            if i%2 == 1:
                sex = '0'
                try:
                    kinfo = lst[(i - 1) / 2]
                except TypeError:
                    kinfo = None
            else:
                sex = '1'
                try:
                    kinfo = lst[(i - 2) / 2]
                except TypeError:
                    kinfo = None

            if not lst[i]:
                if cairo_available:
                    box = PedigreeBox_cairo('', '', '', sex, None, self.detail, kinfo, self.main, self.pedigree)
                else:
                    box = PedigreeBox('', '', '', sex, None, self.detail, kinfo, self.main, self.pedigree)
                table.attach(box, x, y, w, h)
                if self.detail:
                    if cairo_available:
                        extrabox = ExtraBox_cairo('')
                    else:
                        extrabox = ExtraBox('')
                    table.attach(extrabox, x, y, w+1, h+height)
            else:
                if self.detail:
                    extra = []
                    extra.append(lst[i][4])
                    if height >= 2:
                        extra.append(lst[i][5])
                        extra.append(lst[i][6])
                    if height == 4:
                        extra.append(lst[i][7])
                        extra.append(lst[i][8])
                        extra.append(lst[i][9])

                    allExtra = [lst[i][4], lst[i][5], lst[i][6], lst[i][7], lst[i][8], lst[i][9]]

                    if cairo_available:
                        box = PedigreeBox_cairo(lst[i][0], lst[i][1], lst[i][2], lst[i][3], allExtra, self.detail, kinfo, self.main, self.pedigree)
                    else:
                        box = PedigreeBox(lst[i][0], lst[i][1], lst[i][2], lst[i][3], allExtra, self.detail, kinfo, self.main, self.pedigree)
                    table.attach(box, x, y, w, h)

                    if cairo_available:
                        extrabox = ExtraBox_cairo(extra)
                    else:
                        extrabox = ExtraBox(extra)
                    table.attach(extrabox, x, y, w+1, h+height)
                else:
                    if cairo_available:
                        box = PedigreeBox_cairo(lst[i][0], lst[i][1], lst[i][2], lst[i][3], None, self.detail, main=self.main)
                    else:
                        box = PedigreeBox(lst[i][0], lst[i][1], lst[i][2], lst[i][3], None, self.detail)
                    table.attach(box, x, y, w, h)

            if self.pos[i][1]:
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.cross_expose_cb)
                table.attach(line, x+1, x+2, h-1, h, gtk.FILL, gtk.FILL, 0, 0)

                x = self.pos[i][1][0][0]
                y = self.pos[i][1][0][1]
                w = 1
                h = self.pos[i][1][0][2]
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.line_expose_cb)
                line.set_data("idx", i*2+1)
                table.attach(line, x, x+w, y, y+h, gtk.FILL, gtk.FILL, 0, 0)
                
                x = self.pos[i][1][1][0]
                y = self.pos[i][1][1][1]
                w = 1
                h = self.pos[i][1][1][2]
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.line_expose_cb)
                line.set_data("idx", i*2+2)
                line.set_data("height", h)
                table.attach(line, x, x+w, y, y+h, gtk.FILL, gtk.FILL, 0, 0)

        for table in self.tables:
            table.show_all()

    def cross_expose_cb(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        if self.lang == 'ar':
            area.window.draw_line(gc, alloc.width/2, alloc.height/2, alloc.width, alloc.height/2)
        else:
            area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2, alloc.height/2)
        area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2, alloc.height)

    def line_expose_cb(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        idx = area.get_data("idx")
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        if idx %2 == 0:
            if self.lang == 'ar':
                area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2, alloc.height/2)
            else:
                area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2, alloc.height/2)
        else:
            if self.lang == 'ar':
                area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2, alloc.height/2)
            else:
                area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, alloc.height, alloc.width/2, alloc.height/2)

    def build_tree(self, pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6, index, depth, lst):
        if depth > 5 or ring == None or index >= len(lst):
            return

        lst[index] = (pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6)

        if not self.pigeons:
            import pigeonparser
            self.parser = pigeonparser.PigeonParser()
            self.parser.get_pigeons()
            self.pigeons = self.parser.pigeons

        if pindex in self.pigeons:
            ringSire = self.pigeons[pindex].sire
            yearSire = self.pigeons[pindex].yearsire
            pindexsire = ringSire + yearSire
            try:
                extra1 = self.pigeons[pindexsire].extra1
                extra2 = self.pigeons[pindexsire].extra2
                extra3 = self.pigeons[pindexsire].extra3
                extra4 = self.pigeons[pindexsire].extra4
                extra5 = self.pigeons[pindexsire].extra5
                extra6 = self.pigeons[pindexsire].extra6
            except KeyError:
                extra1 = ''
                extra2 = ''
                extra3 = ''
                extra4 = ''
                extra5 = ''
                extra6 = ''

            if ringSire:
                self.build_tree(pindexsire, ringSire, yearSire, '0', extra1, extra2, extra3, extra4, extra5, extra6, (2*index)+1, depth+1, lst)

            ringDam = self.pigeons[pindex].dam
            yearDam = self.pigeons[pindex].yeardam
            pindexdam = ringDam + yearDam
            try:
                extra1 = self.pigeons[pindexdam].extra1
                extra2 = self.pigeons[pindexdam].extra2
                extra3 = self.pigeons[pindexdam].extra3
                extra4 = self.pigeons[pindexdam].extra4
                extra5 = self.pigeons[pindexdam].extra5
                extra6 = self.pigeons[pindexdam].extra6
            except KeyError:
                extra1 = ''
                extra2 = ''
                extra3 = ''
                extra4 = ''
                extra5 = ''
                extra6 = ''

            if ringDam:
                self.build_tree(pindexdam, ringDam, yearDam, '1', extra1, extra2, extra3, extra4, extra5, extra6, (2*index)+2, depth+1, lst)

