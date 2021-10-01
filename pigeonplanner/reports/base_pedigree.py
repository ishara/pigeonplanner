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

from typing import List, Optional

from pigeonplanner.core import enums
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.database.models import Pigeon, Person
from pigeonplanner.reportlib.utils import pt2cm
from pigeonplanner.reportlib.basereport import Report


class PedigreeReport(Report):
    def __init__(self, reportopts, pigeon: Pigeon, userinfo: Person, layout: dict):
        Report.__init__(self, "My_pedigree", reportopts)

        self._pigeon = pigeon
        self._userinfo = userinfo
        self._layout = layout

    def write_report(self):
        self.doc.start_page()

        title_y = self._draw_title()
        user_y = self._draw_user_info(title_y)
        pigeon_y = self._draw_pigeon_info(title_y)
        image_y = self._draw_pigeon_image(title_y)
        separator_y = self._draw_header_separator(title_y, user_y, pigeon_y, image_y)
        self._draw_pedigree(separator_y)

        self.doc.end_page()

    def get_right_align_x(self, style_name: str, text: str) -> float:
        style_sheet = self.doc.get_style_sheet()
        style_name = style_sheet.get_draw_style(style_name)
        style_name = style_name.get_paragraph_style()
        font = style_sheet.get_paragraph_style(style_name).get_font()
        width = self.doc.string_width(font, text)
        return self.doc.get_usable_width() - pt2cm(width)

    def get_text_height(self, style_name: str) -> float:
        style_sheet = self.doc.get_style_sheet()
        style_name = style_sheet.get_draw_style(style_name)
        style_name = style_name.get_paragraph_style()
        font_style = style_sheet.get_paragraph_style(style_name).get_font()
        font_size = font_style.get_size()
        # TODO: Count and add spacing around text (see libcairodoc.GtkDocText), document this? Get value from there?
        return pt2cm(int(round(font_size + font_size * 0.2)))

    def _draw_title(self) -> float:
        text_height = self.get_text_height("Title")
        line_y = text_height + text_height * 0.15
        self.doc.draw_text("Title", _("Pedigree of:"), 0.1, 0)
        if self._pigeon is not None:
            band_x = self.get_right_align_x("Title", self._pigeon.band)
            self.doc.draw_text("Title", self._pigeon.band, band_x, 0)
        self.doc.draw_line("TitleSeparator", 0, line_y, self.doc.get_usable_width(), line_y)
        return line_y

    def _draw_user_info(self, title_y: float) -> float:
        if self._layout["options"]["user_info"] == "no_show" or self._userinfo is None:
            return 0.0
        elif self._layout["options"]["user_info"] == "left":
            header_x = 0.1
        elif self._layout["options"]["user_info"] == "right":
            header_x = self.doc.get_usable_width()
        else:  # Center
            header_x = self.doc.get_usable_width() / 2
        header_y = title_y + 0.2

        user_info = []
        if self._layout["options"]["user_name"]:
            user_info.append(self._userinfo.name)
        if self._layout["options"]["user_address"]:
            user_info.append(self._userinfo.street)
            user_info.append("%s %s" % (self._userinfo.zipcode, self._userinfo.city))
        if self._layout["options"]["user_phone"]:
            user_info.append(self._userinfo.phone)
        if self._layout["options"]["user_email"]:
            user_info.append(self._userinfo.email)
        self.doc.draw_text("UserInfo", "\n".join(user_info), header_x, header_y)
        height = sum(self.get_text_height("UserInfo") for _ in user_info)
        return height + header_y

    def _draw_pigeon_image(self, title_y: float) -> float:
        pigeon_image_location = self._layout["options"]["pigeon_image"]
        if (
            pigeon_image_location == "no_show"
            or self._pigeon is None
            or self._pigeon.main_image is None
            or not self._pigeon.main_image.exists
        ):
            return 0.0

        if pigeon_image_location == "left":
            img_x = 0
            img_x_align = "left"
        elif pigeon_image_location == "right":
            img_x = self.doc.get_usable_width()
            img_x_align = "right"
        else:  # Center
            img_x = self.doc.get_usable_width() / 2
            img_x_align = "center"

        img_y = title_y + 0.2
        img_w = 6
        img_h = 3

        self.doc.draw_image(
            self._pigeon.main_image.path, img_x, img_y, img_w, img_h, xalign=img_x_align, yalign="top"
        )
        return img_h + img_y

    def _draw_pigeon_info(self, title_y: float) -> float:
        if self._pigeon is None:
            return title_y

        if self._layout["options"]["pigeon_info"] == "no_show":
            return 0.0
        elif self._layout["options"]["pigeon_info"] == "left":
            header_x = 0.1
        elif self._layout["options"]["pigeon_info"] == "right":
            header_x = self.doc.get_usable_width()
        else:  # Center
            header_x = self.doc.get_usable_width() / 2
        header_y = title_y + 0.2

        details = []
        pigeon_info = []
        if self._layout["options"]["pigeon_name"] and self._pigeon.name:
            details.append(self._pigeon.name)
        if self._layout["options"]["pigeon_colour"] and self._pigeon.colour:
            if len(details) != 0:
                details.append(" - ")
            details.append(self._pigeon.colour)
        if self._layout["options"]["pigeon_sex"]:
            if len(details) != 0:
                details.append(" - ")
            details.append(self._pigeon.sex_string)
        if details:
            pigeon_info.append("".join(details))
        if self._layout["options"]["pigeon_extra"]:
            pigeon_info.extend(self._pigeon.extra)

        self.doc.draw_text("PigeonInfo", "\n".join(pigeon_info), header_x, header_y)
        height = sum(self.get_text_height("PigeonInfo") for _ in pigeon_info)
        return height + header_y

    def _draw_header_separator(self, title_y: float, user_y: float, pigeon_y: float, image_y: float) -> float:
        if sum([user_y, pigeon_y, image_y]) == 0:
            return title_y
        separator_y = max(title_y, user_y, pigeon_y, image_y)
        separator_y += separator_y * 0.08
        self.doc.draw_line("HeaderSeparator", 0, separator_y, self.doc.get_usable_width(), separator_y)
        return separator_y

    def _calculate_box_height(
        self,
        top_line_height: float,
        details_line_height: float,
        comments_line_height: float,
        n_lines_allowed: int,
        box_text_offset_y: float,
    ) -> float:
        box_height = top_line_height
        n_lines = 1
        if (
            self._layout["options"]["box_middle_left"] != "empty"
            or self._layout["options"]["box_middle_right"] != "empty"
            and n_lines < n_lines_allowed
        ):
            box_height += details_line_height
            n_lines += 1
        if self._layout["options"]["box_bottom_left"] != "empty" and n_lines < n_lines_allowed:
            box_height += details_line_height
            n_lines += 1
        n_lines_comments = n_lines_allowed - n_lines
        box_height += comments_line_height * n_lines_comments
        # TODO: on closer look, the below changes depending on zoom level. This can get ugly...
        #       Save to PDF to be sure. Looks like zoom level 1 is correct.
        box_height += box_text_offset_y * min(2, n_lines_allowed - 1)  # TODO: better, still wrong with 3 lines?
        box_height = max(box_height, top_line_height + details_line_height + box_text_offset_y)
        return box_height

    def _draw_pedigree(self, header_bottom):
        pedigree_lst: List[Optional[Pigeon]] = [None] * 31
        corepigeon.build_pedigree_tree(self._pigeon, 0, 1, pedigree_lst)

        box_separator_w = 0.2
        box_separator_h = 0.2
        box_width = (self.doc.get_usable_width() / 4) - box_separator_w
        start_y = header_bottom + 0.4

        gen1_n_lines_allowed = self._layout["options"]["pedigree_gen_1_lines"]
        gen2_n_lines_allowed = self._layout["options"]["pedigree_gen_2_lines"]
        gen3_n_lines_allowed = self._layout["options"]["pedigree_gen_3_lines"]
        gen4_n_lines_allowed = self._layout["options"]["pedigree_gen_4_lines"]

        box_text_offset_x = 0.08
        box_text_offset_y = 0.08

        # calculate heights
        band_line_height = self.get_text_height("PedigreeBoxBand")
        details_line_height = self.get_text_height("PedigreeBoxDetailsLeft")
        comments_line_height = self.get_text_height("PedigreeBoxComments")
        top_line_height = max(band_line_height, details_line_height)

        gen_1_box_height = self._calculate_box_height(
            top_line_height, details_line_height, comments_line_height, gen1_n_lines_allowed, box_text_offset_y
        )
        gen_2_box_height = self._calculate_box_height(
            top_line_height, details_line_height, comments_line_height, gen2_n_lines_allowed, box_text_offset_y
        )
        gen_3_box_height = self._calculate_box_height(
            top_line_height, details_line_height, comments_line_height, gen3_n_lines_allowed, box_text_offset_y
        )
        gen_4_box_height = self._calculate_box_height(
            top_line_height, details_line_height, comments_line_height, gen4_n_lines_allowed, box_text_offset_y
        )

        sex_symbol_map = {
            enums.Sex.cock: "\u2642",
            enums.Sex.hen: "\u2640",
        }

        x = 0
        y = 0
        y_mid = 0
        y_offset = 0
        box_height = 0
        n_lines_allowed = 0
        for index, pigeon in enumerate(pedigree_lst):
            gen_0 = index == 0
            gen_1 = 1 <= index <= 2
            gen_2 = 3 <= index <= 6
            gen_3 = 7 <= index <= 14
            gen_4 = 15 <= index <= 31

            # Calculate box dimensions and coordinates
            if index == 0:
                box_height = gen_1_box_height  # TODO: height ok?
                x = 0
                y_mid = start_y + ((gen_4_box_height * 16 + box_separator_h * 15) / 2)
                y = y_mid - (gen_1_box_height / 2)  # TODO: was h0, now gen0 and gen1 are the same
                y_offset = (gen_4_box_height * 8) + (box_separator_h * 8)
                n_lines_allowed = gen1_n_lines_allowed
            elif index == 1:
                box_height = gen_1_box_height
                x = 0
                y_mid = start_y + ((gen_4_box_height * 8 + box_separator_h * 7) / 2)
                y = y_mid - (gen_1_box_height / 2)
                y_offset = (gen_4_box_height * 8) + (box_separator_h * 8)
                n_lines_allowed = gen1_n_lines_allowed
            elif index == 3:
                box_height = gen_2_box_height
                x += box_width + box_separator_w
                y_mid = start_y + ((gen_4_box_height * 4 + box_separator_h * 3) / 2)
                y = y_mid - (gen_2_box_height / 2)
                y_offset = (gen_4_box_height * 4) + (box_separator_h * 4)
                n_lines_allowed = gen2_n_lines_allowed
            elif index == 7:
                box_height = gen_3_box_height
                x += box_width + box_separator_w
                y_mid = start_y + ((gen_4_box_height * 2 + box_separator_h) / 2)
                y = y_mid - (box_height / 2)
                y_offset = (gen_4_box_height * 2) + (box_separator_h * 2)
                n_lines_allowed = gen3_n_lines_allowed
            elif index == 15:
                box_height = gen_4_box_height
                x += box_width + box_separator_w
                y_mid = start_y + box_height / 2
                y = start_y
                y_offset = box_height + box_separator_h
                n_lines_allowed = gen4_n_lines_allowed

            if index == 0:
                if self._layout["options"]["pedigree_layout_pigeon"] == "no_show":
                    continue
                if self._layout["options"]["pedigree_layout_pigeon"] == "image":
                    if self._pigeon is None or self._pigeon.main_image is None or not self._pigeon.main_image.exists:
                        continue
                    img_w = box_width - 0.2
                    img_h = 5
                    self.doc.draw_image(
                        self._pigeon.main_image.path, x, y_mid, img_w, img_h, xalign="left", yalign="center"
                    )
                    continue
                if self._layout["options"]["pedigree_layout_pigeon"] == "details":
                    pass

            # Draw box
            if pigeon is None:
                boxstyle = "PedigreeBoxNone"
            elif pigeon.is_cock():
                boxstyle = "PedigreeBoxCock"
            elif pigeon.is_hen():
                boxstyle = "PedigreeBoxHen"
            else:
                boxstyle = "PedigreeBoxUnknown"
            self.doc.draw_box(boxstyle, None, x, y, box_width, box_height)

            # Get the text
            top_right = None
            middle_left = None
            middle_right = None
            bottom_left = None
            comments = None
            if pigeon is None:
                bandnumber = ""
            else:
                bandnumber = pigeon.band
                if self._layout["options"]["pedigree_sex_sign"] and pigeon.sex in sex_symbol_map:
                    bandnumber = bandnumber + "  %s" % sex_symbol_map[pigeon.sex]
                if self._layout["options"]["box_top_right"] != "empty":
                    top_right = getattr(pigeon, self._layout["options"]["box_top_right"])
                if self._layout["options"]["box_middle_left"] != "empty":
                    middle_left = getattr(pigeon, self._layout["options"]["box_middle_left"])
                if self._layout["options"]["box_middle_right"] != "empty":
                    middle_right = getattr(pigeon, self._layout["options"]["box_middle_right"])
                if self._layout["options"]["box_bottom_left"] != "empty":
                    bottom_left = getattr(pigeon, self._layout["options"]["box_bottom_left"])
                if self._layout["options"]["box_comments"]:
                    comments = pigeon.extra

            # Draw text
            n_lines = 1
            has_middle_line = False
            has_bottom_line = False
            self.doc.draw_text("PedigreeBoxBand", bandnumber, x + box_text_offset_x, y + box_text_offset_y)
            if top_right is not None:
                self.doc.draw_text(
                    "PedigreeBoxDetailsRight", top_right, x + box_width - box_text_offset_x, y + box_text_offset_y
                )
            if middle_left is not None and n_lines < n_lines_allowed:
                has_middle_line = True
                self.doc.draw_text(
                    "PedigreeBoxDetailsLeft",
                    middle_left,
                    x + box_text_offset_x,
                    y + top_line_height + box_text_offset_y,
                )
            if middle_right is not None and n_lines < n_lines_allowed:
                has_middle_line = True
                self.doc.draw_text(
                    "PedigreeBoxDetailsRight",
                    middle_right,
                    x + box_width - box_text_offset_x,
                    y + top_line_height + box_text_offset_y,
                )
            n_lines += 1 if has_middle_line else 0
            if bottom_left is not None and n_lines < n_lines_allowed:
                n_lines += 1
                has_bottom_line = True
                bottom_line_y = y + top_line_height + box_text_offset_y
                if has_middle_line:
                    bottom_line_y += details_line_height
                self.doc.draw_text("PedigreeBoxDetailsLeft", bottom_left, x + box_text_offset_x, bottom_line_y)
            if comments is not None:
                comments_y = y + top_line_height + box_text_offset_y
                if has_middle_line:
                    comments_y += details_line_height
                if has_bottom_line:
                    comments_y += details_line_height
                comments_str = "\n".join(comments[: n_lines_allowed - n_lines])
                self.doc.draw_text("PedigreeBoxComments", comments_str, x + box_text_offset_x, comments_y)

            # Draw pedigree lines
            if gen_1 or gen_2 or gen_3:
                self.doc.draw_line("PedigreeLine", x + box_width, y_mid, x + box_width + (box_separator_w / 2), y_mid)
            if gen_2 or gen_3 or gen_4:
                self.doc.draw_line("PedigreeLine", x, y_mid, x - (box_separator_w / 2), y_mid)
                if index % 2 == 1:
                    self.doc.draw_line(
                        "PedigreeLine", x - (box_separator_w / 2), y_mid, x - (box_separator_w / 2), y_mid + y_offset
                    )
            if gen_0:
                self.doc.draw_line("PedigreeLine", x + box_width / 2, y, x + box_width / 2, y - 3.8)
                self.doc.draw_line(
                    "PedigreeLine", x + box_width / 2, y + box_height, x + box_width / 2, y + box_height + 3.8
                )

            # Increase y position for next box
            y += y_offset
            y_mid += y_offset
