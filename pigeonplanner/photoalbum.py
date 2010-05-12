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
import gtk.glade
import logging
logger = logging.getLogger(__name__)

import const
import widgets


MARGIN = 6

(ZOOM_BEST_FIT,
 ZOOM_FIT_WIDTH,
 ZOOM_FREE,) = range(3)


class PhotoAlbum:

    zoom_factors = {
        0.25: '25%',
        0.50: '50%',
        0.75: '75%',
        1.00: '100%',
        1.25: '125%',
        1.50: '150%',
        1.75: '175%',
        2.00: '200%',
    }

    def __init__(self, parent, parser, database):
        self.wTree = gtk.glade.XML(const.GLADEPHOTOALBUM)
        self.wTree.signal_autoconnect(self)

        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            setattr(self, name, w)

        self.photoalbum.set_transient_for(parent)

        self.parser = parser
        self.database = database

        self.build_toolbar()
        self.fill_iconview()

        self.pixbuf = None
        self.interp = gtk.gdk.INTERP_BILINEAR
        self.max = (1600, 1200)
        self.picture_no = len(self.iconview.get_model())
        self.current_picture = 0
        self.zoom_mode = ZOOM_FREE
        self.iconview.select_path((0,))
        self.set_zoom(1.0)
        self.zoom_fit_button.set_active(True)

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(widgets.photoalbumui)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.photoalbum.add_accel_group(accelgroup)

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
        self.vbox.reorder_child(toolbar, 0)

    def create_action_group(self):
        action_group = gtk.ActionGroup("PhotoAlbumActions")
        action_group.add_actions((
            ("First", gtk.STOCK_GOTO_FIRST, None, None,
                    _("Shows the first picture"), self.on_first_clicked),
            ("Prev", gtk.STOCK_GO_BACK, None, None,
                    _("Shows previous picture"), self.on_prev_clicked),
            ("Next", gtk.STOCK_GO_FORWARD, None, None,
                    _("Shows the next picture"), self.on_next_clicked),
            ("Last", gtk.STOCK_GOTO_LAST, None, None,
                    _("Shows the last picture"), self.on_last_clicked),
            ("In", gtk.STOCK_ZOOM_IN, None, None,
                    _("Zooms the picture in"), self.on_zoom_in_clicked),
            ("Out", gtk.STOCK_ZOOM_OUT, None, None,
                    _("Zooms the picture out"), self.on_zoom_out_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_clicked),
           ))
        action_group.add_toggle_actions((
            ("Fit", gtk.STOCK_ZOOM_FIT, None, None,
                    _("Zooms to fit the whole picture"), self.on_zoom_fit_toggled),
           ))

        return action_group

    def fill_iconview(self):
        store = gtk.ListStore(str, str, str, gtk.gdk.Pixbuf)
        store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.iconview.set_model(store)
        self.iconview.set_text_column(2)
        self.iconview.set_pixbuf_column(3)

        for pigeon in self.database.get_all_images():
            if not pigeon[3]: continue

            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(pigeon[3], 96, 96)
                store.append(["%s%s" %(pigeon[2], pigeon[1]), pigeon[0], "%s/%s" %(pigeon[1], pigeon[2][2:]), pixbuf])
            except gobject.GError:
                logger.error("Could not find original image for: %s/%s" %(pigeon[1], pigeon[2]))

        if len(store) > 0:
            self.labelImage.hide()
        else:
            self.disable_toolbuttons()
            self.labelImage.show()

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

    def set_picture(self, picture_no):
        if picture_no < 0 or picture_no >= self.picture_no:
            return

        if self.current_picture != picture_no:
            self.iconview.select_path((picture_no,))

    def set_zoom(self, zoom):
        if not self.pixbuf:
            return

        self.zoom = zoom

        screen_width = int(self.pixbuf.get_width() * self.zoom + 2 * MARGIN)
        screen_height = int(self.pixbuf.get_height() * self.zoom + 2 * MARGIN)
        self.drawingarea.set_size_request(screen_width, screen_height)
        self.drawingarea.queue_draw()
        
        self.zoom_in_button.set_sensitive(self.zoom != max(self.zoom_factors.keys()))
        self.zoom_out_button.set_sensitive(self.zoom != min(self.zoom_factors.keys()))
        
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
        self.photoalbum.destroy()

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
        self.context = widget.window.cairo_create()
        self.context.rectangle(event.area)
        self.context.clip()

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
        if  picture_w < width:
            xtranslate += (width - picture_w) / 2

        ytranslate = MARGIN
        if  picture_h < height:
            ytranslate += (height - picture_h) / 2

        self.context.translate(xtranslate, ytranslate)
        self.context.set_source_pixbuf(self.pixbuf.scale_simple(picture_w, picture_h, self.interp), 0, 0)
        self.context.paint()

    def on_iconview_changed(self, widget):
        model = widget.get_model()

        try:
            path = widget.get_selected_items()[0]
        except IndexError:
            self.set_pixbuf(None)
            self.disable_toolbuttons()
            return

        pindex = model[path][1]
        image = self.parser.pigeons[pindex].image

        self.set_pixbuf(image)
        self.current_picture = path[0]

        widgets.set_multiple_sensitive(
            {self.first_button: self.current_picture,
             self.prev_button: self.current_picture,
             self.next_button: self.current_picture < self.picture_no - 1,
             self.last_button: self.current_picture < self.picture_no - 1,
             self.zoom_in_button: True,
             self.zoom_out_button: True,
             self.zoom_fit_button: True})

    def set_pixbuf(self, filename):
        if not filename:
            self.pixbuf = None
            self.drawingarea.queue_draw()
            return

        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        if not self.max or (width < self.max[0] and height < self.max[1]):
            self.pixbuf = pixbuf
        else:
            width, height = self.scale_to_fit((width, height), self.max)
            self.pixbuf = pixbuf.scale_simple(width, height, self.interp)

        self.drawingarea.queue_draw()

    def disable_toolbuttons(self):
        widgets.set_multiple_sensitive(
            {self.first_button: False,
             self.prev_button: False,
             self.next_button: False,
             self.last_button: False,
             self.zoom_in_button: False,
             self.zoom_out_button: False,
             self.zoom_fit_button: False})

