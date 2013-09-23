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
import logging
logger = logging.getLogger(__name__)

import gtk
import gtk.gdk
import gobject

from pigeonplanner import const
from pigeonplanner import common
from pigeonplanner import errors
from pigeonplanner import builder
from pigeonplanner import messages
from pigeonplanner import thumbnail
from pigeonplanner import database
from pigeonplanner import pigeonparser
from pigeonplanner.ui import tools
from pigeonplanner.ui import utils
from pigeonplanner.ui import dialogs
from pigeonplanner.ui import filechooser
from pigeonplanner.ui.widgets import date
from pigeonplanner.ui.widgets import sexentry
from pigeonplanner.ui.widgets import bandentry
from pigeonplanner.ui.messagedialog import ErrorDialog, WarningDialog


RESPONSE_EDIT = 10
RESPONSE_SAVE = 12


_ICONTHEME = gtk.icon_theme_get_default()
try:
    _ICON_ZOOM = _ICONTHEME.load_icon("gtk-find", 22, 0)
    CURSOR_ZOOM = gtk.gdk.Cursor(gtk.gdk.display_get_default(), _ICON_ZOOM, 0, 0)
except Exception as exc:
    #TODO: logging the exception causes trouble on OS X
    ##logger.warning("Can't load zoom cursor icon:", exc)
    logger.warning("Can't load zoom cursor icon")
    CURSOR_ZOOM = None


class PigeonAlreadyExists(Exception): pass


class DetailsDialog(gtk.Dialog):
    def __init__(self, pigeon=None, parent=None, mode=None):
        gtk.Dialog.__init__(self, None, parent, gtk.DIALOG_MODAL)
        if pigeon is None:
            title = _("Details of pigeon")
        else:
            title = _("Details of %s") %pigeon.get_band_string()
        self.set_title(title)
        self.set_resizable(False)
        if parent is None:
            self.set_position(gtk.WIN_POS_MOUSE)

        self.details = DetailsView(self)
        self.vbox.pack_start(self.details.get_root_widget(), False, False)
        if mode == const.ADD:
            self.details.clear_details()
        else:
            self.details.set_details(pigeon)
        if mode in (const.EDIT, const.ADD):
            self.details.start_edit(mode)
            self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                             gtk.STOCK_SAVE, RESPONSE_SAVE)
            self.set_default_response(RESPONSE_SAVE)
        else:
            self.add_buttons(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
            self.set_default_response(gtk.RESPONSE_CLOSE)
        self.run()

    def run(self):
        self.connect('response', self.on_dialog_response)
        self.show_all()

    def on_dialog_response(self, dialog, response_id):
        keep_alive = False
        if response_id in (gtk.RESPONSE_CLOSE, gtk.RESPONSE_DELETE_EVENT):
            pass
        elif response_id == RESPONSE_SAVE:
            keep_alive = self.details.operation_saved()
        elif response_id == gtk.RESPONSE_CANCEL:
            self.details.operation_cancelled()

        if not keep_alive:
            dialog.destroy()


class PigeonImageWidget(gtk.EventBox):
    def __init__(self, editable, view, parent=None):
        gtk.EventBox.__init__(self)
        if editable:
            self.connect('button-press-event', self.on_editable_button_press_event)
        else:
            self.connect('enter-notify-event', self.on_enter_notify_event)
            self.connect('leave-notify-event', self.on_leave_notify_event)
            self.connect('button-press-event', self.on_button_press_event)

        self._view = view
        self._parent = parent
        self._imagewidget = gtk.Image()
        self._imagewidget.set_size_request(200, 200)
        self.add(self._imagewidget)
        self._imagepath = None
        self.set_default_image()

    def on_enter_notify_event(self, widget, event):
        if self._imagepath:
            self.get_window().set_cursor(CURSOR_ZOOM)

    def on_leave_notify_event(self, widget, event):
        self.get_window().set_cursor(None)

    def on_button_press_event(self, widget, event):
        if self._view.pigeon is None:
            return
        parent = None if isinstance(self._parent, gtk.Dialog) else self._parent
        tools.PhotoAlbum(parent, self._view.pigeon.get_pindex())

    def on_editable_button_press_event(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_ADD, self.on_open_imagechooser, None),
                (gtk.STOCK_REMOVE, self.set_default_image, None)]
            utils.popup_menu(event, entries)
        else:
            self.on_open_imagechooser()

    def on_open_imagechooser(self, widget=None):
        chooser = filechooser.ImageChooser(self._parent)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            try:
                pb = gtk.gdk.pixbuf_new_from_file_at_size(filename, 200, 200)
            except gobject.GError, exc:
                logger.error("Can't set image '%s':%s", filename, exc)
                ErrorDialog(messages.MSG_INVALID_IMAGE, self._parent)
            else:
                self._imagewidget.set_from_pixbuf(pb)
                self._imagepath = filename
        elif response == chooser.RESPONSE_CLEAR:
            self.set_default_image()
        chooser.destroy()

    def set_default_image(self, widget=None):
        logo = gtk.gdk.pixbuf_new_from_file_at_size(const.LOGO_IMG, 75, 75)
        self._imagewidget.set_from_pixbuf(logo)
        self._imagepath = None

    def set_image(self, path=None):
        if path:
            pixbuf = thumbnail.get_image(path)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(const.LOGO_IMG, 75, 75)
        self._imagewidget.set_from_pixbuf(pixbuf)
        self._imagepath = path

    def get_image_path(self):
        return self._imagepath


