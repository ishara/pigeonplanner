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


from pigeonplanner.core import config
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.reportlib.utils import pt2cm as PT2CM
from pigeonplanner.reportlib.basereport import Report, ReportOptions
from pigeonplanner.reportlib.styles import (ParagraphStyle, FontStyle,
                                            GraphicsStyle, FONT_SANS_SERIF)


class PedigreeReport(Report):
    def __init__(self, reportopts, pigeon, userinfo):
        Report.__init__(self, "My_pedigree", reportopts)

        self._pigeon = pigeon
        self._userinfo = userinfo

    def get_right_align_x(self, style, text):
        style_sheet = self.doc.get_style_sheet()
        style_name = style_sheet.get_draw_style(style)
        style_name = style_name.get_paragraph_style()
        font = style_sheet.get_paragraph_style(style_name).get_font()
        width = self.doc.string_width(font, text)
        return self.doc.get_usable_width() - PT2CM(width)

    def begin_report(self):
        name = ""
        colour = ""
        sex = ""
        if config.get("printing.pedigree-name") and self._pigeon is not None and\
            self._pigeon.name:
            name = "%s - " % self._pigeon.name
        if config.get("printing.pedigree-colour") and self._pigeon is not None and\
            self._pigeon.colour:
            colour = "%s - " % self._pigeon.colour
        if config.get("printing.pedigree-sex") and self._pigeon is not None:
            sex = self._pigeon.sex_string
        self.pigeoninfo = name + colour + sex

    def write_report(self):
        self.doc.start_page()

        # Title line
        band = self._pigeon.get_band_string(True) if self._pigeon is not None else ""
        x_cm = self.get_right_align_x("Title", band)

        self.doc.draw_text("Title", _("Pedigree of:"), .1, 0)
        self.doc.draw_text("Title", band, x_cm, 0)
        self.doc.draw_line("Seperator", 0, 1, self.doc.get_usable_width(), 1)

        # Header
        ## User info
        header_bottom = self._draw_user_info()

        ## Pigeon details
        header_y = 1.2
        header_y_offset = .4
        x_cm = self.get_right_align_x("Header", self.pigeoninfo)
        self.doc.draw_text("Header", self.pigeoninfo, x_cm, header_y)
        header_y += header_y_offset

        if config.get("printing.pedigree-extra"):
            ex1, ex2, ex3, ex4, ex5, ex6 = self._pigeon.extra if\
                self._pigeon is not None else ("", "", "", "", "", "")

            if ex1:
                x_cm = self.get_right_align_x("Header", ex1)
                self.doc.draw_text("Header", ex1, x_cm, header_y)
                header_y += header_y_offset
            if ex2:
                x_cm = self.get_right_align_x("Header", ex2)
                self.doc.draw_text("Header", ex2, x_cm, header_y)
                header_y += header_y_offset
            if ex3:
                x_cm = self.get_right_align_x("Header", ex3)
                self.doc.draw_text("Header", ex3, x_cm, header_y)
                header_y += header_y_offset
            if ex4:
                x_cm = self.get_right_align_x("Header", ex4)
                self.doc.draw_text("Header", ex4, x_cm, header_y)
                header_y += header_y_offset
            if ex5:
                x_cm = self.get_right_align_x("Header", ex5)
                self.doc.draw_text("Header", ex5, x_cm, header_y)
                header_y += header_y_offset
            if ex6:
                x_cm = self.get_right_align_x("Header", ex6)
                self.doc.draw_text("Header", ex6, x_cm, header_y)
                header_y += header_y_offset

        if header_y > header_bottom:
            header_bottom = header_y

        ## Seperator
        header_bottom += .2
        self.doc.draw_line("Seperator", 0, header_bottom,
                            self.doc.get_usable_width(), header_bottom)

        # Pedigree
        lst = [None]*31
        corepigeon.build_pedigree_tree(self._pigeon, 0, 1, lst)

        h_sep = .2
        w_sep = .2
        w = (self.doc.get_usable_width() / 4) - w_sep
        h_total = self.doc.get_usable_height() - (header_bottom + .2)
        y_start = header_bottom + .2
        y_div = (h_total / 16) + y_start
        if config.get("printing.pedigree-box-colour"):
            h1, h2, h3, h4 = 3.1, 3.1, 1.9, 0.9
        else:
            h1, h2, h3, h4 = 2.8, 2.8, 1.6, 0.9

        for index, pigeon in enumerate(lst):
            # Skip first item, it's the selected pigeon
            if index == 0:
                continue

            # Calculate box positions for each vertical row
            if index == 1:
                n_lines = 6
                x = 0
                h = h1
                y_mid = y_div + ((h4 * 8 + h_sep * 7) / 2)
                y = y_mid - (h / 2)
                y_offset = (h4 * 8) + (h_sep * 8)
                left = False
                right = True
                last = False
            elif index == 3:
                n_lines = 6
                x += w + w_sep
                h = h2
                y_mid = y_div + ((h4 * 4 + h_sep * 3) / 2)
                y = y_mid - (h / 2)
                y_offset = (h4 * 4) + (h_sep * 4)
                left = True
                right = True
                last = False
            elif index == 7:
                n_lines = 3
                x += w + w_sep
                h = h3
                y_mid = y_div + ((h4 * 2 + h_sep) / 2)
                y = y_mid - (h / 2)
                y_offset = (h4 * 2) + (h_sep * 2)
                left = True
                right = True
                last = False
            elif index == 15:
                n_lines = 1
                x += w + w_sep
                h = h4
                y_mid = y_div + h / 2
                y = y_div
                y_offset = h + h_sep
                left = True
                right = False
                last = True

            # Get the text
            if pigeon is not None:
                text = pigeon.get_band_string(True)
                ex1, ex2, ex3, ex4, ex5, ex6 = pigeon.extra
                if not last and config.get("printing.pedigree-box-colour"):
                    text += "\n" + pigeon.colour
            else:
                text = ""
                ex1, ex2, ex3, ex4, ex5, ex6 = ("", "", "", "", "", "")

            if n_lines >= 1:
                text += "\n" + ex1
            if n_lines >= 3:
                text += "\n" + ex2
                text += "\n" + ex3
            if n_lines == 6:
                text += "\n" + ex4
                text += "\n" + ex5
                text += "\n" + ex6

            # Draw box with text
            if pigeon is None:
                boxstyle = "PedigreeNone"
            elif pigeon.is_cock():
                boxstyle = "PedigreeCock"
            elif pigeon.is_hen():
                boxstyle = "PedigreeHen"
            else:
                boxstyle = "PedigreeUnknown"

            self.doc.draw_box(boxstyle, text, x, y, w, h)

            # Draw pedigree lines
            if right:
                self.doc.draw_line("PedigreeLine", x + w, y_mid,
                                                   x + w + (w_sep / 2), y_mid)
            if left:
                self.doc.draw_line("PedigreeLine", x, y_mid, x - (w_sep / 2), y_mid)
                if index % 2 == 1:
                    self.doc.draw_line("PedigreeLine", x - (w_sep / 2), y_mid,
                                                       x - (w_sep / 2), y_mid + y_offset)

            # Draw image
            if (index == 22 and config.get("printing.pedigree-image") and
                self._pigeon is not None and
                self._pigeon.main_image is not None):
                # index 22 is last box of first part
                img_y = y + y_offset - (h_sep / 2)
                img_w = w - .2
                img_h = 5

                self.doc.draw_image(self._pigeon.main_image.path, w/2, img_y, img_w, img_h,
                                    xalign="center", yalign="center")

            # Increase y position for next box
            y += y_offset
            y_mid += y_offset

        self.doc.end_page()

    def _draw_user_info(self):
        header_x = .1
        header_y = 1.2
        header_y_offset = .4

        n_lines = [
            config.get("printing.user-name"),
            # Count the address twice as it draws two lines
            config.get("printing.user-address"),
            config.get("printing.user-address"),
            config.get("printing.user-phone"),
            config.get("printing.user-email")
        ].count(True)
        header_bottom = header_y + (n_lines * header_y_offset)

        if self._userinfo is None:
            return header_bottom

        if config.get("printing.user-name"):
            self.doc.draw_text("Header", self._userinfo.name, header_x, header_y)
            header_y += header_y_offset
        if config.get("printing.user-address"):
            self.doc.draw_text("Header", self._userinfo.street, header_x, header_y)
            header_y += header_y_offset
            self.doc.draw_text("Header", "%s %s" % (self._userinfo.zipcode,
                                                    self._userinfo.city),
                                header_x, header_y)
            header_y += header_y_offset
        if config.get("printing.user-phone"):
            self.doc.draw_text("Header", self._userinfo.phone, header_x, header_y)
            header_y += header_y_offset
        if config.get("printing.user-email"):
            self.doc.draw_text("Header", self._userinfo.email, header_x, header_y)
            header_y += header_y_offset

        return header_bottom


