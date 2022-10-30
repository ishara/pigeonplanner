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

from gi.repository import Gdk

from pigeonplanner.reportlib.basereport import ReportOptions
from pigeonplanner.reportlib.styles import ParagraphStyle, FontStyle, GraphicsStyle, FONT_SANS_SERIF


paragraph_styles = {}
graphic_styles = {}
paper_margins = {}


def gdkrgba_to_tuple(color: Gdk.RGBA) -> tuple:
    return int(color.red * 255), int(color.green * 255), int(color.blue * 255)


def set_margins(top: float = None, bottom: float = None, left: float = None, right: float = None):
    if top is not None:
        paper_margins["tmargin"] = top
    if bottom is not None:
        paper_margins["bmargin"] = bottom
    if left is not None:
        paper_margins["lmargin"] = left
    if right is not None:
        paper_margins["rmargin"] = right


def set_font_style(style_id: str, size: int = None, color: Gdk.RGBA = None, align: int = None):
    try:
        para_style = paragraph_styles[style_id]
        font_style = para_style.get_font()
    except KeyError:
        para_style = ParagraphStyle()
        font_style = FontStyle()

    font_style.set_type_face(FONT_SANS_SERIF)
    if size is not None:
        font_style.set_size(size)
    if color is not None:
        color_tuple = gdkrgba_to_tuple(color)
        font_style.set_color(color_tuple)
    para_style.set(font=font_style, align=align)
    paragraph_styles[style_id] = para_style
    graph_style = GraphicsStyle()  # TODO: might set attributes to default, we just don't set any custom here (yet)
    graph_style.set_paragraph_style(style_id)
    graphic_styles[style_id] = graph_style


def set_graphics_style(
    style_id: str,
    line_width: float = None,
    line_style: int = None,
    color: Gdk.RGBA = None,
    fill_color: Gdk.RGBA = None,
    para_style: str = None,
):
    graph_style = graphic_styles.get(style_id, GraphicsStyle())
    if line_width is not None:
        graph_style.set_line_width(line_width)
    if line_style is not None:
        graph_style.set_line_style(line_style)
    if color is not None:
        color_tuple = gdkrgba_to_tuple(color)
        graph_style.set_color(color_tuple)
    if fill_color is not None:
        fill_color_tuple = gdkrgba_to_tuple(fill_color)
        graph_style.set_fill_color(fill_color_tuple)
    if para_style is not None:
        graph_style.set_paragraph_style(para_style)
    graphic_styles[style_id] = graph_style


class PedigreeReportOptions(ReportOptions):
    def set_values(self):
        self.margins = paper_margins

    def make_default_style(self, default_style):
        for name, style in paragraph_styles.items():
            default_style.add_paragraph_style(name, style)
        for name, style in graphic_styles.items():
            default_style.add_draw_style(name, style)
