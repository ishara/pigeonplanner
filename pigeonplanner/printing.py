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
import gobject
import cairo
import logging
logger = logging.getLogger(__name__)

import const
import widgets
import messages
from pedigree import DrawPedigree


class BasePrinting:
    def __init__(self, parent, options, print_action, pdf_name):
        self.parent = parent

        if options.paper == 0:
            psize = gtk.PAPER_NAME_A4
        elif options.paper == 1:
            psize = gtk.PAPER_NAME_LETTER
        paper_size = gtk.PaperSize(psize)

        setup = gtk.PageSetup()
        setup.set_paper_size(paper_size)

        print_ = gtk.PrintOperation()
        print_.set_default_page_setup(setup)
        print_.set_unit(gtk.UNIT_MM)
        print_.set_show_progress(True)

        print_.connect("begin_print", self.begin_print)
        print_.connect("draw_page", self.draw_page)

        action = None
        if print_action == 'print':
            action = gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG
        elif print_action == 'preview':
            action = gtk.PRINT_OPERATION_ACTION_PREVIEW
        elif print_action == 'save':
            fc = gtk.FileChooserDialog(title=_("Save as..."), 
                        parent=self.parent,
                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            ftr = gtk.FileFilter()
            ftr.set_name("PDF")
            ftr.add_pattern("*.pdf")
            fc.add_filter(ftr)

            fc.set_current_name("%s.pdf" %pdf_name)
            fc.set_current_folder(const.HOMEDIR)

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
                widgets.message_dialog('error', messages.MSG_PRINTOP_ERROR, self.parent)
            else:
                if response == gtk.PRINT_OPERATION_RESULT_ERROR:
                    print_error = print_.get_error()
                    logger.error("Error printing: %s" %print_error)
                    widgets.message_dialog('error', messages.MSG_PRINT_ERROR)
                elif response == gtk.PRINT_OPERATION_RESULT_APPLY:
                    settings = print_.get_print_settings()


class PrintPedigree(BasePrinting):
    def __init__(self, parent, pigeoninfo, userinfo, options, print_action):
        pdf_name = "pedigree_%s_%s" %(pigeoninfo['ring'], pigeoninfo['year'])
        self.pigeoninfo = pigeoninfo
        self.options = options
        self.userinfo = userinfo
        BasePrinting.__init__(self, parent, options, print_action, pdf_name)

    def begin_print(self, operation, context):
        operation.set_n_pages(1)

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
        ring = "%s / %s" %(self.pigeoninfo['ring'], self.pigeoninfo['year'][2:])
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
            cr.show_text("%s %s" %(self.userinfo['code'], self.userinfo['city']))
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
        if self.options.pigName and self.pigeoninfo['name']:
            name = "%s - " %self.pigeoninfo['name']
        if self.options.pigColour and self.pigeoninfo['colour']:
            colour = "%s - " %self.pigeoninfo['colour']
        if self.options.pigSex:
            sex = self.pigeoninfo['sex']
        info = name + colour + sex
        xb, yb, width, height, xa, ya = cr.text_extents(info)
        cr.move_to(total_width-width, endPigeon)
        cr.show_text(info)
        if info:
            endPigeon += 6

        if self.options.pigExtra:
            cr.set_font_size(4)
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra1'])
            cr.move_to(total_width-width, endPigeon)
            cr.show_text(self.pigeoninfo['extra1'])
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra2'])
            cr.move_to(total_width-width, endPigeon+5)
            cr.show_text(self.pigeoninfo['extra2'])
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra3'])
            cr.move_to(total_width-width, endPigeon+10)
            cr.show_text(self.pigeoninfo['extra3'])
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra4'])
            cr.move_to(total_width-width, endPigeon+15)
            cr.show_text(self.pigeoninfo['extra4'])
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra5'])
            cr.move_to(total_width-width, endPigeon+20)
            cr.show_text(self.pigeoninfo['extra5'])
            xb, yb, width, height, xa, ya = cr.text_extents(self.pigeoninfo['extra6'])
            cr.move_to(total_width-width, endPigeon+25)
            cr.show_text(self.pigeoninfo['extra6'])
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

#Working:
#        pos = [(),
#               ((0, 95, 46, 28), ((48, 109, 85),(48, 109, 133))),
#               ((0, 191, 46, 28), ((48, 205, 181),(48, 205, 229))),
#               ((50, 71, 46, 28), ((98, 85, 73),(98, 85, 97))),
#               ((50, 119, 46, 28), ((98, 133, 121),(98, 133, 145))),
#               ((50, 167, 46, 28), ((98, 181, 169),(98, 181, 193))),
#               ((50, 215, 46, 28), ((98, 229, 217),(98, 229, 241))),
#               ((100, 65, 46, 16), ((148, 73, 67),(148, 73, 79))),
#               ((100, 89, 46, 16), ((148, 97, 91),(148, 97, 103))),
#               ((100, 113, 46, 16), ((148, 121, 115),(148, 121, 127))),
#               ((100, 137, 46, 16), ((148, 145, 139),(148, 145, 151))),
#               ((100, 161, 46, 16), ((148, 169, 163),(148, 169, 175))),
#               ((100, 185, 46, 16), ((148, 193, 187),(148, 193, 199))),
#               ((100, 209, 46, 16), ((148, 217, 211),(148, 217, 223))),
#               ((100, 233, 46, 16), ((148, 241, 235),(148, 241, 247))),
#               ((150, 62, 46, 10), (None)),
#               ((150, 74, 46, 10), (None)),
#               ((150, 86, 46, 10), (None)),
#               ((150, 98, 46, 10), (None)),
#               ((150, 110, 46, 10), (None)),
#               ((150, 122, 46, 10), (None)),
#               ((150, 134, 46, 10), (None)),
#               ((150, 146, 46, 10), (None)),
#               ((150, 158, 46, 10), (None)),
#               ((150, 170, 46, 10), (None)),
#               ((150, 182, 46, 10), (None)),
#               ((150, 194, 46, 10), (None)),
#               ((150, 206, 46, 10), (None)),
#               ((150, 218, 46, 10), (None)),
#               ((150, 230, 46, 10), (None)),
#               ((150, 242, 46, 10), (None))]

#        pos = [(),
#               ((0, 95, 46, 28), ((48, 109, 85),(48, 109, 133))),
#               ((0, 215, 46, 28), ((48, 229, 205),(48, 229, 253))),
#               ((50, 71, 46, 28), ((98, 85, 73),(98, 85, 97))),
#               ((50, 119, 46, 28), ((98, 133, 121),(98, 133, 145))),
#               ((50, 191, 46, 28), ((98, 205, 193),(98, 205, 217))),
#               ((50, 239, 46, 28), ((98, 253, 241),(98, 253, 265))),
#               ((100, 65, 46, 16), ((148, 73, 67),(148, 73, 79))),
#               ((100, 89, 46, 16), ((148, 97, 91),(148, 97, 103))),
#               ((100, 113, 46, 16), ((148, 121, 115),(148, 121, 127))),
#               ((100, 137, 46, 16), ((148, 145, 139),(148, 145, 151))),
#               ((100, 185, 46, 16), ((148, 193, 187),(148, 193, 199))),
#               ((100, 209, 46, 16), ((148, 217, 211),(148, 217, 223))),
#               ((100, 233, 46, 16), ((148, 241, 235),(148, 241, 247))),
#               ((100, 257, 46, 16), ((148, 265, 259),(148, 265, 271))),
#               ((150, 62, 46, 10), (None)),
#               ((150, 74, 46, 10), (None)),
#               ((150, 86, 46, 10), (None)),
#               ((150, 98, 46, 10), (None)),
#               ((150, 110, 46, 10), (None)),
#               ((150, 122, 46, 10), (None)),
#               ((150, 134, 46, 10), (None)),
#               ((150, 146, 46, 10), (None)),
#               ((150, 182, 46, 10), (None)),
#               ((150, 194, 46, 10), (None)),
#               ((150, 206, 46, 10), (None)),
#               ((150, 218, 46, 10), (None)),
#               ((150, 230, 46, 10), (None)),
#               ((150, 242, 46, 10), (None)),
#               ((150, 254, 46, 10), (None)),
#               ((150, 266, 46, 10), (None))]

        lst = [None]*31
        dp = DrawPedigree()
        dp.build_tree(self.pigeoninfo['pindex'], self.pigeoninfo['ring'], self.pigeoninfo['year'],
                      self.pigeoninfo['sex'],
                      '', '', '', '', '', '', 0, 1, lst)

        for i in range(1, 31):
            x = pos[i][0][0]
            y = pos[i][0][1]
            w = pos[i][0][2]
            h = pos[i][0][3]

            cr.rectangle(x, y, w, h)

            if lst[i]:
                cr.move_to(x + 0.5, y + 0.5 + font_size)
                cr.show_text(lst[i][1] + "/" + lst[i][2][2:])

                if i <= 6:
                    height = 6
                elif i >= 7 and i <= 14:
                    height = 3
                else:
                    height = 1

                if height >= 1:
                    cr.move_to(x + 0.5, y + 1.75 + font_size*2)
                    cr.show_text(lst[i][4])
                if height >= 3:
                    cr.move_to(x + 0.5, y + 2.5 + font_size*3)
                    cr.show_text(lst[i][5])
                    cr.move_to(x + 0.5, y + 3 + font_size*4)
                    cr.show_text(lst[i][6])
                if height == 6:
                    cr.move_to(x + 0.5, y + 3.5 + font_size*5)
                    cr.show_text(lst[i][7])
                    cr.move_to(x + 0.5, y + 4 + font_size*6)
                    cr.show_text(lst[i][8])
                    cr.move_to(x + 0.5, y + 4.5 + font_size*7)
                    cr.show_text(lst[i][9])

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


class PrintResults:
    def __init__(self, results, fyearpigeon, fyearrace, fracepoint, fsector, fcoef, fplace):

        self.results = results

        self.fyearpigeon = fyearpigeon
        self.fyearrace = fyearrace
        self.fracepoint = fracepoint
        self.fsector = fsector
        self.fcoef = fcoef
        self.fplace = fplace

        paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)

        setup = gtk.PageSetup()
        setup.set_paper_size(paper_size)

        print_ = gtk.PrintOperation()
        print_.set_default_page_setup(setup)
        print_.set_unit(gtk.UNIT_MM)

        print_.connect("begin_print", self.begin_print)
        print_.connect("draw_page", self.draw_page)

        action = gtk.PRINT_OPERATION_ACTION_PREVIEW
