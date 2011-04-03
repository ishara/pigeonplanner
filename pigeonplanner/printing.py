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

"""
Ingterface for all printing operations
"""


import os.path
import datetime

import gtk
import gobject
import cairo
import pango
import logging
logger = logging.getLogger(__name__)

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import messages
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import pedigree
from pigeonplanner.ui import printpreview
from pigeonplanner.ui.widgets import filefilters


PRINTER_DPI = 72.0

class BasePrinting(object):
    def __init__(self, parent, options, print_action, pdf_name, orientation):
        self.parent = parent

        if options.paper == 0:
            psize = gtk.PAPER_NAME_A4
        elif options.paper == 1:
            psize = gtk.PAPER_NAME_LETTER
        paper_size = gtk.PaperSize(psize)

        setup = gtk.PageSetup()
        setup.set_paper_size(paper_size)
        setup.set_orientation(orientation)

        settings = gtk.PrintSettings()
        settings.set_paper_size(paper_size)
        settings.set_orientation(orientation)

        print_ = gtk.PrintOperation()
        print_.set_default_page_setup(setup)
        print_.set_print_settings(settings)
        print_.set_unit(gtk.UNIT_MM)
        print_.set_show_progress(True)

        print_.connect("begin_print", self.begin_print)
        print_.connect("draw_page", self.draw_page)
        print_.connect("preview", self.preview_page)

        action = None
        if print_action == const.PRINT:
            action = gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG
        elif print_action == const.PREVIEW:
            action = gtk.PRINT_OPERATION_ACTION_PREVIEW
        elif print_action == const.MAIL:
            print_.set_export_filename(os.path.join(const.TEMPDIR, pdf_name))
            action = gtk.PRINT_OPERATION_ACTION_EXPORT
        elif print_action == const.SAVE:
            fc = gtk.FileChooserDialog(title=_("Save as..."), 
                        parent=self.parent,
                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            fc.add_filter(filefilters.PdfFilter())

            fc.set_current_name(pdf_name)
            fc.set_current_folder(common.get_unicode_path(const.HOMEDIR))

            response = fc.run()
            save_path = None
            if response == gtk.RESPONSE_OK:
                save_path = fc.get_filename()
            fc.destroy()
            if save_path:
                if not save_path.endswith(".pdf"):
                    save_path += ".pdf"
                print_.set_export_filename(save_path)
                action = gtk.PRINT_OPERATION_ACTION_EXPORT

        if action != None:
            try:
                response = print_.run(action, self.parent)
            except gobject.GError, e:
                logger.error("Error in print operation: %s" %e)
                dialogs.MessageDialog(const.ERROR,
                                      messages.MSG_PRINTOP_ERROR,
                                      self.parent)
            else:
                if response == gtk.PRINT_OPERATION_RESULT_ERROR:
                    print_error = print_.get_error()
                    logger.error("Error printing: %s" %print_error)
                    dialogs.MessageDialog(const.ERROR,
                                          messages.MSG_PRINT_ERROR)
                elif response == gtk.PRINT_OPERATION_RESULT_APPLY:
                    settings = print_.get_print_settings()

    def begin_print(self, operation, context):
        raise NotImplementedError

    def draw_page (self, operation, context, page_number):
        raise NotImplementedError

    def preview_page(self, operation, preview, context, parent):
        self.preview = printpreview.PrintPreview(operation, preview,
                                                 context, parent)

        # Dummy cairo context
        try:
            width = int(round(context.get_width()))
        except ValueError:
            width = 0
        try:
            height = int(round(context.get_height()))
        except ValueError:
            height = 0
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        context.set_cairo_context(cr, PRINTER_DPI, PRINTER_DPI)

        return True


class PrintPedigree(BasePrinting):
    def __init__(self, parent, pigeon, userinfo, options, print_action,
                 pdf_name, parser):
        orientation = gtk.PAGE_ORIENTATION_PORTRAIT
        self.pigeon = pigeon
        self.options = options
        self.userinfo = userinfo
        self.parser = parser
        self.preview = None
        BasePrinting.__init__(self, parent, options, print_action, pdf_name,
                              orientation)

    def begin_print(self, operation, context):
        operation.set_n_pages(1)

        if self.preview:
            self.preview.start()

    def draw_page (self, operation, context, page_number):
        cr = context.get_cairo_context()

        font = "Sans"
        total_width = context.get_width()
        # page corrections
        line_width = total_width - 4
        total_width -= 6

        cr.select_font_face(font)

        # head
        cr.set_font_size(8)
        cr.move_to(0, 10)
        cr.show_text(_("Pedigree of:"))
        ring = self.pigeon.get_band_string(True) if self.pigeon is not None else ''
        xb, yb, width, height, xa, ya = cr.text_extents(ring)
        cr.move_to(total_width-width, 10)
        cr.show_text(ring)

        # line
        cr.move_to(0, 12)
        cr.line_to(line_width, 12)

        # address
        cr.set_font_size(5)
        endPerson = 19
        if self.options.perName:
            cr.move_to(0, endPerson)
            cr.show_text(self.userinfo['name'])
            endPerson += 7
        if self.options.perAddress:
            cr.move_to(0, endPerson)
            cr.show_text(self.userinfo['street'])
            cr.move_to(0, endPerson+7)
            cr.show_text("%s %s" %(self.userinfo['code'],
                                   self.userinfo['city']))
            endPerson += 14
        if self.options.perPhone:
            cr.move_to(0, endPerson)
            cr.show_text(self.userinfo['phone'])
            endPerson += 7
        if self.options.perEmail:
            cr.move_to(0, endPerson)
            cr.show_text(self.userinfo['email'])


        # pigeondetails
        endPigeon = 19
        name = ''
        colour = ''
        sex = ''
        if self.options.pigName and self.pigeon is not None and\
            self.pigeon.get_name():
            name = "%s - " % self.pigeon.get_name()
        if self.options.pigColour and self.pigeon is not None and\
            self.pigeon.get_colour():
            colour = "%s - " % self.pigeon.get_colour()
        if self.options.pigSex and self.pigeon is not None:
            sex = self.pigeon.get_sex_string()
        info = name + colour + sex
        xb, yb, width, height, xa, ya = cr.text_extents(info)
        cr.move_to(total_width-width, endPigeon)
        cr.show_text(info)
        if info:
            endPigeon += 6

        if self.options.pigExtra:
            ex1, ex2, ex3, ex4, ex5, ex6 = self.pigeon.get_extra() if\
                self.pigeon is not None else ('', '', '', '', '', '')

            cr.set_font_size(4)
            xb, yb, width, height, xa, ya = cr.text_extents(ex1)
            cr.move_to(total_width-width, endPigeon)
            cr.show_text(ex1)
            xb, yb, width, height, xa, ya = cr.text_extents(ex2)
            cr.move_to(total_width-width, endPigeon+5)
            cr.show_text(ex2)
            xb, yb, width, height, xa, ya = cr.text_extents(ex3)
            cr.move_to(total_width-width, endPigeon+10)
            cr.show_text(ex3)
            xb, yb, width, height, xa, ya = cr.text_extents(ex4)
            cr.move_to(total_width-width, endPigeon+15)
            cr.show_text(ex4)
            xb, yb, width, height, xa, ya = cr.text_extents(ex5)
            cr.move_to(total_width-width, endPigeon+20)
            cr.show_text(ex5)
            xb, yb, width, height, xa, ya = cr.text_extents(ex6)
            cr.move_to(total_width-width, endPigeon+25)
            cr.show_text(ex6)
            endPigeon += 25

        # line
        cr.move_to(0, 52)
        cr.line_to(line_width, 52)

        # pedigree
        font_size = 3

        cr.select_font_face(font, cairo.FONT_SLANT_NORMAL)
        cr.set_font_size(font_size)

        pos = [(),
               ((0, 95, 45, 28), ((47, 109, 85),(47, 109, 133))),
               ((0, 191, 45, 28), ((47, 205, 181),(47, 205, 229))),
               ((49, 71, 45, 28), ((96, 85, 73),(96, 85, 97))),
               ((49, 119, 45, 28), ((96, 133, 121),(96, 133, 145))),
               ((49, 167, 45, 28), ((96, 181, 169),(96, 181, 193))),
               ((49, 215, 45, 28), ((96, 229, 217),(96, 229, 241))),
               ((98, 65, 45, 16), ((145, 73, 67),(145, 73, 79))),
               ((98, 89, 45, 16), ((145, 97, 91),(145, 97, 103))),
               ((98, 113, 45, 16), ((145, 121, 115),(145, 121, 127))),
               ((98, 137, 45, 16), ((145, 145, 139),(145, 145, 151))),
               ((98, 161, 45, 16), ((145, 169, 163),(145, 169, 175))),
               ((98, 185, 45, 16), ((145, 193, 187),(145, 193, 199))),
               ((98, 209, 45, 16), ((145, 217, 211),(145, 217, 223))),
               ((98, 233, 45, 16), ((145, 241, 235),(145, 241, 247))),
               ((147, 62, 45, 10), (None)),
               ((147, 74, 45, 10), (None)),
               ((147, 86, 45, 10), (None)),
               ((147, 98, 45, 10), (None)),
               ((147, 110, 45, 10), (None)),
               ((147, 122, 45, 10), (None)),
               ((147, 134, 45, 10), (None)),
               ((147, 146, 45, 10), (None)),
               ((147, 158, 45, 10), (None)),
               ((147, 170, 45, 10), (None)),
               ((147, 182, 45, 10), (None)),
               ((147, 194, 45, 10), (None)),
               ((147, 206, 45, 10), (None)),
               ((147, 218, 45, 10), (None)),
               ((147, 230, 45, 10), (None)),
               ((147, 242, 45, 10), (None))]

        lst = [None]*31
        pedigree.build_tree(self.parser, self.pigeon, 0, 1, lst)

        for i in xrange(1, 31):
            x = pos[i][0][0]
            y = pos[i][0][1]
            w = pos[i][0][2]
            h = pos[i][0][3]

            cr.rectangle(x, y, w, h)

            if lst[i]:
                pigeon = lst[i]
                cr.move_to(x + 0.5, y + 0.5 + font_size)
                cr.show_text(pigeon.get_band_string(True) if pigeon is not None
                                else '')

                if i <= 6:
                    height = 6
                elif i >= 7 and i <= 14:
                    height = 3
                else:
                    height = 1
                ex1, ex2, ex3, ex4, ex5, ex6 = pigeon.get_extra() if\
                    pigeon is not None else ('', '', '', '', '', '')
                if height >= 1:
                    cr.move_to(x + 0.5, y + 1.75 + font_size*2)
                    cr.show_text(ex1)
                if height >= 3:
                    cr.move_to(x + 0.5, y + 2.5 + font_size*3)
                    cr.show_text(ex2)
                    cr.move_to(x + 0.5, y + 3 + font_size*4)
                    cr.show_text(ex3)
                if height == 6:
                    cr.move_to(x + 0.5, y + 3.5 + font_size*5)
                    cr.show_text(ex4)
                    cr.move_to(x + 0.5, y + 4 + font_size*6)
                    cr.show_text(ex5)
                    cr.move_to(x + 0.5, y + 4.5 + font_size*7)
                    cr.show_text(ex6)

            if pos[i][1]:
                w = 2

                x = pos[i][1][0][0]
                y = pos[i][1][0][1]
                h = pos[i][1][0][2]

                cr.move_to(x-w, y)
                cr.line_to(x, y)

                cr.line_to(x, h)
                cr.line_to(x+w, h)

                x = pos[i][1][1][0]
                y = pos[i][1][1][1]
                h = pos[i][1][1][2]

                cr.move_to(x, y)

                cr.line_to(x, h)
                cr.line_to(x+w, h)

        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.3)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
      
        cr.stroke()