class PedigreeReportOptions(ReportOptions):

    def set_values(self):
        self.margins = {"lmargin": 1., "rmargin": 1.}

    def make_default_style(self, default_style):
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=18)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("Title", para)
        g = GraphicsStyle()
        g.set_paragraph_style("Title")
        default_style.add_draw_style("Title", g)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=12)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("Header", para)
        g = GraphicsStyle()
        g.set_paragraph_style("Header")
        default_style.add_draw_style("Header", g)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=8)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("Pedigree", para)
        g = GraphicsStyle()
        g.set_line_width(1)
        g.set_paragraph_style("Pedigree")
        default_style.add_draw_style("PedigreeNone", g)
        gc = GraphicsStyle()
        gc.set_line_width(1)
        if config.get("printing.pedigree-use-box-color"):
            gc.set_color((32, 74, 135))
        if config.get("printing.pedigree-use-box-fill-color"):
            gc.set_fill_color((185, 207, 231))
        gc.set_paragraph_style("Pedigree")
        default_style.add_draw_style("PedigreeCock", gc)
        gh = GraphicsStyle()
        gh.set_line_width(1)
        if config.get("printing.pedigree-use-box-color"):
            gh.set_color((135, 32, 106))
        if config.get("printing.pedigree-use-box-fill-color"):
            gh.set_fill_color((255, 205, 241))
        gh.set_paragraph_style("Pedigree")
        default_style.add_draw_style("PedigreeHen", gh)
        gu = GraphicsStyle()
        gu.set_line_width(1)
        if config.get("printing.pedigree-use-box-color"):
            gu.set_color((100, 100, 100))
        if config.get("printing.pedigree-use-box-fill-color"):
            gu.set_fill_color((200, 200, 200))
        gu.set_paragraph_style("Pedigree")
        default_style.add_draw_style("PedigreeUnknown", gu)

        g = GraphicsStyle()
        g.set_line_width(.6)
        default_style.add_draw_style("PedigreeLine", g)

        g = GraphicsStyle()
        g.set_line_width(1)
        default_style.add_draw_style("Seperator", g)

