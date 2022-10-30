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

import math

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
from gi.repository import PangoCairo

from pigeonplanner import messages
from pigeonplanner import thumbnail
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.ui import utils
from pigeonplanner.ui import component
from pigeonplanner.ui.messagedialog import InfoDialog

try:
    from pigeonplanner.ui.detailsview import DetailsDialog
except SyntaxError:
    # Glade is Python 2 only. Ignore the SyntaxError that's raised further down
    # in this import, the module isn't used through Glade anyway.
    pass


class PedigreeBoxMixin:
    WIDTH = 155
    WIDTH_DETAILED = 230
    HEIGHT = 30

    @property
    def index(self):
        # Widget name should end in an integer and match the index from the pedigree calculation:
        #         - 3
        #    - 1 -
        #    |    - 4
        # 0 -
        #    |    - 5
        #    - 2 -
        #         - 6
        # We assume this is set in Glade.
        # noinspection PyUnresolvedReferences
        return int(self.get_name().split("_")[-1])


class PedigreeBox(Gtk.DrawingArea, PedigreeBoxMixin):
    __gtype_name__ = "PedigreeBox"
    __gsignals__ = {"redraw-pedigree": (GObject.SIGNAL_RUN_LAST, None, ())}
    detailed = GObject.property(type=bool, default=False, nick="Is detailed")

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(self.WIDTH_DETAILED if self.detailed else self.WIDTH, self.HEIGHT)
        self.set_has_tooltip(True)
        self.set_hexpand(True)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self.draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("enter-notify-event", self.on_enter_event)
        self.connect("leave-notify-event", self.on_leave_event)
        self.connect("state-changed", self.state_changed)
        self.connect("query-tooltip", self.on_query_tooltip)
        self.bgcolor = (211 / 256.0, 215 / 256.0, 207 / 256.0)
        self.bordercolor = (0, 0, 0)
        self.pigeon = None
        self.pigeon_child = None
        self.editable = False
        self.highlight = False
        self.text = ""
        self.textlayout = None
        self.text_baseline = 0

    @property
    def sex(self):
        try:
            return self.pigeon.sex
        except AttributeError:
            return (
                enums.Sex.cock
                if (self.index % 2 == 1 or (self.index == 0 and self.pigeon.sex == enums.Sex.cock))
                else enums.Sex.hen
            )

    def set_pigeon(self, pigeon, pigeon_child):
        self.pigeon = pigeon
        self.pigeon_child = pigeon_child

        if self.pigeon:
            self.editable = True
            self.text = self.pigeon.band
            if self.pigeon.is_cock():
                self.bgcolor = (185 / 256.0, 207 / 256.0, 231 / 256.0)
                self.bordercolor = (32 / 256.0, 74 / 256.0, 135 / 256.0)
            elif self.pigeon.is_hen():
                self.bgcolor = (255 / 256.0, 205 / 256.0, 241 / 256.0)
                self.bordercolor = (135 / 256.0, 32 / 256.0, 106 / 256.0)
            else:
                self.bgcolor = (200 / 256.0, 200 / 256.0, 200 / 256.0)
                self.bordercolor = (100 / 256.0, 100 / 256.0, 100 / 256.0)
        else:
            self.editable = False
            self.text = ""
            self.bgcolor = (211 / 256.0, 215 / 256.0, 207 / 256.0)
            self.bordercolor = (0, 0, 0)
            if self.detailed and pigeon_child is not None:
                self.editable = True
                tform = '<span style="italic" foreground="#6a6a6a">%s</span>'
                self.text = tform % common.escape_text(_("<edit>"))

    def set_highlight(self, value):
        self.highlight = value
        self.queue_draw()

    def on_enter_event(self, _widget, _event):
        if self.editable:
            self.set_highlight(True)

    def on_leave_event(self, _widget, _event):
        self.set_highlight(False)

    def state_changed(self, widget, _prev_state):
        if widget.get_state() == Gtk.StateType.INSENSITIVE:
            self.text = '<span foreground="#6a6a6a">%s</span>' % self.text
            self.bgcolor = (211 / 256.0, 215 / 256.0, 207 / 256.0)
        self.queue_draw()

    def on_query_tooltip(self, _widget, _x, _y, _keyboard, tooltip):
        if self.pigeon is None:
            return False
        image = self.pigeon.main_image
        if image is not None and image.exists:
            tooltip.set_icon(thumbnail.get_image(image.path))
            return True
        return False

    def on_button_press(self, _widget, event):
        if self.detailed:
            if not self.editable:
                return
            if event.button == Gdk.BUTTON_PRIMARY:
                self._edit_pigeon_details(None)
            elif event.button == Gdk.BUTTON_SECONDARY:
                entries = [(self._edit_pigeon_details, None, _("Edit"))]
                if self.pigeon is not None:
                    entries.insert(0, (self._show_pigeon_details, None, _("Information")))
                    if not self.pigeon.visible:
                        entries.append((self._clear_box, None, _("Clear")))
                        entries.append((self._remove_pigeon, None, _("Remove")))
                utils.popup_menu(event, entries)
        else:
            if self.pigeon is None:
                return
            if event.button == Gdk.BUTTON_PRIMARY:
                self._show_pigeon_details(None)
            elif event.button == Gdk.BUTTON_SECONDARY:
                entries = [
                    (self._show_pigeon_details, None, _("Information")),
                    (self._select_pigeon, None, _("Go to")),
                ]
                utils.popup_menu(event, entries)
        return True

    def draw(self, _widget, context):
        alloc = self.get_allocation()

        if not self.textlayout:
            self.textlayout = PangoCairo.create_layout(context)
            font_desc = self.get_style_context().get_font(Gtk.StateFlags.NORMAL)
            font_size = int(font_desc.get_size() / Pango.SCALE)
            self.text_baseline = -font_size + 15
            self.textlayout.set_font_description(font_desc)
            self.textlayout.set_ellipsize(Pango.EllipsizeMode.END)
        self.textlayout.set_width(Pango.units_from_double(alloc.width - 8))
        self.textlayout.set_markup(self.text, -1)

        context.move_to(0, 5)
        context.curve_to(0, 2, 2, 0, 5, 0)
        context.line_to(alloc.width - 8, 0)
        context.curve_to(alloc.width - 5, 0, alloc.width - 3, 2, alloc.width - 3, 5)
        context.line_to(alloc.width - 3, alloc.height - 8)
        context.curve_to(
            alloc.width - 3, alloc.height - 5, alloc.width - 5, alloc.height - 3, alloc.width - 8, alloc.height - 3
        )
        context.line_to(5, alloc.height - 3)
        context.curve_to(2, alloc.height - 3, 0, alloc.height - 5, 0, alloc.height - 8)
        context.close_path()
        path = context.copy_path()

        context.save()
        context.translate(3, 3)
        context.new_path()
        context.append_path(path)
        context.set_source_rgba(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2], 0.4)
        context.fill_preserve()
        context.set_line_width(0)
        context.stroke()
        context.restore()

        context.append_path(path)
        context.clip()

        context.append_path(path)
        context.set_source_rgb(*self.bgcolor)
        context.fill_preserve()
        context.stroke()

        context.move_to(5, self.text_baseline)
        context.set_source_rgb(0, 0, 0)
        PangoCairo.show_layout(context, self.textlayout)

        width = 5 if self.highlight else 2
        context.set_line_width(width)
        context.append_path(path)
        context.set_source_rgb(*self.bordercolor)
        context.stroke()

    def on_edit_finished(self, _detailsview, pigeon, _operation):
        self.pigeon = pigeon
        self._edit_child_parent(False)
        self.emit("redraw-pedigree")

    def _select_pigeon(self, _widget):
        if not component.get("Treeview").select_pigeon(None, self.pigeon):
            InfoDialog(messages.MSG_NO_PIGEON, self.get_toplevel())

    def _show_pigeon_details(self, _widget):
        DetailsDialog(self.pigeon, self.get_toplevel())

    def _edit_pigeon_details(self, _widget):
        mode = enums.Action.add if self.pigeon is None else enums.Action.edit
        dialog = DetailsDialog(self.pigeon, self.get_toplevel(), mode)
        dialog.details.set_pedigree_mode(True)
        dialog.details.set_sex(self.sex)
        dialog.details.connect("edit-finished", self.on_edit_finished)

    def _edit_child_parent(self, clear):
        if self.pigeon_child is None:
            return
        if clear:
            parent = None
        else:
            parent = self.pigeon
        if self.pigeon.is_cock():
            self.pigeon_child.sire = parent
        else:
            self.pigeon_child.dam = parent
        self.pigeon_child.save()

    def _clear_box(self, _widget):
        self._edit_child_parent(True)
        self.emit("redraw-pedigree")

    def _remove_pigeon(self, _widget):
        corepigeon.remove_pigeon(self.pigeon)
        main_treeview = component.get("Treeview")
        main_path = main_treeview.get_path_for_pigeon(self.pigeon)
        if main_path is not None:
            main_treeview.remove_row(main_path)
        self._edit_child_parent(True)
        self.emit("redraw-pedigree")


