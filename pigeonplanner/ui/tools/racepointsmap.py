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

import os

from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import OsmGpsMap

from pigeonplanner.core import const
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.ui import builder
from pigeonplanner.ui.tools import AddressBook
from pigeonplanner.ui.messagedialog import QuestionDialog
from pigeonplanner.database.models import Racepoint


MAP_TYPES = {
    OsmGpsMap.MapSource_t.OPENSTREETMAP: "OpenStreetMap",
    OsmGpsMap.MapSource_t.OPENSTREETMAP_RENDERER: "OpenStreetMap renderer",
    OsmGpsMap.MapSource_t.OPENAERIALMAP: "OpenAerialMap",
    OsmGpsMap.MapSource_t.MAPS_FOR_FREE: "Maps For Free",
    OsmGpsMap.MapSource_t.GOOGLE_STREET: "Google street",
    OsmGpsMap.MapSource_t.GOOGLE_SATELLITE: "Google satellite",
    OsmGpsMap.MapSource_t.GOOGLE_HYBRID: "Google hybrid",
    OsmGpsMap.MapSource_t.VIRTUAL_EARTH_STREET: "Virtualearth street",
    OsmGpsMap.MapSource_t.VIRTUAL_EARTH_SATELLITE: "Virtualearth satellite",
    OsmGpsMap.MapSource_t.VIRTUAL_EARTH_HYBRID: "Virtualearth hybrid"
}

DEFAULT_ZOOM = 6

MARKER_SIZE = 32


def get_marker_pixbuf(marker_name):
    img = os.path.join(const.IMAGEDIR, "%s.png" % marker_name)
    return GdkPixbuf.Pixbuf.new_from_file_at_size(img, MARKER_SIZE, MARKER_SIZE)


