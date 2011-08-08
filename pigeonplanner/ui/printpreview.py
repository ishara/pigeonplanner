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


import math

import gtk

from ui.widgets import menus


PRINTER_DPI = 72.0

MARGIN = 6

(ZOOM_BEST_FIT,
 ZOOM_FIT_WIDTH,
 ZOOM_FREE,) = range(3)


class PrintPreview(gtk.Window):
    zoom_factors = {
        0.50: '50%',
        0.75: '75%',
        1.00: '100%',
        1.25: '125%',
        1.50: '150%',
        1.75: '175%',
        2.00: '200%',
        3.00: '300%',
        4.00: '400%',
    }

    def __init__(self, operation, preview, context, parent):
        gtk.Window.__init__(self)
        self.connect('delete-event', self.on_window_delete)
        self.set_transient_for(parent)
        self.set_title(_("Print Preview"))
        self.resize(800, 600)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_modal(True)

        self.operation = operation
        self.preview = preview
        self.context = context

        self.drawingarea = gtk.DrawingArea()
        self.drawingarea.connect('expose-event', self.on_drawingarea_expose)
        self.swin = gtk.ScrolledWindow()
        self.swin.connect('size-allocate', self.on_swin_size_allocate)
        self.swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.swin.add_with_viewport(self.drawingarea)
        self.vbox = gtk.VBox()
        self.vbox.pack_end(self.swin)
        self.add(self.vbox)

        self.build_toolbar()
        self.current_page = None

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(menus.ui_printpreview)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        self.zoom_in_button = uimanager.get_widget('/Toolbar/In')
        self.zoom_out_button = uimanager.get_widget('/Toolbar/Out')
        self.zoom_fit_button = uimanager.get_widget('/Toolbar/Fit')
        self.first_button = uimanager.get_widget('/Toolbar/First')
        self.prev_button = uimanager.get_widget('/Toolbar/Prev')
        self.next_button = uimanager.get_widget('/Toolbar/Next')
        self.last_button = uimanager.get_widget('/Toolbar/Last')

        toolbar = uimanager.get_widget('/Toolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.vbox.pack_start(toolbar, False, False)

    def create_action_group(self):
        action_group = gtk.ActionGroup("PreviewWindowActions")
        action_group.add_actions((
            ("First", gtk.STOCK_GOTO_FIRST, None, None,
                    _("Shows the first page"), self.on_first_clicked),
            ("Prev", gtk.STOCK_GO_BACK, None, None,
                    _("Shows previous page"), self.on_prev_clicked),
            ("Next", gtk.STOCK_GO_FORWARD, None, None,
                    _("Shows the next page"), self.on_next_clicked),
            ("Last", gtk.STOCK_GOTO_LAST, None, None,
                    _("Shows the last page"), self.on_last_clicked),
            ("In", gtk.STOCK_ZOOM_IN, None, None,
                    _("Zooms the page in"), self.on_zoom_in_clicked),
            ("Out", gtk.STOCK_ZOOM_OUT, None, None,
                    _("Zooms the page out"), self.on_zoom_out_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_clicked),
           ))
        action_group.add_toggle_actions((
            ("Fit", gtk.STOCK_ZOOM_FIT, None, None,
                    _("Zooms to fit the whole page"),
                    self.on_zoom_fit_toggled),
           ))

        return action_group

    def get_view_size(self):
        width = self.swin.allocation.width - 2 * MARGIN
        height = self.swin.allocation.height - 2 * MARGIN

        if self.swin.get_shadow_type() != gtk.SHADOW_NONE:
            width -= 2 * self.swin.style.xthickness
            height -= 2 * self.swin.style.ythickness

        spacing = self.swin.style_get_property('scrollbar-spacing')
        
        vsb_w, vsb_h = self.swin.get_vscrollbar().size_request()
        vsb_w += spacing
        
        hsb_w, hsb_h = self.swin.get_hscrollbar().size_request()
        hsb_h += spacing
        
        return width, height, vsb_w, hsb_h

    def set_page(self, page_no):
        if page_no < 0 or page_no >= self.page_no:
            return

        if self.current_page != page_no:
            self.drawingarea.queue_draw()

        self.current_page = page_no

        self.first_button.set_sensitive(self.current_page)
        self.prev_button.set_sensitive(self.current_page)
        self.next_button.set_sensitive(self.current_page < self.page_no - 1)
        self.last_button.set_sensitive(self.current_page < self.page_no - 1)

    def set_zoom(self, zoom):
        self.zoom = zoom

        screen_width = int(self.paper_width * self.zoom + 2 * MARGIN)
        screen_height = int(self.paper_height * self.zoom + 2 * MARGIN)
        self.drawingarea.set_size_request(screen_width, screen_height)
        self.drawingarea.queue_draw()
        
        self.zoom_in_button.set_sensitive(self.zoom !=
                                          max(self.zoom_factors.keys()))
        self.zoom_out_button.set_sensitive(self.zoom !=
                                           min(self.zoom_factors.keys()))
        
    def zoom_in(self):
        zoom = [z for z in self.zoom_factors.keys() if z > self.zoom]

        if zoom:
            return min(zoom)
        else:
            return self.zoom

    def zoom_out(self):
        zoom = [z for z in self.zoom_factors.keys() if z < self.zoom]

        if zoom:
            return max(zoom)
        else:
            return self.zoom

    def zoom_best_fit(self):
        width, height, vsb_w, hsb_h = self.get_view_size()
        zoom = min(width / self.paper_width, height / self.paper_height)

        return zoom

    def end_preview(self):
        self.operation.end_preview()

    def on_window_delete(self, widget, event):
        self.end_preview()
        return False

    def on_close_clicked(self, widget):
        self.end_preview()
        self.destroy()

    def on_first_clicked(self, widget):
        self.set_page(0)
    
    def on_prev_clicked(self, widget):
        self.set_page(self.current_page - 1)
    
    def on_next_clicked(self, widget):
        self.set_page(self.current_page + 1)
    
    def on_last_clicked(self, widget):
        self.set_page(self.page_no - 1)

    def on_zoom_fit_toggled(self, widget):
        if widget.get_active():
            self.zoom_mode = ZOOM_BEST_FIT
            self.set_zoom(self.zoom_best_fit())
        else:
            self.zoom_mode = ZOOM_FREE

    def on_zoom_in_clicked(self, widget):
        self.zoom_fit_button.set_active(False)
        self.zoom_mode = ZOOM_FREE
        self.set_zoom(self.zoom_in())
    
    def on_zoom_out_clicked(self, widget):
        self.zoom_fit_button.set_active(False)
        self.zoom_mode = ZOOM_FREE
        self.set_zoom(self.zoom_out())

    def on_swin_size_allocate(self, scrolledwindow, allocation):
        if self.zoom_mode == ZOOM_BEST_FIT:
            self.set_zoom(self.zoom_best_fit())

    def on_drawingarea_expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area)
        cr.clip()

        paper_w = int(self.paper_width * self.zoom)
        paper_h = int(self.paper_height * self.zoom)

        width, height, vsb_w, hsb_h = self.get_view_size()
        if paper_h > height:
            width -= vsb_w
        if paper_w > width:
            height -= hsb_h

        xtranslate = MARGIN
        if  paper_w < width:
            xtranslate += (width - paper_w) / 2

        ytranslate = MARGIN
        if  paper_h < height:
            ytranslate += (height - paper_h) / 2

        cr.translate(xtranslate, ytranslate)

        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(0, 0, paper_w, paper_h)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.stroke()

        if self.orientation == gtk.PAGE_ORIENTATION_LANDSCAPE:
            cr.rotate(math.radians(90))
            cr.translate(0, -paper_w)

        dpi = PRINTER_DPI * self.zoom
        self.context.set_cairo_context(cr, dpi, dpi)
        self.preview.render_page(self.current_page)

    def start(self):
        page_setup = self.context.get_page_setup()
        self.paper_width = page_setup.get_paper_width(gtk.UNIT_POINTS)
        self.paper_height = page_setup.get_paper_height(gtk.UNIT_POINTS)
        self.page_width = page_setup.get_page_width(gtk.UNIT_POINTS)
        self.page_height = page_setup.get_page_height(gtk.UNIT_POINTS)
        self.orientation = page_setup.get_orientation()

        self.page_no = self.operation.get_property('n_pages')

        self.zoom_mode = ZOOM_FREE
        self.set_zoom(1.0)
        self.set_page(0)

        self.show_all()

