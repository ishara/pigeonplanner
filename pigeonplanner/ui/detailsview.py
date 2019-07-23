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


import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf

from pigeonplanner import messages
from pigeonplanner import thumbnail
from pigeonplanner.ui import tools
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.widgets import date
from pigeonplanner.ui.widgets import sexentry
from pigeonplanner.ui.widgets import bandentry
from pigeonplanner.ui.messagedialog import ErrorDialog, WarningDialog
from pigeonplanner.core import enums
from pigeonplanner.core import const
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.database.models import Status, Colour, Strain, Loft

logger = logging.getLogger(__name__)

RESPONSE_EDIT = 10
RESPONSE_SAVE = 12


class DetailsDialog(Gtk.Dialog):
    def __init__(self, pigeon=None, parent=None, mode=None):
        Gtk.Dialog.__init__(self, None, parent, Gtk.DialogFlags.MODAL)

        if parent is None:
            self.set_position(Gtk.WindowPosition.MOUSE)

        if mode in (enums.Action.edit, enums.Action.add):
            self.details = DetailsViewEdit(parent=self, pigeon=pigeon)
            self.details.start_edit(mode)
            self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_SAVE, RESPONSE_SAVE)
            self.set_default_response(RESPONSE_SAVE)
            self.set_resizable(True)
            self.resize(620, 1)
        else:
            self.details = DetailsView(parent=self)
            self.details.set_details(pigeon)
            self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
            self.set_default_response(Gtk.ResponseType.CLOSE)
            self.set_resizable(False)
        self.vbox.pack_start(self.details.get_root_widget(), False, False, 0)

        if pigeon is None:
            title = _("Details of pigeon")
            self.details.clear_details()
        else:
            title = _("Details of %s") % pigeon.band
        self.set_title(title)

        self.run()

    def run(self):
        self.connect("response", self.on_dialog_response)
        self.show_all()

    def on_dialog_response(self, dialog, response_id):
        keep_alive = False
        if response_id in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
            pass
        elif response_id == RESPONSE_SAVE:
            keep_alive = self.details.operation_saved()
        elif response_id == Gtk.ResponseType.CANCEL:
            self.details.operation_cancelled()

        if not keep_alive:
            dialog.destroy()


class PigeonImageWidget(Gtk.EventBox):
    def __init__(self, editable, view, parent=None):
        Gtk.EventBox.__init__(self)
        if editable:
            self.connect("button-press-event", self.on_editable_button_press_event)
            self.connect("realize", self.on_realize)
        else:
            self.connect("button-press-event", self.on_button_press_event)

        self._logo_pb = GdkPixbuf.Pixbuf.new_from_file_at_size(const.LOGO_IMG, 75, 75)
        self._view = view
        self._parent = parent
        self._imagewidget = Gtk.Image.new_from_pixbuf(self._logo_pb)
        self._imagewidget.set_size_request(200, 200)
        self.add(self._imagewidget)
        self._imagepath = ""
        self.set_default_image()

    def on_button_press_event(self, widget, event):
        if self._view.pigeon is None:
            return
        parent = None if isinstance(self._parent, Gtk.Dialog) else self._parent
        tools.PhotoAlbum(parent, self._view.pigeon.main_image)

    def on_editable_button_press_event(self, widget, event):
        if event.button == Gdk.BUTTON_SECONDARY:
            entries = [
                (Gtk.STOCK_ADD, self.on_open_imagechooser, None, None),
                (Gtk.STOCK_REMOVE, self.set_default_image, None, None)]
            utils.popup_menu(event, entries)
        else:
            self.on_open_imagechooser()

    def on_open_imagechooser(self, widget=None):
        chooser = filechooser.ImageChooser(self._parent)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 200, 200)
            except GLib.GError as exc:
                logger.error("Can't set image '%s':%s", filename, exc)
                ErrorDialog(messages.MSG_INVALID_IMAGE, self._parent)
            else:
                self._imagewidget.set_from_pixbuf(pb)
                self._imagepath = filename
        elif response == chooser.RESPONSE_CLEAR:
            self.set_default_image()
        chooser.destroy()

    def on_realize(self, widget):
        self.set_cursor("pointer")

    def set_default_image(self, widget=None):
        self._imagewidget.set_from_pixbuf(self._logo_pb)
        self._imagepath = ""

    def set_image(self, image=None):
        if image is not None:
            pixbuf = thumbnail.get_image(image.path)
            self._imagewidget.set_from_pixbuf(pixbuf)
            self._imagepath = image.path
            self.set_cursor("pointer")
        else:
            self.set_default_image()
            self.set_cursor(None)

    def get_image_path(self):
        return self._imagepath

    def set_cursor(self, cursor):
        if cursor is not None:
            cursor = Gdk.Cursor.new_from_name(Gdk.Display.get_default(), cursor)
        gdkwindow = self.get_window()
        gdkwindow.set_cursor(cursor)