class RacepointsmapWindow(builder.GtkBuilder):
    (LS_OBJID,
     LS_NAME,
     LS_LATITUDE,
     LS_LONGITUDE,
     LS_MARKER,
     LS_POINT) = range(6)

    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "Racepointsmap.ui")

        self._racepoint_action = None
        self._marker_add = None

        self.widgets.selection = self.widgets.treeview.get_selection()
        self._selection_changed_id = self.widgets.selection.connect("changed", self.on_selection_changed)

        self._map = Map(self)
        self.widgets.box_map.pack_end(self._map, True, True, 0)

        self._fill_loft_info()
        self._fill_racepoints()
        self._fill_maptypes()

        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show_all()

        self._map.grab_focus()

    # noinspection PyMethodMayBeStatic
    def on_window_delete_event(self, widget, _event):
        widget.destroy()
        return False

    def on_button_loft_add_clicked(self, _widget):
        book = AddressBook(self.widgets.window)
        book.widgets.buttonsave.connect("clicked", self._fill_loft_info)

    def on_button_loft_cancel_clicked(self, _widget):
        self.widgets.loft_revealer.set_reveal_child(False)

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        for row in model:
            row[self.LS_MARKER].selected = False
        self._map.maptrack.remove_point(1)
        self.widgets.distance_entry.set_text("0.0")
        self.widgets.button_edit.set_sensitive(treeiter is not None)
        self.widgets.button_remove.set_sensitive(treeiter is not None)
        if treeiter is not None:
            marker = model[treeiter][self.LS_MARKER]
            marker.selected = True
            mappoint = model[treeiter][self.LS_POINT]
            if mappoint is not None and self._map.maptrack.n_points() != 0:
                self._map.maptrack.add_point(mappoint)
            self._set_distance_entry()

    def on_distance_combo_changed(self, _widget):
        self._set_distance_entry()

    def on_track_switch_active(self, widget, _active):
        if widget.get_active():
            self._map.add_maptrack()
        else:
            self._map.remove_maptrack()

    def on_maptype_combo_changed(self, widget):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        self._map.props.map_source = model[tree_iter][0]

    def on_button_add_clicked(self, widget):
        self._racepoint_action = enums.Action.add
        self._show_addedit_popover(widget)

    def on_button_edit_clicked(self, widget):
        self._racepoint_action = enums.Action.edit
        racepoint = self._get_selected_racepoint()
        self._show_addedit_popover(widget, racepoint.racepoint, racepoint.xco, racepoint.yco)

    def on_button_remove_clicked(self, _widget):
        selection = self.widgets.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if QuestionDialog((_("Removing the selected racepoint."), _("Are you sure?"), ""),
                          self.widgets.window).run():
            Racepoint.delete_by_id(model[treeiter][self.LS_OBJID])
            model[treeiter][self.LS_MARKER].remove_from_map()
            model.remove(treeiter)

    def on_edit_apply_clicked(self, _widget):
        name = self.widgets.edit_racepoint_entry.get_text()
        if name == "":
            self.widgets.addedit_error_label.set_text("The racepoint name is required.")
            self.widgets.addedit_error_revealer.set_reveal_child(True)
            return

        try:
            latitude = self.widgets.edit_latitude_entry.get_text()
            longitude = self.widgets.edit_longitude_entry.get_text()
        except errors.InvalidInputError:
            return

        try:
            if self._racepoint_action == enums.Action.add:
                Racepoint.create(racepoint=name, xco=latitude, yco=longitude)
            elif self._racepoint_action == enums.Action.edit:
                racepoint = self._get_selected_racepoint()
                racepoint.racepoint = name
                racepoint.xco = latitude
                racepoint.yco = longitude
                racepoint.save()
        except errors.IntegrityError:
            self.widgets.addedit_error_label.set_text("The racepoint name already exists.")
            self.widgets.addedit_error_revealer.set_reveal_child(True)
            return

        self._fill_racepoints()
        self.widgets.popover.popdown()

    def on_edit_cancel_clicked(self, _widget):
        self.widgets.popover.popdown()

    def on_popover_closed(self, _widget):
        if self._marker_add is not None:
            self._map.image_remove(self._marker_add)
            self._marker_add = None

    def on_button_zoom_in_clicked(self, _widget):
        self._map.set_zoom(self._map.props.zoom + 1)

    def on_button_zoom_out_clicked(self, _widget):
        self._map.set_zoom(self._map.props.zoom - 1)

    def add_racepoint_through_map(self, mappoint, rect):
        latitude, longitude = mappoint.get_degrees()
        img = get_marker_pixbuf("marker_add")
        self._marker_add = self._map.image_add_with_alignment(latitude, longitude, img, 0.5, 1)
        self._racepoint_action = enums.Action.add
        self._show_addedit_popover(self._map, latitude=str(latitude), longitude=str(longitude), rect=rect)

    def _show_addedit_popover(self, widget, name="", latitude="", longitude="", rect=None):
        self.widgets.addedit_error_revealer.set_reveal_child(False)
        self.widgets.edit_racepoint_entry.set_text(name)
        self.widgets.edit_latitude_entry.set_text(latitude)
        self.widgets.edit_longitude_entry.set_text(longitude)
        self.widgets.popover.set_relative_to(widget)
        # This is a stupid solution for something that should be easier. When clicking on the map we pass
        # the GdkRectangle where the mouse pointer is to show the popover at the correct place. The popover
        # set_pointing_to() method doesn't allow None as argument to possibly reset this again to just the
        # widget it's attached to. So we modify the widget's GdkRectangle to point to the correct location.
        if rect is None:
            rect = widget.get_allocation()
            rect.x = 0
        self.widgets.popover.set_pointing_to(rect)
        self.widgets.popover.show_all()
        self.widgets.popover.popup()
        self.widgets.edit_racepoint_entry.grab_focus()

    def _set_distance_entry(self):
        unit = self.widgets.distance_combo.get_unit()
        distance = self._map.maptrack.get_length() / unit
        self.widgets.distance_entry.set_text(str(round(distance, 2)))

    def _get_selected_racepoint(self):
        model, treeiter = self.widgets.selection.get_selected()
        racepoint_id = model[treeiter][self.LS_OBJID]
        return Racepoint.get_by_id(racepoint_id)

    def _fill_loft_info(self, _widget=None):
        person = common.get_own_address()
        if person is None:
            self.widgets.loft_name.set_text("")
            self.widgets.loft_latitude.set_text("")
            self.widgets.loft_longitude.set_text("")
            self.widgets.loft_revealer.set_reveal_child(True)
            return
        self.widgets.loft_name.set_text(person.name)
        self.widgets.loft_latitude.set_text(person.latitude)
        self.widgets.loft_longitude.set_text(person.longitude)
        if not person.has_valid_coordinates():
            self.widgets.loft_revealer.set_reveal_child(True)
            return
        self.widgets.loft_revealer.set_reveal_child(False)

    def _fill_racepoints(self):
        self._map.clear_markers()
        self.widgets.ls_racepoints.clear()
        for obj in Racepoint.select().order_by(Racepoint.racepoint.asc()):
            marker = Marker(self._map, obj)
            marker.add_to_map(selected=False)
            if obj.has_valid_coordinates():
                point = OsmGpsMap.MapPoint.new_degrees(obj.latitude_float, obj.longitude_float)
            else:
                point = None
            self.widgets.ls_racepoints.append([obj.id, obj.racepoint, obj.xco, obj.yco, marker, point])

    def _fill_maptypes(self):
        for map_enum, map_name in MAP_TYPES.items():
            self.widgets.ls_maptypes.append([map_enum, map_name])
        self.widgets.maptype_combo.set_active(0)