#        action = gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG

        response = print_.run(action)

        if response == gtk.PRINT_OPERATION_RESULT_ERROR:
            widgets.message_dialog('error', messages.MSG_PRINT_ERROR)
        elif response == gtk.PRINT_OPERATION_RESULT_APPLY:
            settings = print_.get_print_settings()

    def begin_print(self, operation, context):
        width = context.get_width()
        height = context.get_height()
        self.layout = context.create_pango_layout()

        num_lines = len(self.results)
        print "num_lines:", num_lines

        lines_first_page = 30
        lines_per_page = height / (4/2)
#        pages = ( int(math.ceil( float(num_lines) / float(self.lines_per_page) ) ) )

#        operation.set_n_pages(pages)

        operation.set_n_pages(2)

    def draw_page (self, operation, context, page_number):
        cr = context.get_cairo_context()

        total_width = context.get_width()
        font = "Sans"

        cr.select_font_face(font)

        # head
        cr.set_font_size(10)
        cr.move_to(0, 12)
        cr.show_text(_("Results"))

        # line
        cr.move_to(0, 15)
        cr.line_to(total_width, 15)

        # address
        cr.set_font_size(6)
        cr.move_to(0, 22)
        cr.show_text(self.options.optionList.name)
        cr.move_to(0, 30)
        cr.show_text(self.options.optionList.street)
        cr.move_to(0, 38)
        cr.show_text(self.options.optionList.code + " " + self.options.optionList.city)
        cr.move_to(0, 46)
        cr.show_text(self.options.optionList.tel)

        # line
        cr.move_to(0, 50)
        cr.line_to(total_width, 50)

        # filters
        prev_width = 0
        words = [_("Year race"), _("Year pigeons"), _("Racepoint"), _("Sector"), _("Coefficient"), _("Place")]
        for word in words:
            xb, yb, width, height, xa, ya = cr.text_extents(word)
            if width > prev_width:
                full_width = width
            prev_width = width

        cr.set_font_size(4)
        cr.move_to(0, 56)
        cr.show_text(_("Year race"))
        cr.move_to(full_width + 10, 56)
        cr.show_text(self.fyearrace)
        cr.move_to(0, 62)
        cr.show_text(_("Year pigeons"))
        cr.move_to(full_width + 10, 62)
        cr.show_text(self.fyearpigeon)
        cr.move_to(0, 68)
        cr.show_text(_("Racepoint"))
        cr.move_to(full_width + 10, 68)
        cr.show_text(self.fracepoint)
        cr.move_to(0, 74)
        cr.show_text(_("Sector"))
        cr.move_to(full_width + 10, 74)
        cr.show_text(self.fsector)
        cr.move_to(0, 80)
        cr.show_text(_("Coefficient"))
        cr.move_to(full_width + 10, 80)
        cr.show_text(str(self.fcoef))
        cr.move_to(0, 86)
        cr.show_text(_("Place"))
        cr.move_to(full_width + 10, 86)
        cr.show_text(str(self.fplace))

        # line
        cr.move_to(0, 90)
        cr.line_to(total_width, 90)

        # index
        cr.move_to(0, 96)
        cr.show_text(_("Band no."))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Band no."))
        cr.move_to(0, 98)
        cr.line_to(width, 98)

        cr.move_to(30, 96)
        cr.show_text(_("Date"))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Date"))
        cr.move_to(30, 98)
        cr.line_to(30 + width, 98)

        cr.move_to(60, 96)
        cr.show_text(_("Racepoint"))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Racepoint"))
        cr.move_to(60, 98)
        cr.line_to(60 + width, 98)

        cr.move_to(100, 96)
        cr.show_text(_("Place"))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Place"))
        cr.move_to(100, 98)
        cr.line_to(100 + width, 98)

        cr.move_to(115, 96)
        cr.show_text(_("Out of"))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Out of"))
        cr.move_to(115, 98)
        cr.line_to(115 + width, 98)

        cr.move_to(130, 96)
        cr.show_text(_("Coef."))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Coef."))
        cr.move_to(130, 98)
        cr.line_to(130 + width, 98)

        cr.move_to(145, 96)
        cr.show_text(_("Sector"))
        xb, yb, width, height, xa, ya = cr.text_extents(_("Sector"))
        cr.move_to(145, 98)
        cr.line_to(145 + width, 98)


        # results
        i = 1
        for result in self.results:
            cr.move_to(0, 98 + 6*i)
            for key, value in result.items():
                cr.show_text(key)
                cr.move_to(30, 98 + 6*i)
                cr.show_text(value[0])
                cr.move_to(60, 98 + 6*i)
                cr.show_text(value[1])
                cr.move_to(100, 98 + 6*i)
                cr.show_text(str(value[2]))
                cr.move_to(115, 98 + 6*i)
                cr.show_text(str(value[3]))
                cr.move_to(130, 98 + 6*i)
                cr.show_text(str(value[4])[:5])
                cr.move_to(145, 98 + 6*i)
                cr.show_text(value[5])

                i += 1

        # final
        cr.set_line_width(0.4)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
      
        cr.stroke()


