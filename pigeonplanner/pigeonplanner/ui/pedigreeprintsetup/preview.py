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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject

from pigeonplanner.ui import builder


PRINTER_DPI = 72.0

MARGIN = 6

(
    ZOOM_BEST_FIT,
    ZOOM_FIT_WIDTH,
    ZOOM_FREE,
) = range(3)


class PrintPreviewWidget(Gtk.Box, builder.WidgetFactory):
    zoom_factors = {
        0.50: "50%",
        0.75: "75%",
        1.00: "100%",
        1.25: "125%",
        1.50: "150%",
        1.75: "175%",
        2.00: "200%",
        3.00: "300%",
        4.00: "400%",
    }

    _instance = None

    def __init__(self, setup_instance=None):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        builder.WidgetFactory.__init__(self)

        self._setup_instance = setup_instance

        self.set_hexpand(True)

        self._operation = None
        self._preview = None
        self._context = None
        self._paper_width = None
        self._paper_height = None
        self._page_width = None
        self._page_height = None
        self._zoom_mode = ZOOM_FREE
        self._zoom = 1.0
        self._last_x = 0
        self._last_y = 0
        self._is_dragging = False

        self.widgets.drawingarea = Gtk.DrawingArea()
        self.widgets.drawingarea.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.BUTTON_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        self.widgets.drawingarea.connect("draw", self.on_drawingarea_draw)
        self.widgets.drawingarea.connect("button-press-event", self.on_button_press_event)
        self.widgets.drawingarea.connect("button-release-event", self.on_button_release_event)
        self.widgets.drawingarea.connect("motion-notify-event", self.on_motion_notify_event)
        self.widgets.drawingarea.connect("scroll-event", self.on_scroll_event)
        self.widgets.swin = Gtk.ScrolledWindow()
        self.widgets.swin.connect("size-allocate", self.on_swin_size_allocate)
        self.widgets.swin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.widgets.swin.add_with_viewport(self.widgets.drawingarea)
        self.pack_end(self.widgets.swin, True, True, 0)

        self.__build_toolbar()
        self.show_all()

    @classmethod
    def get_instance(cls, setup_instance=None):
        if cls._instance is None:
            cls._instance = cls(setup_instance=setup_instance)
        return cls._instance

    @classmethod
    def destroy_instance(cls):
        cls._instance = None

    def __build_toolbar(self):
        image_save = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        button_save = Gtk.Button(label=_("Save PDF"), image=image_save, always_show_image=True)
        button_save.connect("clicked", self.on_save_clicked)
        image_print = Gtk.Image.new_from_icon_name("document-print-symbolic", Gtk.IconSize.BUTTON)
        button_print = Gtk.Button(label=_("Print"), image=image_print, always_show_image=True)
        button_print.connect("clicked", self.on_print_clicked)
        box_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box_actions.get_style_context().add_class("linked")
        box_actions.pack_start(button_save, False, False, 0)
        box_actions.pack_start(button_print, False, False, 0)

        image_zoom_fit_width = Gtk.Image.new_from_icon_name("zoom-fit-best-symbolic", Gtk.IconSize.BUTTON)
        self._zoom_fit_width_button = Gtk.ToggleButton(image=image_zoom_fit_width)
        self._zoom_fit_width_button.connect("toggled", self.on_zoom_fit_width_toggled)
        self._zoom_fit_width_button.set_tooltip_text(_("Zooms to fit the page width"))
        image_zoom_best_fit = Gtk.Image.new_from_icon_name("zoom-fit-best-symbolic", Gtk.IconSize.BUTTON)
        self._zoom_best_fit_button = Gtk.ToggleButton(image=image_zoom_best_fit)
        self._zoom_best_fit_button.connect("toggled", self.on_zoom_best_fit_toggled)
        self._zoom_best_fit_button.set_tooltip_text(_("Zooms to fit the whole page"))
        self._zoom_original_button = Gtk.Button.new_from_icon_name("zoom-original-symbolic", Gtk.IconSize.BUTTON)
        self._zoom_original_button.connect("clicked", self.on_zoom_original_clicked)
        self._zoom_in_button = Gtk.Button.new_from_icon_name("zoom-in-symbolic", Gtk.IconSize.BUTTON)
        self._zoom_in_button.connect("clicked", self.on_zoom_in_clicked)
        self._zoom_in_button.set_tooltip_text(_("Zooms the page in"))
        self._zoom_out_button = Gtk.Button.new_from_icon_name("zoom-out-symbolic", Gtk.IconSize.BUTTON)
        self._zoom_out_button.connect("clicked", self.on_zoom_out_clicked)
        self._zoom_out_button.set_tooltip_text(_("Zooms the page out"))
        box_zoom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box_zoom.get_style_context().add_class("linked")
        box_zoom.pack_start(self._zoom_fit_width_button, False, False, 0)
        box_zoom.pack_start(self._zoom_best_fit_button, False, False, 0)
        box_zoom.pack_start(self._zoom_original_button, False, False, 0)
        box_zoom.pack_start(self._zoom_in_button, False, False, 0)
        box_zoom.pack_start(self._zoom_out_button, False, False, 0)

        button_quit = Gtk.Button.new_from_icon_name("window-close", Gtk.IconSize.BUTTON)
        button_quit.connect("clicked", self.on_quit_clicked)
        button_quit.set_tooltip_text(_("Close this window"))
        box_window = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box_window.get_style_context().add_class("linked")
        box_window.pack_start(button_quit, False, False, 0)

        box_outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, border_width=10)
        box_outer.pack_start(box_actions, False, False, 0)
        box_outer.pack_start(box_zoom, False, False, 0)
        box_outer.pack_start(box_window, False, False, 0)

        self.pack_start(box_outer, False, False, 0)

    def __set_zoom(self, zoom):
        self._zoom = zoom

        screen_width = int(self._paper_width * self._zoom + 2 * MARGIN)
        screen_height = int(self._paper_height * self._zoom + 2 * MARGIN)
        self.widgets.drawingarea.set_size_request(screen_width, screen_height)
        self.widgets.drawingarea.queue_draw()

        self._zoom_in_button.set_sensitive(self._zoom != max(self.zoom_factors))
        self._zoom_out_button.set_sensitive(self._zoom != min(self.zoom_factors))

    def __zoom_in(self):
        zoom = [z for z in self.zoom_factors if z > self._zoom]

        if zoom:
            return min(zoom)
        else:
            return self._zoom

    def __zoom_out(self):
        zoom = [z for z in self.zoom_factors if z < self._zoom]

        if zoom:
            return max(zoom)
        else:
            return self._zoom

    def __zoom_fit_width(self):
        width, height, vsb_w, hsb_h = self.__get_view_size()

        zoom = width / self._paper_width
        if self._paper_height * zoom > height:
            zoom = (width - vsb_w) / self._paper_width

        return zoom

    def __zoom_best_fit(self):
        width, height, vsb_w, hsb_h = self.__get_view_size()

        zoom = min(width / self._paper_width, height / self._paper_height)

        return zoom

    def __get_view_size(self):
        width = self.widgets.swin.get_allocated_width() - 2 * MARGIN
        height = self.widgets.swin.get_allocated_height() - 2 * MARGIN

        if self.widgets.swin.get_shadow_type() != Gtk.ShadowType.NONE:
            width -= 2 * self.widgets.swin.get_style().xthickness
            height -= 2 * self.widgets.swin.get_style().ythickness

        spacing = GObject.Value()
        spacing.init(GObject.TYPE_INT)
        spacing = self.widgets.swin.style_get_property("scrollbar-spacing", spacing)

        reqmin, req = self.widgets.swin.get_vscrollbar().get_preferred_size()
        vsb_w = spacing + req.width
        reqmin, req = self.widgets.swin.get_hscrollbar().get_preferred_size()
        hsb_h = spacing + req.height

        return width, height, vsb_w, hsb_h

    def on_drawingarea_draw(self, _widget, cr):
        if self._context is None:
            return

        # On Windows this function is already called once before the start function which sets
        # these necessary variables. It'll also call this function anyway once everything is
        # set up so we can stop execution here without problem if these variables aren't set yet.
        if self._paper_width is None or self._paper_height is None:
            return

        # get the extents of the page and the screen
        paper_w = int(self._paper_width * self._zoom)
        paper_h = int(self._paper_height * self._zoom)

        width, height, vsb_w, hsb_h = self.__get_view_size()
        if paper_h > height:
            width -= vsb_w
        if paper_w > width:
            height -= hsb_h

        # put the paper on the middle of the window
        xtranslate = MARGIN
        if paper_w < width:
            xtranslate += (width - paper_w) / 2

        ytranslate = MARGIN
        if paper_h < height:
            ytranslate += (height - paper_h) / 2

        cr.translate(xtranslate, ytranslate)

        # draw an empty white page
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(0, 0, paper_w, paper_h)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.stroke()

        dpi = PRINTER_DPI * self._zoom
        self._context.set_cairo_context(cr, dpi, dpi)
        # print("n_pages:", self._operation.get_property('n_pages'))
        if self._operation.get_property("n_pages") > 0:
            self._preview.render_page(0)  # self._current_page)

    def on_swin_size_allocate(self, _scrolledwindow, _allocation):
        if self._zoom_mode == ZOOM_FIT_WIDTH:
            self.__set_zoom(self.__zoom_fit_width())

        if self._zoom_mode == ZOOM_BEST_FIT:
            self.__set_zoom(self.__zoom_best_fit())

    def on_quit_clicked(self, _widget):
        self.get_toplevel().destroy()

    def on_save_clicked(self, _widget):
        self._setup_instance.save_pedigree()

    def on_print_clicked(self, _widget):
        self._setup_instance.print_pedigree()

    def on_zoom_fit_width_toggled(self, toggletoolbutton):
        if toggletoolbutton.get_active():
            self._zoom_best_fit_button.set_active(False)
            self._zoom_mode = ZOOM_FIT_WIDTH
            self.__set_zoom(self.__zoom_fit_width())
        else:
            self._zoom_mode = ZOOM_FREE

    def on_zoom_best_fit_toggled(self, toggletoolbutton):
        if toggletoolbutton.get_active():
            self._zoom_fit_width_button.set_active(False)
            self._zoom_mode = ZOOM_BEST_FIT
            self.__set_zoom(self.__zoom_best_fit())
        else:
            self._zoom_mode = ZOOM_FREE

    def on_zoom_original_clicked(self, _toolbutton):
        self._zoom_fit_width_button.set_active(False)
        self._zoom_best_fit_button.set_active(False)
        self._zoom_mode = ZOOM_FREE
        self.__set_zoom(1.0)

    def on_zoom_in_clicked(self, _toolbutton):
        self._zoom_fit_width_button.set_active(False)
        self._zoom_best_fit_button.set_active(False)
        self._zoom_mode = ZOOM_FREE
        self.__set_zoom(self.__zoom_in())

    def on_zoom_out_clicked(self, _toolbutton):
        self._zoom_fit_width_button.set_active(False)
        self._zoom_best_fit_button.set_active(False)
        self._zoom_mode = ZOOM_FREE
        self.__set_zoom(self.__zoom_out())

    def on_button_press_event(self, widget, event):
        if event.button == Gdk.BUTTON_PRIMARY and event.type == Gdk.EventType.BUTTON_PRESS:
            cursor_drag = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.FLEUR)
            widget.get_window().set_cursor(cursor_drag)
            self._last_x = event.x
            self._last_y = event.y
            self._is_dragging = True
            return True
        return False

    def on_button_release_event(self, widget, event):
        if event.button == Gdk.BUTTON_PRIMARY and event.type == Gdk.EventType.BUTTON_RELEASE:
            self.on_motion_notify_event(widget, event)
            widget.get_window().set_cursor(None)
            self._is_dragging = False
            return True
        return False

    def on_motion_notify_event(self, _widget, event):
        if self._is_dragging and (
            event.type == Gdk.EventType.MOTION_NOTIFY or event.type == Gdk.EventType.BUTTON_RELEASE
        ):
            hadjustment = self.widgets.swin.get_hadjustment()
            vadjustment = self.widgets.swin.get_vadjustment()
            self._update_scrollbar_positions(vadjustment, vadjustment.get_value() - (event.y - self._last_y))
            self._update_scrollbar_positions(hadjustment, hadjustment.get_value() - (event.x - self._last_x))
            return True
        return False

    def on_scroll_event(self, _widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.on_zoom_in_clicked(None)
                return True
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.on_zoom_out_clicked(None)
                return True
        return False

    def _update_scrollbar_positions(self, adjustment, value):  # noqa
        if value > (adjustment.get_upper() - adjustment.get_page_size()):
            adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        else:
            adjustment.set_value(value)
        return True

    def set_print_objects(self, operation, preview, context):
        self._operation = operation
        self._preview = preview
        self._context = context

    def end_preview(self):
        if self._preview is not None:
            GLib.idle_add(self._preview.end_preview, priority=GLib.PRIORITY_HIGH)

    def start(self):
        page_setup = self._context.get_page_setup()
        self._paper_width = page_setup.get_paper_width(Gtk.Unit.POINTS)
        self._paper_height = page_setup.get_paper_height(Gtk.Unit.POINTS)
        self._page_width = page_setup.get_page_width(Gtk.Unit.POINTS)
        self._page_height = page_setup.get_page_height(Gtk.Unit.POINTS)

        self.__set_zoom(self._zoom)
        self.widgets.drawingarea.queue_draw()