class PrintResults(BasePrinting):
    def __init__(self, parent, results, userinfo, options, print_action,
                 pdf_name):
        orientation = gtk.PAGE_ORIENTATION_LANDSCAPE
        self.results = results
        self.options = options
        self.userinfo = userinfo

        self.preview = None

        self.header_font_size = 12
        self.pagenr_font_size = 6
        self.text_font_size = 8

        self.columnNames = {
                    0: _("Band no."),
                    1: _("Date"),
                    2: _("Racepoint"),
                    3: _("Placed"),
                    4: _("Out of"),
                    5: _("Coef."),
                    6: _("Sector"),
                    7: _("Type"),
                    8: _("Category"),
                    9: _("Wind"),
                    10: _("Weather"),
                    11: _("Comment")
                }

        BasePrinting.__init__(self, parent, options, print_action, pdf_name,
                              orientation)

    def begin_print(self, operation, context):
        self.width = context.get_width()
        self.height = context.get_height()

        header = ''
        if self.options.perName:
            header += '%s\n' % self.userinfo['name']
        if self.options.perAddress:
            header += '%s\n' % self.userinfo['street']
            header += '%s %s\n' %( self.userinfo['code'], self.userinfo['city'])
        if self.options.perPhone:
            header += '%s\n' % self.userinfo['phone']
        if self.options.perEmail:
            header += '%s' % self.userinfo['email']
        self.header_layout = context.create_pango_layout()
        font = pango.FontDescription("Arial "+str(self.header_font_size))
        self.header_layout.set_font_description(font)
        self.header_layout.set_width(int(self.width*pango.SCALE))
        self.header_layout.set_alignment(pango.ALIGN_LEFT)
        self.header_layout.set_text(header)
        self.header_height = self.header_layout.get_size()[1] / 1024.0 + 2
        self.results_start = self.header_height + 4

        self.pagenr_layout = context.create_pango_layout()
        font = pango.FontDescription("Arial "+str(self.pagenr_font_size))
        self.pagenr_layout.set_font_description(font)
        self.pagenr_layout.set_width(int(self.width*pango.SCALE))
        self.pagenr_layout.set_alignment(pango.ALIGN_RIGHT)

        self.results_layouts = []
        self.column_layouts = []
        for x in xrange(12):
            if x == 5 and not self.options.colcoef:
                continue
            if x == 6 and not self.options.colsector:
                continue
            if x == 7 and not self.options.coltype:
                continue
            if x == 8 and not self.options.colcategory:
                continue
            if x == 9 and not self.options.colweather:
                continue
            if x == 10 and not self.options.colwind:
                continue
            if x == 11 and not self.options.colcomment:
                continue

            self.results_layouts.append(self.create_layout(context, x))
            self.column_layouts.append(self.create_column_layout(context, x))

        num_lines = self.results_layouts[0].get_line_count()

        self.page_breaks = []
        page_height = 0

        for line in xrange(num_lines):
            layout_line = self.results_layouts[0].get_line(line)
            ink_rect, logical_rect = layout_line.get_extents()
            lx, ly, lwidth, lheight = logical_rect
            line_height = lheight / 1024.0
            if page_height + line_height > self.height - self.results_start:
                self.page_breaks.append(line)
                page_height = 0
            page_height += line_height

        operation.set_n_pages(len(self.page_breaks) + 1)

        if self.preview:
            self.preview.start()

    def draw_page (self, operation, context, page_number):
        if page_number == 0:
            start = 0
        else:
            start = self.page_breaks[page_number - 1]

        try:
            end = self.page_breaks[page_number]
        except IndexError:
            end = self.results_layouts[0].get_line_count()

        cr = context.get_cairo_context()
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(0, 0)

        date_page = "%s %s / %s" % (_("Page"), page_number+1,
                                    operation.props.n_pages)
        if self.options.resDate:
            date_page += "\n\n%s" % datetime.date.today()
        self.pagenr_layout.set_text(date_page)
        cr.show_layout(self.pagenr_layout)
        cr.show_layout(self.header_layout)

        cr.move_to(0, self.header_height)
        cr.line_to(context.get_width(), self.header_height)
        cr.set_line_width(0.3)
        cr.stroke()

        for index, column_layout in enumerate(self.results_layouts):
            i = 0
            start_pos_y = 0
            title_height = 0

            if self.options.resColumnNames:
                if index == 0:
                    start_pos_x = 0
                else:
                    size_title = self.column_layouts[index-1].get_size()[0]
                    size_column = self.results_layouts[index-1].get_size()[0]
                    if size_title >= size_column:
                        start_pos_x += \
                            (self.column_layouts[index-1].get_size()[0] /
                             1024.0 + 4)
                    else:
                        start_pos_x += \
                            (self.results_layouts[index-1].get_size()[0] /
                             1024.0 + 4)

                cr.move_to(start_pos_x, start_pos_y + self.results_start)
                cr.show_layout(self.column_layouts[index])
                title_height += \
                            (self.column_layouts[index].get_size()[1] /
                             1024.0 + 2)
            else:
                if index == 0:
                    start_pos_x = 0
                else:
                    start_pos_x += \
                            (self.results_layouts[index-1].get_size()[0] /
                             1024.0 + 4)

            line_iter = column_layout.get_iter()
            while True:
                if i >= start:
                    line = line_iter.get_line()
                    x, logical_rect = line_iter.get_line_extents()
                    lx, ly, lwidth, lheight = logical_rect
                    baseline = line_iter.get_baseline()
                    if i == start:
                        start_pos_y = ly / pango.SCALE
                    cr.move_to(start_pos_x, baseline / 1024.0 - start_pos_y +
                               self.results_start + title_height)
                    cr.show_layout_line(line)
                i += 1
                if not (i < end and line_iter.next_line()):
                    break

    def create_layout(self, context, column):
        text = ''
        for result in self.results:
            text += '%s\n' % result[column]
        layout = context.create_pango_layout()
        font = pango.FontDescription("Arial "+str(self.text_font_size))
        layout.set_font_description(font)
        layout.set_width(int(self.width*pango.SCALE))
        layout.set_wrap(pango.WRAP_CHAR)
        layout.set_text(text)

        return layout

    def create_column_layout(self, context, column):
        layout = context.create_pango_layout()
        font = pango.FontDescription("Arial "+str(self.text_font_size))
        layout.set_font_description(font)
        layout.set_width(int(self.width*pango.SCALE))
        layout.set_markup("<u>%s</u>" %self.columnNames[column])

        return layout