class Map(OsmGpsMap.Map):
    def __init__(self, window):
        OsmGpsMap.Map.__init__(self)
        self.connect("button-press-event", self.on_button_press_event)
        self.set_zoom(DEFAULT_ZOOM)
        self.maptrack = OsmGpsMap.MapTrack()
        self.track_add(self.maptrack)
        self._window = window

        osd_layer = OsmGpsMap.MapOsd(
            show_dpad=False,  # Top left control buttons to move map
            show_zoom=False,  # Top left control buttons to zoom map
            show_scale=True,  # Bottom left scale measure
            show_coordinates=False,  # Bottom right map center coordinates
        )
        self.layer_add(osd_layer)

        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.ZOOMIN, Gdk.keyval_from_name("plus"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.ZOOMIN, Gdk.keyval_from_name("KP_Add"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.ZOOMOUT, Gdk.keyval_from_name("minus"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.ZOOMOUT, Gdk.keyval_from_name("KP_Subtract"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.UP, Gdk.keyval_from_name("Up"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.DOWN, Gdk.keyval_from_name("Down"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.LEFT, Gdk.keyval_from_name("Left"))
        self.set_keyboard_shortcut(OsmGpsMap.MapKey_t.RIGHT, Gdk.keyval_from_name("Right"))

    def on_button_press_event(self, _widget, event):
        self.grab_focus()

        if event.button == Gdk.BUTTON_SECONDARY:
            point = self.get_event_location(event)
            x, y = self.convert_geographic_to_screen(point)
            rect = Gdk.Rectangle()
            rect.x = x
            rect.y = y
            self._window.add_racepoint_through_map(point, rect)

    def clear_markers(self):
        self.image_remove_all()
        person = common.get_own_address()
        self.add_home_marker(person)

    def add_home_marker(self, person):
        if person is None and not person.has_valid_coordinates():
            return

        img = get_marker_pixbuf("marker_home")
        self.image_add_with_alignment_z(person.latitude_float, person.longitude_float, img, 0.5, 1, 1)

        self.set_center(person.latitude_float, person.longitude_float)

        loft = OsmGpsMap.MapPoint.new_degrees(person.latitude_float, person.longitude_float)
        self.maptrack.add_point(loft)

    def add_maptrack(self):
        self.track_add(self.maptrack)

    def remove_maptrack(self):
        self.track_remove(self.maptrack)


class Marker:
    def __init__(self, mapobj, racepoint):
        self._mapimg = None
        self._selected = False
        self._racepoint = racepoint
        self._mapobj = mapobj
        self.latitude = racepoint.latitude_float
        self.longitude = racepoint.longitude_float
        self._img = get_marker_pixbuf("marker")
        self._img_selected = get_marker_pixbuf("marker_selected")

    def add_to_map(self, selected):
        self.remove_from_map()
        if self._racepoint.has_valid_coordinates():
            img = self._img_selected if selected else self._img
            self._mapimg = self._mapobj.image_add_with_alignment(self.latitude, self.longitude, img, 0.5, 1)

    def remove_from_map(self):
        if self._mapimg is not None:
            self._mapobj.image_remove(self._mapimg)

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self.remove_from_map()
        self.add_to_map(selected=value)