class DetailsView(builder.GtkBuilder, gobject.GObject):
    __gsignals__ = {'edit-finished': (gobject.SIGNAL_RUN_LAST,
                                      None, (object, int)),
                    'edit-cancelled': (gobject.SIGNAL_RUN_LAST,
                                       None, ()),
                    }
    def __init__(self, parent):
        builder.GtkBuilder.__init__(self, "DetailsView.ui")
        gobject.GObject.__init__(self)

        self.parent = parent
        self.pedigree_mode = False
        self.pigeon = None
        self.child = None

        self.widgets.pigeonimage = PigeonImageWidget(False, self, parent)
        self.widgets.viewportImage.add(self.widgets.pigeonimage)
        self.widgets.pigeonimage_edit = PigeonImageWidget(True, self, parent)
        self.widgets.viewportImageEdit.add(self.widgets.pigeonimage_edit)

        self.widgets.combocolour.set_data(database.get_all_data(database.Tables.COLOURS), sort=False)
        self.widgets.combostrain.set_data(database.get_all_data(database.Tables.STRAINS), sort=False)
        self.widgets.comboloft.set_data(database.get_all_data(database.Tables.LOFTS), sort=False)

        self.widgets.statusdialog.set_transient_for(parent)
        self.widgets.root.show_all()

    # Callbacks
    ## Status
    def on_buttonstatus_clicked(self, widget):
        if self.pigeon is None: return
        status = self.pigeon.get_active()
        self.widgets.labelstatus.set_markup("<b>%s</b>" %_(common.statusdic[status]))
        self.widgets.notebookstatus.set_current_page(status)
        self._set_status_editable(False)
        self.widgets.hboxstatusedit.hide()
        self.widgets.hboxstatusnormal.show()
        self.widgets.statusdialog.show()
        self.widgets.buttonstatusok.grab_focus()

    def on_buttonstatusedit_clicked(self, widget):
        self._set_status_editable(True)
        self.widgets.hboxstatusedit.show()
        self.widgets.hboxstatusnormal.hide()
        self.widgets.statusdialog.show()

    def on_combostatus_changed(self, widget):
        status = widget.get_active()
        self.widgets.notebookstatus.set_current_page(status)
        self._set_status_image(status)

    def on_statusdialog_close(self, widget, event=None):
        page = self.widgets.notebookstatus.get_current_page()
        table = self.widgets.notebookstatus.get_nth_page(page)
        for child in table.get_children():
            if isinstance(child, date.DateEntry):
                try:
                    # Just check the date, the value is used elsewhere
                    child.get_text()
                except errors.InvalidInputError, msg:
                    ErrorDialog(msg.value, self.parent)
                    return True
        self.widgets.statusdialog.hide()
        return True

    def on_findsire_clicked(self, widget):
        self._run_pigeondialog(const.SIRE)

    def on_finddam_clicked(self, widget):
        self._run_pigeondialog(const.DAM)

    # Public methods
    def get_root_widget(self):
        return self.widgets.root

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

    def set_details(self, pigeon):
        if pigeon is None:
            self.widgets.errorlabel.show()
            self.widgets.detailbook.set_sensitive(False)
            return

        self.pigeon = pigeon

        self.widgets.entryband.set_band(*pigeon.get_band())
        self.widgets.entrysire.set_band(*pigeon.get_sire())
        self.widgets.entrydam.set_band(*pigeon.get_dam())
        self.widgets.entrysex.set_sex(pigeon.get_sex())
        self.widgets.entrystrain.set_text(pigeon.get_strain())
        self.widgets.entryloft.set_text(pigeon.get_loft())
        self.widgets.entrycolour.set_text(pigeon.get_colour())
        self.widgets.entryname.set_text(pigeon.get_name())
        extra1, extra2, extra3, extra4, extra5, extra6 = pigeon.get_extra()
        self.widgets.entryextra1.set_text(extra1)
        self.widgets.entryextra2.set_text(extra2)
        self.widgets.entryextra3.set_text(extra3)
        self.widgets.entryextra4.set_text(extra4)
        self.widgets.entryextra5.set_text(extra5)
        self.widgets.entryextra6.set_text(extra6)

        self._set_status(pigeon.get_pindex(), pigeon.get_active())

        self.widgets.pigeonimage.set_image(pigeon.get_image())

    def get_edit_details(self):
        ring, year = self.widgets.entrybandedit.get_band()
        ringsire, yearsire = self.widgets.entrysireedit.get_band()
        ringdam, yeardam = self.widgets.entrydamedit.get_band()
        if self.pigeon is None:
            show = 0 if self.pedigree_mode else 1
        else:
            show = self.pigeon.get_visible()
        data = {"band": ring, "year": year, "show": show,
                "sire": ringsire, "yearsire": yearsire, "dam": ringdam, "yeardam": yeardam,
                "sex": self.widgets.combosex.get_active_text(),
                "active": self.widgets.combostatus.get_active(),
                "colour": self.widgets.combocolour.child.get_text(),
                "name": self.widgets.entrynameedit.get_text(),
                "strain": self.widgets.combostrain.child.get_text(),
                "loft": self.widgets.comboloft.child.get_text(),
                "image": self.widgets.pigeonimage_edit.get_image_path(),
                "extra1": self.widgets.entryextraedit1.get_text(),
                "extra2": self.widgets.entryextraedit2.get_text(),
                "extra3": self.widgets.entryextraedit3.get_text(),
                "extra4": self.widgets.entryextraedit4.get_text(),
                "extra5": self.widgets.entryextraedit5.get_text(),
                "extra6": self.widgets.entryextraedit6.get_text()}
        return data

    def clear_details(self):
        self.widgets.entryband.clear()
        self.widgets.entrybandedit.clear()
        self.widgets.entrysire.clear()
        self.widgets.entrysireedit.clear()
        self.widgets.entrydam.clear()
        self.widgets.entrydamedit.clear()

        self.widgets.combocolour.child.set_text('')
        self.widgets.combostrain.child.set_text('')
        self.widgets.comboloft.child.set_text('')
        self.widgets.combosex.set_active(0)
        self.widgets.combostatus.set_active(1)
        self.widgets.combostatus.emit('changed')

        self.widgets.pigeonimage.set_default_image()

        for entry in self.get_objects_from_prefix("entry"):
            if isinstance(entry, bandentry.BandEntry): continue
            if isinstance(entry, date.DateEntry): continue
            if isinstance(entry, sexentry.SexEntry):
                entry.set_sex(None)
                continue
            entry.set_text('')
        for text in self.get_objects_from_prefix("text"):
            text.get_buffer().set_text('')

    def start_edit(self, operation):
        self._operation = operation
        if operation == const.EDIT:
            logger.debug("Start editing pigeon '%s'", self.pigeon.get_pindex())
            self.widgets.entrybandedit.set_band(
                                *self.widgets.entryband.get_band(validate=False))
            self.widgets.entrysireedit.set_band(
                                *self.widgets.entrysire.get_band(validate=False))
            self.widgets.entrydamedit.set_band(
                                *self.widgets.entrydam.get_band(validate=False))
            self.widgets.entrynameedit.set_text(self.widgets.entryname.get_text())
            self.widgets.entryextraedit1.set_text(self.widgets.entryextra1.get_text())
            self.widgets.entryextraedit2.set_text(self.widgets.entryextra2.get_text())
            self.widgets.entryextraedit3.set_text(self.widgets.entryextra3.get_text())
            self.widgets.entryextraedit4.set_text(self.widgets.entryextra4.get_text())
            self.widgets.entryextraedit5.set_text(self.widgets.entryextra5.get_text())
            self.widgets.entryextraedit6.set_text(self.widgets.entryextra6.get_text())
            self.widgets.combocolour.child.set_text(self.widgets.entrycolour.get_text())
            self.widgets.combostrain.child.set_text(self.widgets.entrystrain.get_text())
            self.widgets.comboloft.child.set_text(self.widgets.entryloft.get_text())
            self.widgets.combosex.set_active(int(self.pigeon.get_sex()))

            status = self.pigeon.get_active()
            self.widgets.combostatus.set_active(status)
            self.widgets.notebookstatus.set_current_page(status)

            image = self.widgets.pigeonimage.get_image_path()
            self.widgets.pigeonimage_edit.set_image(image)
        else:
            logger.debug("Start adding a pigeon")

        self.widgets.detailbook.set_current_page(1)
        self.widgets.entrybandedit.grab_focus()

    def operation_saved(self):
        """ Collect pigeon data, save it to the database and do the required
            steps for saving extra data.

            Return True to keep dialog open, False to close it
        """
        try:
            data = self.get_edit_details()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.parent)
            return True
        if self._operation == const.EDIT:
            try:
                self._update_pigeon_data(data)
            except database.InvalidValueError:
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                return True
            except errors.InvalidInputError:
                # This is a corner case. Some status date is incorrect, but the
                # user choose another one. Don't bother him with this.
                pass
            old_pindex = self.pigeon.get_pindex()
            self.pigeon = pigeonparser.parser.update_pigeon(data["pindex"], old_pindex)
        elif self._operation == const.ADD:
            try:
                self._add_pigeon_data(data)
            except PigeonAlreadyExists, msg:
                logger.debug("Pigeon already exists '%s'", msg)
                return False
            except errors.InvalidInputError:
                # See comment above
                pass
            self.pigeon = pigeonparser.parser.add_pigeon(pindex=data["pindex"])
        self.set_details(self.pigeon)
        self.emit('edit-finished', self.pigeon, self._operation)
        combodata = [(self.widgets.combocolour, data["colour"], database.Tables.COLOURS),
                     (self.widgets.combostrain, data["strain"], database.Tables.STRAINS),
                     (self.widgets.comboloft, data["loft"], database.Tables.LOFTS)]
        for combo, value, table in combodata:
            database.add_data(table, value)
            combo.add_item(value)
        logger.debug("Operation '%s' finished", self._operation)

        return False

    def operation_cancelled(self):
        logger.debug("Operation '%s' cancelled", self._operation)
        self.emit('edit-cancelled')

    # Internal methods
    def _set_status_image(self, status):
        image = os.path.join(const.IMAGEDIR,
                             'status_%s.png' % common.statusdic[status].lower())
        self.widgets.imagestatus.set_from_file(image)
        self.widgets.imagestatus.set_tooltip_text(_(common.statusdic[status]))
        self.widgets.imagestatusedit.set_from_file(image)

    def _set_status(self, pindex, status):
        self._set_status_image(status)
        if status == const.DEAD:
            data = database.get_status(database.Tables.DEAD, pindex)
            if data:
                self.widgets.entrydatedead.set_text(data["date"])
                self.widgets.textinfodead.get_buffer().set_text(data["info"])
        elif status == const.SOLD:
            data = database.get_status(database.Tables.SOLD, pindex)
            if data:
                self.widgets.entrydatesold.set_text(data["date"])
                self.widgets.entrybuyersold.set_text(data["person"])
                self.widgets.textinfosold.get_buffer().set_text(data["info"])
        elif status == const.LOST:
            data = database.get_status(database.Tables.LOST, pindex)
            if data:
                self.widgets.entrydatelost.set_text(data["date"])
                self.widgets.entrypointlost.set_text(data["racepoint"])
                self.widgets.textinfolost.get_buffer().set_text(data["info"])
        elif status == const.BREEDER:
            data = database.get_status(database.Tables.BREEDER, pindex)
            if data:
                self.widgets.entrydatebreedfrom.set_text(data["start"])
                self.widgets.entrydatebreedto.set_text(data["end"])
                self.widgets.textinfobreeder.get_buffer().set_text(data["info"])
        elif status == const.LOANED:
            data = database.get_status(database.Tables.LOANED, pindex)
            if data:
                self.widgets.entrydateloan.set_text(data["loaned"])
                self.widgets.entrydateloanback.set_text(data["back"])
                self.widgets.entrypersonloan.set_text(data["person"])
                self.widgets.textinfoloan.get_buffer().set_text(data["info"])

    def _set_status_editable(self, value):
        def set_editable(widget, value):
            if isinstance(widget, gtk.ScrolledWindow):
                set_editable(widget.get_child(), value)
            try:
                widget.set_editable(value)
            except:
                pass
        for table in self.widgets.notebookstatus.get_children():
            table.foreach(set_editable, value)

    def _get_status_info(self, pindex=None):
        pindex = pindex or self.pigeon.get_pindex()

        bffr = self.widgets.textinfodead.get_buffer()
        dead = {"date": self.widgets.entrydatedead.get_text(),
                "info": bffr.get_text(*bffr.get_bounds()),
                "pindex": pindex}

        bffr = self.widgets.textinfosold.get_buffer()
        sold = {"person": self.widgets.entrybuyersold.get_text(),
                "date": self.widgets.entrydatesold.get_text(),
                "info": bffr.get_text(*bffr.get_bounds()),
                "pindex": pindex}

        bffr = self.widgets.textinfolost.get_buffer()
        lost = {"racepoint": self.widgets.entrypointlost.get_text(),
                "date": self.widgets.entrydatelost.get_text(),
                "info": bffr.get_text(*bffr.get_bounds()),
                "pindex": pindex}

        bffr = self.widgets.textinfobreeder.get_buffer()
        breed = {"start": self.widgets.entrydatebreedfrom.get_text(),
                 "end": self.widgets.entrydatebreedto.get_text(),
                 "info": bffr.get_text(*bffr.get_bounds()),
                "pindex": pindex}

        bffr = self.widgets.textinfoloan.get_buffer()
        loan = {"loaned": self.widgets.entrydateloan.get_text(),
                "back": self.widgets.entrydateloanback.get_text(),
                "person": self.widgets.entrypersonloan.get_text(),
                "info": bffr.get_text(*bffr.get_bounds()),
                "pindex": pindex}

        return dead, sold, lost, breed, loan

    def _insert_status_data(self, status, pindex, data=None):
        if data is None:
            dead, sold, lost, breed, loan = self._get_status_info(pindex)
        else:
            dead, sold, lost, breed, loan = data

        if status == const.DEAD:
            database.add_status(database.Tables.DEAD, dead)
        elif status == const.SOLD:
            database.add_status(database.Tables.SOLD, sold)
        elif status == const.LOST:
            database.add_status(database.Tables.LOST, lost)
        elif status == const.BREEDER:
            database.add_status(database.Tables.BREEDER, breed)
        elif status == const.LOANED:
            database.add_status(database.Tables.LOANED, loan)

    def _run_pigeondialog(self, sex):
        try:
            pindex = self.widgets.entrybandedit.get_pindex()
        except errors.InvalidInputError:
            ErrorDialog(messages.MSG_NO_PARENT, self.parent)
            return
        band, year = self.widgets.entrybandedit.get_band()
        dialog = dialogs.PigeonListDialog(self.parent)
        dialog.fill_treeview(pindex, sex, year)
        response = dialog.run()
        if response == gtk.RESPONSE_APPLY:
            pigeon = dialog.get_selected()
            if pigeon.is_cock():
                self.widgets.entrysireedit.set_pindex(pigeon.get_pindex())
            else:
                self.widgets.entrydamedit.set_pindex(pigeon.get_pindex())
        dialog.destroy()

    def _update_pigeon_data(self, data):
        """
        Update the data when a pigeon is edited
        """

        pindex = self.pigeon.get_pindex()
        pindex_new = common.get_pindex_from_band(data["band"], data["year"])
        data["pindex"] = pindex_new

        # Update the data in the pigeon table
        # Raises an exception when the pigeon is a duplicate. We catch this in
        # the calling method so be sure this database call is the first!
        database.update_pigeon(pindex, data)
        # Update pindex in the results table
        if database.pigeon_has_results(pindex):
            database.update_result_for_pindex(pindex, {"pindex": pindex_new})
        # Update pindex in the medication table
        if database.pigeon_has_medication(pindex):
            database.update_medication_for_pindex(pindex, {"pindex": pindex_new})
        # Remove the old thumbnail (if exists)
        image = data["image"]
        prev_image = self.pigeon.get_image()
        if image != prev_image and prev_image:
            try:
                os.remove(thumbnail.get_path(prev_image))
            except:
                pass
        # Update the status or create a new record
        status = self.widgets.combostatus.get_active()
        old_status = self.pigeon.get_active()
        dead, sold, lost, breed, loan = self._get_status_info(pindex_new)
        if status != old_status:
            if old_status != const.ACTIVE:
                database.remove_status(common.get_status(old_status), pindex)
            self._insert_status_data(status, pindex, (dead, sold, lost, breed, loan))
        else:
            if status == const.DEAD:
                database.update_status(database.Tables.DEAD, pindex, dead)
            elif status == const.SOLD:
                database.update_status(database.Tables.SOLD, pindex, sold)
            elif status == const.LOST:
                database.update_status(database.Tables.LOST, pindex, lost)
            elif status == const.BREEDER:
                database.update_status(database.Tables.BREEDER, pindex, breed)
            elif status == const.LOANED:
                database.update_status(database.Tables.LOANED, pindex, loan)

    def _add_pigeon_data(self, data):
        pindex = common.get_pindex_from_band(data["band"], data["year"])
        data["pindex"] = pindex

        # First we do some checks
        if database.pigeon_exists(pindex):
            if pigeonparser.parser.pigeons[pindex].show == 1:
                # The pigeon already exists, don't add it
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                raise PigeonAlreadyExists(pindex)
            else:
                # The pigeon exists, but doesn't show, ask to show again
                if WarningDialog(messages.MSG_SHOW_PIGEON, self.parent).run():
                    #TODO: review! This can't be right.
                    pigeonparser.parser.show = 1
                    database.update_pigeon(pindex, show=True)
                # Always return here. Either way the user doesn't want it
                # to show, or it is already set to visible, so don't add it.
                return
        # Checks say that this is really a none existing pigeon, so add it
        database.add_pigeon(data)
        status = self.widgets.combostatus.get_active()
        self._insert_status_data(status, pindex)