class PrintVelocity(BasePrinting):
    def __init__(self, parent, data, info, options, print_action, pdf_name=''):
        orientation = gtk.PAGE_ORIENTATION_PORTRAIT
        self.options = options
        self.parent = parent
        self.data = data
        self.info = info
        self.preview = None
        BasePrinting.__init__(self, parent, options, print_action, pdf_name,
                              orientation)

    def begin_print(self, operation, context):
        operation.set_n_pages(1)

        # There is no preview button, but Linux users have a printpreview
        # button in the printdialog. Weird things happen if we don't do this.
        if self.preview:
            self.preview.start()

    def draw_page (self, operation, context, page_number):
        cr = context.get_cairo_context()

        total_width = context.get_width()
        font = "Sans"

        cr.select_font_face(font)

        # head
        cr.set_font_size(10)
        cr.move_to(0, 12)
        cr.show_text(_("Velocity"))

        # line
        cr.move_to(0, 15)
        cr.line_to(total_width, 15)

        # info
        cr.set_font_size(6)
        cr.move_to(0, 22)
        cr.show_text("%s: " %_("Date") + self.info[0])
        cr.move_to(0, 30)
        cr.show_text("%s: " %_("Released") + self.info[1])
        cr.move_to(0, 38)
        cr.show_text("%s: " %_("Distance") + str(self.info[2]))

        # line
        cr.move_to(0, 42)
        cr.line_to(total_width, 42)

        # index
        x = 50
        cr.move_to(0, x)
        cr.show_text(_("Velocity"))
        xb, yb, velocitywidth, height, xa, ya = cr.text_extents(_("Velocity"))
        cr.move_to(0, x+2)
        cr.line_to(velocitywidth, x+2)

        cr.move_to(40, x)
        cr.show_text(_("Flight Time"))
        xb, yb, flightwidth, height, xa, ya = \
                                    cr.text_extents(_("Flight Time"))
        cr.move_to(40, x+2)
        cr.line_to(40 + flightwidth, x+2)

        cr.move_to(80, x)
        cr.show_text(_("Time of Arrival"))
        xb, yb, arrivalwidth, height, xa, ya = \
                                    cr.text_extents(_("Time of Arrival"))
        cr.move_to(80, x+2)
        cr.line_to(80 + arrivalwidth, x+2)

        # data
        i = 1
        for data in self.data:
            xb, yb, width, height, xa, ya = cr.text_extents(str(data[0]))
            cr.move_to(0 + (velocitywidth/2-width/2), 50 + 8*i)
            cr.show_text(str(data[0]))
            xb, yb, width, height, xa, ya = cr.text_extents(data[1])
            cr.move_to(40 + (flightwidth/2-width/2), 50 + 8*i)
            cr.show_text(data[1])
            xb, yb, width, height, xa, ya = cr.text_extents(data[2])
            cr.move_to(80 + (arrivalwidth/2-width/2), 50 + 8*i)
            cr.show_text(data[2])

            i += 1

        # final
        cr.set_line_width(0.4)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
      
        cr.stroke()