class PedigreeExtraBox(Gtk.DrawingArea, PedigreeBoxMixin):
    __gtype_name__ = "PedigreeExtraBox"
    num_lines = GObject.property(type=int, default=6, minimum=1, maximum=6, nick="Num lines")

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self.draw)
        self.set_size_request(self.WIDTH_DETAILED, self.HEIGHT)

        self.text = ""
        self.textlayout = None
        self.bgcolor = (211 / 256.0, 215 / 256.0, 207 / 256.0)
        self.bordercolor = (0, 0, 0)

    def set_pigeon(self, pigeon, _pigeon_child):
        if pigeon is not None:
            self.text = common.escape_text("\n".join(pigeon.extra[: self.num_lines]))
            self.bgcolor = (240 / 256.0, 230 / 256.0, 140 / 256.0)
            self.bordercolor = (0, 0, 0)
        else:
            self.text = ""
            self.bgcolor = (211 / 256.0, 215 / 256.0, 207 / 256.0)
            self.bordercolor = (0, 0, 0)

    def draw(self, _widget, context):
        alloc = self.get_allocation()

        if not self.textlayout:
            self.textlayout = PangoCairo.create_layout(context)
            font_desc = self.get_style_context().get_font(Gtk.StateFlags.NORMAL)
            self.textlayout.set_font_description(font_desc)
            self.textlayout.set_ellipsize(Pango.EllipsizeMode.END)
        self.textlayout.set_width(Pango.units_from_double(alloc.width - 8))
        self.textlayout.set_markup(self.text, -1)

        context.move_to(0, 5)
        context.curve_to(0, 2, 2, 0, 5, 0)
        context.line_to(alloc.width - 8, 0)
        context.curve_to(alloc.width - 5, 0, alloc.width - 3, 2, alloc.width - 3, 5)
        context.line_to(alloc.width - 3, alloc.height - 8)
        context.curve_to(
            alloc.width - 3, alloc.height - 5, alloc.width - 5, alloc.height - 3, alloc.width - 8, alloc.height - 3
        )
        context.line_to(5, alloc.height - 3)
        context.curve_to(2, alloc.height - 3, 0, alloc.height - 5, 0, alloc.height - 8)
        context.close_path()
        path = context.copy_path()

        context.save()
        context.translate(3, 3)
        context.new_path()
        context.append_path(path)
        context.set_source_rgba(self.bordercolor[0], self.bordercolor[1], self.bordercolor[2], 0.4)
        context.fill_preserve()
        context.set_line_width(0)
        context.stroke()
        context.restore()

        context.append_path(path)
        context.clip()

        context.append_path(path)
        context.set_source_rgb(*self.bgcolor)
        context.fill_preserve()
        context.stroke()

        context.move_to(5, 4)
        context.set_source_rgb(0, 0, 0)
        PangoCairo.show_layout(context, self.textlayout)

        context.set_line_width(2)
        context.append_path(path)
        context.set_source_rgb(*self.bordercolor)
        context.stroke()


class PedigreeBoxJoin(Gtk.DrawingArea):
    __gtype_name__ = "PedigreeBoxJoin"

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(12, -1)
        self.connect("draw", self.draw)

    # noinspection PyMethodMayBeStatic
    def draw(self, area, context):
        alloc = area.get_allocation()
        height_offset = PedigreeBoxMixin.HEIGHT / 2

        context.set_dash([], 0)
        context.set_line_width(2)

        if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL:
            context.translate(alloc.width, alloc.height)
            context.rotate(math.pi)

        context.move_to(0, alloc.height / 2)
        context.line_to(alloc.width / 2, alloc.height / 2)
        context.line_to(alloc.width / 2, 0 + height_offset)
        context.line_to(alloc.width, 0 + height_offset)
        context.move_to(alloc.width / 2, alloc.height / 2)
        context.line_to(alloc.width / 2, alloc.height - height_offset)
        context.line_to(alloc.width, alloc.height - height_offset)

        context.stroke()
