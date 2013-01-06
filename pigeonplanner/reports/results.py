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


from translation import gettext as _
from reports.common import HelperMethods
from reportlib.basereport import Report, ReportOptions
from reportlib.styles import (ParagraphStyle, FontStyle,
                              TableStyle, TableCellStyle,
                              FONT_SANS_SERIF, PAPER_LANDSCAPE, PARA_ALIGN_LEFT)


class ResultsReport(Report, HelperMethods):
    def __init__(self, reportopts, results, userinfo, options):
        Report.__init__(self, "My results", reportopts)

        self._results = results
        self._options = options
        self._userinfo = userinfo

    def write_report(self):
        # Header with user details
        self.add_header()

        # Pagenumber and date
        #TODO: how to get pagenr and total pages at this point?
#        self.doc.start_paragraph("pagenr")
#        self.doc.write_text("")
#        self.doc.end_paragraph()

        # Actual results
        #TODO: column size with different columns
        columns = {
                    0: _("Band no."),
                    1: _("Date"),
                    2: _("Racepoint"),
                    3: _("Placed"),
                    4: _("Out of")
                }

        if self._options.colcoef:
            columns[5] = _("Coef.")
        if self._options.colsector:
            columns[6] = _("Sector")
        if self._options.coltype:
            columns[7] = _("Type")
        if self._options.colcategory:
            columns[8] = _("Category")
        if self._options.colweather:
            columns[9] = _("Wind")
        if self._options.colwind:
            columns[10] = _("Weather")
        if self._options.colcomment:
            columns[11] = _("Comment")

        self.doc.start_table("my_table", "table")

        if self._options.resColumnNames:
            self.doc.start_row()
            for name in columns.values():
                self.add_cell(name, "headercell", "colheader")
            self.doc.end_row()

        for row in self._results:
            self.doc.start_row()
            for index, cell in enumerate(row):
                if index not in columns.keys():
                    continue
                self.add_cell(cell, "cell", "celltext")
            self.doc.end_row()
        self.doc.end_table()


class ResultsReportOptions(ReportOptions):

    def set_values(self):
        self.orientation = PAPER_LANDSCAPE

    def make_default_style(self, default_style):
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=12)
        para = ParagraphStyle()
        para.set(font=font, align=PARA_ALIGN_LEFT, bborder=1, bmargin=.5)
        default_style.add_paragraph_style("header", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=6)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("pagenr", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=8, bold=1)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("colheader", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=8)
        para = ParagraphStyle()
        para.set(font=font)
        default_style.add_paragraph_style("celltext", para)

        table = TableStyle()
        table.set_width(100)
        table.set_column_widths([8, 7, 8, 5, 5, 6, 10,
                                 6, 7, 6.5, 6.5, 25])
        default_style.add_table_style('table', table)

        cell = TableCellStyle()
        cell.set_padding(0.1)
        cell.set_borders(0, 1, 0, 0)
        default_style.add_cell_style("headercell", cell)

        cell = TableCellStyle()
        cell.set_padding(0.1)
        cell.set_borders(0, 0, 0, 0)
        default_style.add_cell_style("cell", cell)
