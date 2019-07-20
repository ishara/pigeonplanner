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
A photo album to display all pigeon pictures
"""

import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.database.models import Image

logger = logging.getLogger(__name__)

MARGIN = 6

(ZOOM_BEST_FIT,
 ZOOM_FIT_WIDTH,
 ZOOM_FREE,) = range(3)


class PhotoAlbum(builder.GtkBuilder):
    ui = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="First"/>
      <toolitem action="Prev"/>
      <toolitem action="Next"/>
      <toolitem action="Last"/>
      <separator/>
      <toolitem action="Slide"/>
      <separator/>
      <toolitem action="Screen"/>
      <separator/>
      <toolitem action="Fit"/>
      <toolitem action="In"/>
      <toolitem action="Out"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""

    zoom_factors = {
        0.25: "25%",
        0.50: "50%",
        0.75: "75%",
        1.00: "100%",
        1.25: "125%",
        1.50: "150%",
        1.75: "175%",
        2.00: "200%",
    }

    def __init__(self, parent, image=None):
        builder.GtkBuilder.__init__(self, "PhotoAlbum.ui")

        self.widgets.photoalbum.set_transient_for(parent)

        self.build_toolbar()
        self.fill_iconview()

        self.pixbuf = None
        self.interp = GdkPixbuf.InterpType.BILINEAR
        self.max = (1600, 1200)
        self.picture_no = len(self.widgets.liststore)
        self.current_picture = 0
        self.zoom = 1.0
        self.zoom_mode = ZOOM_FREE
        if image is not None:
            path = tuple(index for index, row in
                         enumerate(self.widgets.liststore) if
                         row[1] == image)
        else:
            path = (0,)
        try:
            self.widgets.iconview.select_path(path)
        except:
            # Original image is missing
            pass
        self.set_zoom(1.0)
        self.widgets.zoom_fit_button.set_active(True)

        self.widgets.photoalbum.show()

    def build_toolbar(self):
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(self.ui)
        uimanager.insert_action_group(self.widgets.actiongroup, 0)
        accelgroup = uimanager.get_accel_group()
        self.widgets.photoalbum.add_accel_group(accelgroup)

        self.widgets.zoom_in_button = uimanager.get_widget("/Toolbar/In")
        self.widgets.zoom_out_button = uimanager.get_widget("/Toolbar/Out")
        self.widgets.zoom_fit_button = uimanager.get_widget("/Toolbar/Fit")
        self.widgets.first_button = uimanager.get_widget("/Toolbar/First")
        self.widgets.prev_button = uimanager.get_widget("/Toolbar/Prev")
        self.widgets.next_button = uimanager.get_widget("/Toolbar/Next")
        self.widgets.last_button = uimanager.get_widget("/Toolbar/Last")
        self.widgets.slide_button = uimanager.get_widget("/Toolbar/Slide")

        toolbar = uimanager.get_widget("/Toolbar")
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        self.widgets.vbox.pack_start(toolbar, False, False, 0)
        self.widgets.vbox.reorder_child(toolbar, 0)

    def fill_iconview(self):
        for image in Image.select():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(image.path, 96, 96)
                self.widgets.liststore.append(
                    [image.pigeon, image, image.pigeon.band, pixbuf])
            except GLib.GError:
                logger.error("Could not find original image for: %s" % image.pigeon.band)

        if len(self.widgets.liststore) > 0:
            self.widgets.labelImage.hide()
        else:
            self.disable_toolbuttons()
            self.widgets.labelImage.show()

    def get_view_size(self):
        width = self.widgets.swin.get_allocation().width - 2 * MARGIN
        height = self.widgets.swin.get_allocation().height - 2 * MARGIN

        if self.widgets.swin.get_shadow_type() != Gtk.ShadowType.NONE:
            width -= 2 * self.widgets.swin.style.xthickness
            height -= 2 * self.widgets.swin.style.ythickness

        spacing = self.widgets.swin.style_get_property("scrollbar-spacing")
        
        vreq = self.widgets.swin.get_vscrollbar().size_request()
        vsb_w = vreq.width + spacing
        
        hreq = self.widgets.swin.get_hscrollbar().size_request()
        hsb_h = hreq.height + spacing

        return width, height, vsb_w, hsb_h

    def set_picture(self, picture_no):
        if picture_no < 0 or picture_no >= self.picture_no:
            return

        if self.current_picture != picture_no:
            path = Gtk.TreePath(picture_no)
            self.widgets.iconview.select_path(path)

    def set_zoom(self, zoom):
        if not self.pixbuf:
            return

        self.zoom = zoom

        screen_width = int(self.pixbuf.get_width() * self.zoom + 2 * MARGIN)
        screen_height = int(self.pixbuf.get_height() * self.zoom + 2 * MARGIN)
        if screen_width < 1:
            screen_width = 1
        if screen_height < 1:
            screen_height = 1
        self.widgets.drawingarea.set_size_request(screen_width, screen_height)
        self.widgets.drawingarea.queue_draw()
        
        self.widgets.zoom_in_button.set_sensitive(self.zoom != max(self.zoom_factors.keys()))
        self.widgets.zoom_out_button.set_sensitive(self.zoom != min(self.zoom_factors.keys()))
        
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
        if not self.pixbuf:
            return

        width, height, vsb_w, hsb_h = self.get_view_size()
        zoom = min(width / float(self.pixbuf.get_width()), height / float(self.pixbuf.get_height()))

        return zoom

    def on_window_delete(self, widget, event):
        return False

    def on_close_clicked(self, widget):
        self.widgets.photoalbum.destroy()

    def on_first_clicked(self, widget):
        self.set_picture(0)
    
    def on_prev_clicked(self, widget):
        self.set_picture(self.current_picture - 1)
    
    def on_next_clicked(self, widget):
        self.set_picture(self.current_picture + 1)
    
    def on_last_clicked(self, widget):
        self.set_picture(self.picture_no - 1)

    def on_zoom_fit_toggled(self, widget):
        if widget.get_active():
            self.zoom_mode = ZOOM_BEST_FIT
            self.set_zoom(self.zoom_best_fit())
        else:
            self.zoom_mode = ZOOM_FREE

    def on_zoom_in_clicked(self, widget):
        self.widgets.zoom_fit_button.set_active(False)
        self.zoom_mode = ZOOM_FREE
        self.set_zoom(self.zoom_in())
    
    def on_zoom_out_clicked(self, widget):
        self.widgets.zoom_fit_button.set_active(False)
        self.zoom_mode = ZOOM_FREE
        self.set_zoom(self.zoom_out())

    def on_fullscreen_toggled(self, widget):
        if widget.get_active():
            self.widgets.photoalbum.fullscreen()
        else:
            self.widgets.photoalbum.unfullscreen()

    def on_slideshow_toggled(self, widget):
        if widget.get_active():
            self.widgets.slide_button.set_stock_id(Gtk.STOCK_MEDIA_STOP)
            self.slideshow_timer = GLib.timeout_add(3000, self.slideshow)
        else:
            self.widgets.slide_button.set_stock_id(Gtk.STOCK_MEDIA_PLAY)
            GLib.source_remove(self.slideshow_timer)

    def slideshow(self):
        if self.current_picture + 1 == self.picture_no:
            next = 0
        else:
            next = self.current_picture + 1

        self.set_picture(next)

        return True

    def on_swin_size_allocate(self, scrolledwindow, allocation):
        if self.zoom_mode == ZOOM_BEST_FIT:
            self.set_zoom(self.zoom_best_fit())

    def on_drawingarea_draw(self, widget, context):
        if not self.pixbuf:
            return

        picture_w = int(self.pixbuf.get_width() * self.zoom)
        picture_h = int(self.pixbuf.get_height() * self.zoom)

        width, height, vsb_w, hsb_h = self.get_view_size()
        if picture_h > height:
            width -= vsb_w
        if picture_w > width:
            height -= hsb_h

        xtranslate = MARGIN
        if picture_w < width:
            xtranslate += (width - picture_w) / 2

        ytranslate = MARGIN
        if picture_h < height:
            ytranslate += (height - picture_h) / 2

        context.translate(xtranslate, ytranslate)
        Gdk.cairo_set_source_pixbuf(context, self.pixbuf.scale_simple(picture_w, picture_h, self.interp), 0, 0)
        context.paint()

    def on_drawingarea_press(self, widget, event):
        if event.button == 2:
            self.widgets.zoom_fit_button.set_active(True)

    def on_drawingarea_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.widgets.zoom_fit_button.set_active(False)
            self.zoom_mode = ZOOM_FREE
            self.set_zoom(self.zoom_in())
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.widgets.zoom_fit_button.set_active(False)
            self.zoom_mode = ZOOM_FREE
            self.set_zoom(self.zoom_out())

    def on_iconview_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.set_picture(self.current_picture - 1)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.set_picture(self.current_picture + 1)

    def on_iconview_changed(self, widget):
        try:
            path = widget.get_selected_items()[0]
        except IndexError:
            self.set_pixbuf(None)
            self.disable_toolbuttons()
            return

        image = self.widgets.liststore[path][1]
        self.set_pixbuf(image.path)
        self.current_picture = path[0]

        utils.set_multiple_sensitive(
            {self.widgets.first_button: self.current_picture,
             self.widgets.prev_button: self.current_picture,
             self.widgets.next_button: self.current_picture < self.picture_no - 1,
             self.widgets.last_button: self.current_picture < self.picture_no - 1,
             self.widgets.zoom_in_button: True,
             self.widgets.zoom_out_button: True,
             self.widgets.zoom_fit_button: True,
             self.widgets.slide_button: True})

    def set_pixbuf(self, filename):
        if not filename:
            self.pixbuf = None
            self.widgets.drawingarea.queue_draw()
            return

        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        max_w, max_h = self.max
        if width < max_w and height < max_h:
            self.pixbuf = pixbuf
        else:
            width, height = self.scale_to_fit((width, height), self.max)
            self.pixbuf = pixbuf.scale_simple(width, height, self.interp)
        self.widgets.drawingarea.queue_draw()

    def scale_to_fit(self, image, frame):
        image_width, image_height = image
        frame_width, frame_height = frame
        image_aspect = float(image_width) / image_height
        frame_aspect = float(frame_width) / frame_height
        max_width = min(frame_width, image_width)
        max_height = min(frame_height, image_height)
        if frame_aspect > image_aspect:
            height = max_height
            width = int(height * image_aspect)
        else:
            width = max_width
            height = int(width / image_aspect)
        return width, height

    def disable_toolbuttons(self):
        utils.set_multiple_sensitive(
            [self.widgets.first_button,
             self.widgets.prev_button,
             self.widgets.next_button,
             self.widgets.last_button,
             self.widgets.zoom_in_button,
             self.widgets.zoom_out_button,
             self.widgets.zoom_fit_button,
             self.widgets.slide_button], False)