class PrintVelocity:
    def __init__(self, parent, data, info):

        self.parent = parent
        self.data = data
        self.info = info

        paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)

        setup = gtk.PageSetup()
        setup.set_paper_size(paper_size)

        print_ = gtk.PrintOperation()
        print_.set_default_page_setup(setup)
        print_.set_unit(gtk.UNIT_MM)

        print_.connect("begin_print", self.begin_print)
        print_.connect("draw_page", self.draw_page)

#        action = gtk.PRINT_OPERATION_ACTION_PREVIEW
        action = gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG

        response = print_.run(action, self.parent)

        if response == gtk.PRINT_OPERATION_RESULT_ERROR:
            widgets.message_dialog('error', messages.MSG_PRINT_ERROR)
        elif response == gtk.PRINT_OPERATION_RESULT_APPLY:
            settings = print_.get_print_settings()

    def begin_print(self, operation, context):
        operation.set_n_pages(1)

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
        xb, yb, flightwidth, height, xa, ya = cr.text_extents(_("Flight Time"))
        cr.move_to(40, x+2)
        cr.line_to(40 + flightwidth, x+2)

        cr.move_to(80, x)
        cr.show_text(_("Time of Arrival"))
        xb, yb, arrivalwidth, height, xa, ya = cr.text_extents(_("Time of Arrival"))
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