class StatusButton(builder.GtkBuilder):
    def __init__(self, parent=None):
        builder.GtkBuilder.__init__(self, "DetailsView.ui",
                                    ["statusbutton", "statusdialog"])
        self.parent = parent
        self.widget = self.widgets.statusbutton
        self.widgets.statusdialog.set_transient_for(parent)
        self.set_default()

    def on_statusdialog_close(self, widget, event=None):
        page = self.widgets.notebookstatus.get_current_page()
        grid = self.widgets.notebookstatus.get_nth_page(page)
        for child in grid.get_children():
            if isinstance(child, date.DateEntry):
                try:
                    # Just check the date, the value is used elsewhere
                    child.get_text()
                except errors.InvalidInputError as msg:
                    ErrorDialog(msg.value, self.parent)
                    return True
        self.widgets.statusdialog.hide()
        return True

    def on_entrypartnerwidow_search_clicked(self, widget):
        return None, enums.Sex.cock, None

    def on_combostatus_changed(self, widget):
        status = widget.get_active()
        self.widgets.notebookstatus.set_current_page(status)
        self._set_button_info(status)

    def on_statusbutton_clicked(self, widget):
        if self.pigeon:
            status_id = self.pigeon.status.status_id
            self.widgets.labelstatus.set_text(enums.Status.get_string(status_id))
            self.widgets.notebookstatus.set_current_page(status_id)
        self.widgets.statusdialog.show()
        self.widgets.buttonstatusok.grab_focus()

    def _set_button_info(self, status):
        image = common.STATUS_IMGS[status]
        label = enums.Status.get_string(status)
        self.widgets.statuslabel.set_text(label)
        self.widgets.statusimage.set_from_file(image)

    def get_current_status(self):
        return self.widgets.combostatus.get_active()

    def get_current_data(self):
        statusdata = Status.get_fields_with_defaults()
        status = self.widgets.combostatus.get_active()
        if status == enums.Status.active:
            return statusdata
        if status == enums.Status.dead:
            bffr = self.widgets.textinfodead.get_buffer()
            statusdata.update({"date": self.widgets.entrydatedead.get_text(),
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata
        if status == enums.Status.sold:
            bffr = self.widgets.textinfosold.get_buffer()
            statusdata.update({"person": self.widgets.entrybuyersold.get_text(),
                               "date": self.widgets.entrydatesold.get_text(),
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata
        if status == enums.Status.lost:
            bffr = self.widgets.textinfolost.get_buffer()
            statusdata.update({"racepoint": self.widgets.entrypointlost.get_text(),
                               "date": self.widgets.entrydatelost.get_text(),
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata
        if status == enums.Status.breeder:
            bffr = self.widgets.textinfobreeder.get_buffer()
            statusdata.update({"start": self.widgets.entrydatebreedfrom.get_text(),
                               "end": self.widgets.entrydatebreedto.get_text(),
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata
        if status == enums.Status.loaned:
            bffr = self.widgets.textinfoloan.get_buffer()
            statusdata.update({"start": self.widgets.entrydateloan.get_text(),
                               "end": self.widgets.entrydateloanback.get_text(),
                               "person": self.widgets.entrypersonloan.get_text(),
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata
        if status == enums.Status.widow:
            bffr = self.widgets.textinfowidow.get_buffer()
            partner_band = self.widgets.entrypartnerwidow.get_band()
            partner = corepigeon.get_or_create_pigeon(partner_band, enums.Sex.cock, False)
            statusdata.update({"partner": partner,
                               "info": bffr.get_text(*bffr.get_bounds())})
            return statusdata

    def set_default(self):
        self.pigeon = None
        self.widgets.combostatus.set_active(enums.Status.active)
        self.widgets.combostatus.emit("changed")

    def set_sensitive(self, value):
        self.widgets.statusbutton.set_sensitive(value)

    def set_pigeon(self, pigeon):
        self.pigeon = pigeon
        status_id = pigeon.status.status_id
        self._set_button_info(status_id)
        self.widgets.combostatus.set_active(status_id)
        if status_id == enums.Status.dead:
            self.widgets.entrydatedead.set_text(pigeon.status.date)
            self.widgets.textinfodead.get_buffer().set_text(pigeon.status.info)
        elif status_id == enums.Status.sold:
            self.widgets.entrydatesold.set_text(pigeon.status.date)
            self.widgets.entrybuyersold.set_text(pigeon.status.person)
            self.widgets.textinfosold.get_buffer().set_text(pigeon.status.info)
        elif status_id == enums.Status.lost:
            self.widgets.entrydatelost.set_text(pigeon.status.date)
            self.widgets.entrypointlost.set_text(pigeon.status.racepoint)
            self.widgets.textinfolost.get_buffer().set_text(pigeon.status.info)
        elif status_id == enums.Status.breeder:
            self.widgets.entrydatebreedfrom.set_text(pigeon.status.start)
            self.widgets.entrydatebreedto.set_text(pigeon.status.end)
            self.widgets.textinfobreeder.get_buffer().set_text(pigeon.status.info)
        elif status_id == enums.Status.loaned:
            self.widgets.entrydateloan.set_text(pigeon.status.start)
            self.widgets.entrydateloanback.set_text(pigeon.status.end)
            self.widgets.entrypersonloan.set_text(pigeon.status.person)
            self.widgets.textinfoloan.get_buffer().set_text(pigeon.status.info)
        elif status_id == enums.Status.widow:
            self.widgets.entrypartnerwidow.set_pigeon(pigeon.status.partner)
            self.widgets.textinfowidow.get_buffer().set_text(pigeon.status.info)

    def set_editable(self, value):
        def set_editable(widget, value):
            if isinstance(widget, Gtk.ScrolledWindow):
                set_editable(widget.get_child(), value)
            if isinstance(widget, bandentry.BandEntry):
                widget.set_has_search(value)
            try:
                widget.set_editable(value)
            except:
                pass
        for grid in self.widgets.notebookstatus.get_children():
            grid.foreach(set_editable, value)
        self.widgets.hboxstatusedit.set_visible(value)
        self.widgets.hboxstatusnormal.set_visible(not value)


class DetailsView(builder.GtkBuilder, component.Component):
    def __init__(self, parent=None, register=False):
        builder.GtkBuilder.__init__(self, "DetailsView.ui", ["root_view"])
        if register:
            component.Component.__init__(self, "DetailsView")

        self.parent = parent or component.get("MainWindow")
        self.pedigree_mode = False
        self.pigeon = None
        self.child = None

        self.widgets.pigeonimage = PigeonImageWidget(False, self, parent)
        self.widgets.viewportImage.add(self.widgets.pigeonimage)

        self.widgets.statusbutton = sb = StatusButton(self.parent)
        self.widgets.statusbutton.set_editable(False)
        self.widgets.statusbutton.set_sensitive(False)
        self.widgets.grid.attach(sb.widget, 2, 2, 1, 1)

        self.widgets.root_view.show_all()

    # Public methods
    def get_root_widget(self):
        return self.widgets.root_view

    def set_details(self, pigeon):
        if pigeon is None:
            self.widgets.errorlabel.show()
            self.widgets.alignUnEdit.set_sensitive(False)
            return

        self.pigeon = pigeon

        self.widgets.entryband.set_pigeon(pigeon)
        self.widgets.entrysire.set_pigeon(pigeon.sire)
        self.widgets.entrydam.set_pigeon(pigeon.dam)
        self.widgets.entrysex.set_sex(pigeon.sex)
        self.widgets.entrystrain.set_text(pigeon.strain)
        self.widgets.entryloft.set_text(pigeon.loft)
        self.widgets.entrycolour.set_text(pigeon.colour)
        self.widgets.entryname.set_text(pigeon.name)
        extra1, extra2, extra3, extra4, extra5, extra6 = pigeon.extra
        self.widgets.entryextra1.set_text(extra1)
        self.widgets.entryextra2.set_text(extra2)
        self.widgets.entryextra3.set_text(extra3)
        self.widgets.entryextra4.set_text(extra4)
        self.widgets.entryextra5.set_text(extra5)
        self.widgets.entryextra6.set_text(extra6)

        self.widgets.statusbutton.set_sensitive(True)
        self.widgets.statusbutton.set_pigeon(pigeon)
        self.widgets.pigeonimage.set_image(pigeon.main_image)

    def clear_details(self):
        self.pigeon = None

        self.widgets.entryband.clear()
        self.widgets.entrysire.clear()
        self.widgets.entrydam.clear()

        self.widgets.statusbutton.set_sensitive(False)
        self.widgets.statusbutton.set_default()
        self.widgets.pigeonimage.set_default_image()

        for entry in self.get_objects_from_prefix("entry"):
            if isinstance(entry, bandentry.BandEntry):
                continue
            if isinstance(entry, date.DateEntry):
                continue
            if isinstance(entry, sexentry.SexEntry):
                entry.set_sex(None)
                continue
            entry.set_text("")
        for text in self.get_objects_from_prefix("text"):
            text.get_buffer().set_text("")


class DetailsViewEdit(builder.GtkBuilder, GObject.GObject):
    __gsignals__ = {"edit-finished": (GObject.SIGNAL_RUN_LAST,
                                      None, (object, int)),
                    "edit-cancelled": (GObject.SIGNAL_RUN_LAST,
                                       None, ()),
                    }

    def __init__(self, parent=None, pigeon=None):
        builder.GtkBuilder.__init__(self, "DetailsView.ui", ["root_edit"])
        GObject.GObject.__init__(self)

        self.parent = parent or component.get("MainWindow")
        self.pigeon = pigeon
        self.pedigree_mode = False
        self.child = None

        self.widgets.pigeonimage_edit = PigeonImageWidget(True, self, parent)
        self.widgets.viewportImageEdit.add(self.widgets.pigeonimage_edit)

        self.widgets.statusbuttonedit = sb = StatusButton(self.parent)
        self.widgets.statusbuttonedit.set_editable(True)
        self.widgets.gridedit.attach(sb.widget, 2, 2, 1, 1)

        self.widgets.combocolour.set_data(Colour)
        self.widgets.combostrain.set_data(Strain)
        self.widgets.comboloft.set_data(Loft)

        self.widgets.root_edit.show_all()

    # Callbacks
    def on_entrysireedit_search_clicked(self, widget):
        return self._get_pigeonsearch_details(enums.Sex.cock)

    def on_entrydamedit_search_clicked(self, widget):
        return self._get_pigeonsearch_details(enums.Sex.hen)

    # Public methods
    def get_root_widget(self):
        return self.widgets.root_edit

    def get_child(self):
        return self.child

    def set_child(self, child):
        self.child = child

    def get_pedigree_mode(self):
        return self.pedigree_mode

    def set_pedigree_mode(self, mode):
        self.pedigree_mode = mode
        self.widgets.combosex.set_sensitive(not mode)

    def set_sex(self, value):
        self.widgets.combosex.set_active(value)

    def get_edit_details(self):
        country, letters, number, year = self.widgets.entrybandedit.get_band()
        sire = self.widgets.entrysireedit.get_band()
        dam = self.widgets.entrydamedit.get_band()
        if self.pigeon is None:
            visible = False if self.pedigree_mode else True
        else:
            visible = self.pigeon.visible
        data = {
            "band_country": country,
            "band_letters": letters,
            "band_number": number,
            "band_year": year,
            "band_format": self.widgets.entrybandedit.band_format,
            "sire": sire,
            "dam": dam,
            "visible": visible,
            "sex": self.widgets.combosex.get_sex(),
            "colour": self.widgets.combocolour.get_child().get_text(),
            "name": self.widgets.entrynameedit.get_text(),
            "strain": self.widgets.combostrain.get_child().get_text(),
            "loft": self.widgets.comboloft.get_child().get_text(),
            "image": self.widgets.pigeonimage_edit.get_image_path(),
            "extra1": self.widgets.entryextraedit1.get_text(),
            "extra2": self.widgets.entryextraedit2.get_text(),
            "extra3": self.widgets.entryextraedit3.get_text(),
            "extra4": self.widgets.entryextraedit4.get_text(),
            "extra5": self.widgets.entryextraedit5.get_text(),
            "extra6": self.widgets.entryextraedit6.get_text()
        }
        return data

    def clear_details(self):
        self.widgets.entrybandedit.clear()
        self.widgets.entrysireedit.clear()
        self.widgets.entrydamedit.clear()

        self.widgets.combocolour.get_child().set_text("")
        self.widgets.combostrain.get_child().set_text("")
        self.widgets.comboloft.get_child().set_text("")
        self.widgets.combosex.set_active(0)

        self.widgets.statusbuttonedit.set_default()
        self.widgets.pigeonimage_edit.set_default_image()

        self.widgets.entrynameedit.set_text("")
        for x in range(1, 7):
            getattr(self.widgets, "entryextraedit%s" % x).set_text("")

    def start_edit(self, operation):
        self._operation = operation
        if operation == enums.Action.edit:
            logger.debug("Start editing pigeon id=%s band=%s", self.pigeon.id, self.pigeon.band_tuple)
            self.widgets.entrybandedit.set_pigeon(self.pigeon)
            self.widgets.entrysireedit.set_pigeon(self.pigeon.sire)
            self.widgets.entrydamedit.set_pigeon(self.pigeon.dam)
            self.widgets.entrynameedit.set_text(self.pigeon.name)
            extra = self.pigeon.extra
            self.widgets.entryextraedit1.set_text(extra[0])
            self.widgets.entryextraedit2.set_text(extra[1])
            self.widgets.entryextraedit3.set_text(extra[2])
            self.widgets.entryextraedit4.set_text(extra[3])
            self.widgets.entryextraedit5.set_text(extra[4])
            self.widgets.entryextraedit6.set_text(extra[5])
            self.widgets.combocolour.get_child().set_text(self.pigeon.colour)
            self.widgets.combostrain.get_child().set_text(self.pigeon.strain)
            self.widgets.comboloft.get_child().set_text(self.pigeon.loft)
            self.widgets.combosex.set_active(self.pigeon.sex)

            self.widgets.statusbuttonedit.set_pigeon(self.pigeon)
            image = self.pigeon.main_image
            self.widgets.pigeonimage_edit.set_image(image)
        else:
            logger.debug("Start adding a pigeon")

        self.widgets.entrybandedit.grab_focus()

    def operation_saved(self):
        """
        Collect pigeon data, save it to the database and do the required
        steps for saving extra data.

        Return True to keep dialog open, False to close it
        """

        try:
            data = self.get_edit_details()
        except errors.InvalidInputError as msg:
            ErrorDialog(msg.value, self.parent)
            return True

        status = self.widgets.statusbuttonedit.get_current_status()
        statusdata = self.widgets.statusbuttonedit.get_current_data()

        if self._operation == enums.Action.edit:
            try:
                pigeon = corepigeon.update_pigeon(self.pigeon, data, status, statusdata)
            except errors.PigeonAlreadyExists:
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                return True
            except errors.PigeonAlreadyExistsHidden as exc:
                pigeon = exc.pigeon
                if WarningDialog(messages.MSG_SHOW_PIGEON, self.parent).run():
                    pigeon.visible = True
                    pigeon.save()
            except errors.InvalidInputError:
                # This is a corner case. Some status date is incorrect, but the
                # user chose another one. Don't bother him with this.
                pass
        elif self._operation == enums.Action.add:
            try:
                pigeon = corepigeon.add_pigeon(data, status, statusdata)
            except errors.PigeonAlreadyExists:
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                return True
            except errors.PigeonAlreadyExistsHidden as exc:
                pigeon = exc.pigeon
                if WarningDialog(messages.MSG_SHOW_PIGEON, self.parent).run():
                    pigeon.visible = True
                    pigeon.save()
            except errors.InvalidInputError:
                # See comment above
                pass

        self.emit("edit-finished", pigeon, self._operation)
        self.widgets.combocolour.add_item(data["colour"])
        self.widgets.combostrain.add_item(data["strain"])
        self.widgets.comboloft.add_item(data["loft"])
        logger.debug("Operation '%s' finished, pigeon id=%s band=%s", self._operation, pigeon.id, pigeon.band_tuple)

        return False

    def operation_cancelled(self):
        logger.debug("Operation '%s' cancelled", self._operation)
        self.emit("edit-cancelled")

    # Internal methods
    def _get_pigeonsearch_details(self, sex):
        try:
            country, letters, number, year = self.widgets.entrybandedit.get_band()
        except errors.InvalidInputError:
            ErrorDialog(messages.MSG_NO_PARENT, self.parent)
            return
        return (country, letters, number, year), sex, year
