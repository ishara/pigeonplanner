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


import gtk


class ExtraBox(gtk.DrawingArea):
    def __init__(self, text):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)

        self.text = '\n'.join(text)

        if text != '':
            self.bgcolor = (240/256.0, 230/256.0, 140/256.0)
            self.bordercolor = (0,0,0)
        else:
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0,0,0)

        self.set_size_request(220,25)

    def realize(self, widget):
        self.context = self.window.cairo_create()
        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        self.set_size_request(max(xmin, 220), max(ymin, 25))
        
    def expose(self, widget, event):
        alloc = self.get_allocation()
        self.context = self.window.cairo_create()

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


class PedigreeBox(gtk.DrawingArea):
    def __init__(self, ring, year, sex, detail=False, button=None):
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.hightlight = False
        self.connect("expose_event", self.expose)
        self.connect("realize", self.realize)
        if not detail:
            self.set_property("can-focus", True)
            self.connect("button-press-event", self.pressed)
            self.connect("focus-in-event", self.focus_in)
            self.connect("focus-out-event", self.focus_out)

        self.ring = ring
        self.year = year
        self.gotobutton = button

        self.text = ''

        if ring != '':
            self.text = ring + ' / ' + year

            if sex == '0':
                self.bgcolor = (185/256.0, 207/256.0, 231/256.0)
                self.bordercolor = (32/256.0, 74/256.0, 135/256.0)
            else:
                self.bgcolor = (255/256.0, 205/256.0, 241/256.0)
                self.bordercolor = (135/256.0, 32/256.0, 106/256.0)
        else:
            self.set_property("can-focus", False)
            self.bgcolor = (211/256.0, 215/256.0, 207/256.0)
            self.bordercolor = (0,0,0)

        self.set_size_request(200,25)

    def focus_in(self, widget, event):
        self.hightlight = True
        self.queue_draw()
        if self.textlayout.get_text() and self.gotobutton:
            self.gotobutton.set_sensitive(True)

    def focus_out(self, widget, event):
        self.hightlight = False
        self.queue_draw()
        if self.gotobutton:
            self.gotobutton.set_sensitive(False)

    def pressed(self, widget, event):
        self.grab_focus()

    def realize(self, widget):
        self.context = self.window.cairo_create()
        self.textlayout = self.context.create_layout()
        self.textlayout.set_font_description(self.get_style().font_desc)
        self.textlayout.set_markup(self.text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        self.set_size_request(max(xmin, 120), max(ymin, 25))
        
    def expose(self, widget, event):
        alloc = self.get_allocation()
        self.context = self.window.cairo_create()

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
    def __init__(self, tables=None, pindex=None, detail=False, button=None, pigeons=None):

        self.pindex = pindex
        self.detail = detail
        self.button = button
        self.pigeons = pigeons
        self.tables = tables
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

            if not lst[i]:
                box = PedigreeBox('', '', 'other', detail=self.detail, button=self.button)
                table.attach(box, x, y, w, h)
                if self.detail:
                    extrabox = ExtraBox('')
                    table.attach(extrabox, x, y, w+1, h+height)
            else:
                box = PedigreeBox(lst[i][1], lst[i][2], lst[i][3], detail=self.detail, button=self.button)
                table.attach(box, x, y, w, h)
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

                    extrabox = ExtraBox(extra)
                    table.attach(extrabox, x, y, w+1, h+height)

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
        area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2, alloc.height/2)
        area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2, alloc.height)

    def line_expose_cb(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        idx = area.get_data("idx")
        gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 2
        if idx %2 == 0:
            area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2, alloc.height/2)
        else:
            area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2, alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, alloc.height, alloc.width/2, alloc.height/2)

    def build_tree(self, pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6, index, depth, lst):
        if depth > 5 or ring == None or index >= len(lst):
            return

        lst[index] = (pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6)

        if not self.pigeons:
            import PigeonParser
            self.parser = PigeonParser.PigeonParser()
            self.parser.get_pigeons()
            self.pigeons = self.parser.pigeons

        if pindex in self.pigeons:

            lst[index] = (pindex, ring, year, sex, ex1, ex2, ex3, ex4, ex5, ex6)

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
                extra1 = extra2 = extra3 = extra4 = extra5 = extra6 = ''

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
                extra1 = extra2 = extra3 = extra4 = extra5 = extra6 = ''

            if ringDam:
                self.build_tree(pindexdam, ringDam, yearDam, '1', extra1, extra2, extra3, extra4, extra5, extra6, (2*index)+2, depth+1, lst)

