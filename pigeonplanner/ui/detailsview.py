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

import const
import common
import errors
import builder
import messages
import thumbnail
import database
from ui import tools
from ui import utils
from ui import dialogs
from ui import filechooser
from ui.widgets import date
from ui.widgets import bandentry
from ui.widgets import comboboxes
from ui.messagedialog import ErrorDialog, WarningDialog
from translation import gettext as _


class PigeonAlreadyExists(Exception): pass


class DetailsDialog(gtk.Dialog):
    def __init__(self, database, parser, pigeon=None, parent=None, mode=None):
        gtk.Dialog.__init__(self, None, parent, gtk.DIALOG_MODAL,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        if pigeon is None:
            title = _("Details of pigeon")
        else:
            title = _("Details of %s") %pigeon.get_band_string()
        self.set_title(title)
        if parent is None:
            self.set_position(gtk.WIN_POS_MOUSE)

        self.details = DetailsView(self, database, parser, True)
        self.vbox.pack_start(self.details.get_widget(), False, False)
        if mode == const.ADD:
            self.details.clear_details()
        else:
            self.details.set_details(pigeon)
        if mode in (const.EDIT, const.ADD):
            self.details.start_edit(mode)
            self.details.connect('edit-finished', self.on_edit_finished)
            self.details.connect('edit-cancelled', self.on_edit_cancelled)
        self.run()

    def run(self):
        self.connect('response', self.on_dialog_response)
        self.show_all()

    def on_dialog_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE or \
           response_id == gtk.RESPONSE_DELETE_EVENT:
            dialog.destroy()

    def on_edit_finished(self, detailsview, pigeon, operation):
        detailsview.set_details(pigeon)
        self.destroy()

    def on_edit_cancelled(self, detailsview):
        self.destroy()


class DetailsView(builder.GtkBuilder, gobject.GObject):
    __gsignals__ = {'edit-finished': (gobject.SIGNAL_RUN_LAST,
                                      None, (object, int)),
                    'edit-cancelled': (gobject.SIGNAL_RUN_LAST,
                                       None, ()),
                    }
    def __init__(self, parent, database, parser, in_dialog=False):
        builder.GtkBuilder.__init__(self, "DetailsView.ui")
        gobject.GObject.__init__(self)

        self.parent = parent
        self.database = database
        self.parser = parser
        self.in_dialog = in_dialog
        self.pedigree_mode = False
        self.pigeon = None
        self.child = None

        combos = {self.combocolour: self.database.COLOURS,
                  self.combostrain: self.database.STRAINS,
                  self.comboloft: self.database.LOFTS}
        for combo, value in combos.items():
            comboboxes.fill_combobox(combo, self.database.select_from_table(value))
            comboboxes.set_entry_completion(combo)
            combo.child.set_activates_default(True)

        ag = gtk.AccelGroup()
        key, modifier = gtk.accelerator_parse('Escape')
        self.buttoncancel.add_accelerator('clicked', ag, key, modifier,
                                                     gtk.ACCEL_VISIBLE)
        self.parent.add_accel_group(ag)

        self.statusdialog.set_transient_for(parent)
        self.root.unparent()
        self.root.show_all()

    # Callbacks
    def on_buttonsave_clicked(self, widget):
        try:
            data = self.get_details()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.parent)
            return
        if self._operation == const.EDIT:
            try:
                self._update_pigeon_data(data)
            except database.InvalidValueError:
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                return
            old_pindex = self.pigeon.get_pindex()
            self.pigeon = self.parser.update_pigeon(data[0], old_pindex)
        elif self._operation == const.ADD:
            try:
                self._add_pigeon_data(data)
            except PigeonAlreadyExists, msg:
                logger.debug("Pigeon already exists '%s'", msg)
                return
            self.pigeon = self.parser.add_pigeon(pindex=data[0])
        self.emit('edit-finished', self.pigeon, self._operation)
        self._finish_edit(data)
        logger.debug("Operation '%s' finished", self._operation)

    def on_buttoncancel_clicked(self, widget):
        logger.debug("Operation '%s' cancelled", self._operation)
        self.emit('edit-cancelled')
        self._finish_edit()

    ## Image
    def on_eventbox_press(self, widget, event):
        if self.pigeon is None or self.in_dialog: return
        tools.PhotoAlbum(self.parent, self.parser, self.database,
                         self.pigeon.get_pindex())

    def on_eventimage_press(self, widget, event):
        if event.button == 3:
            entries = [
                (gtk.STOCK_ADD, self.on_open_imagechooser, None),
                (gtk.STOCK_REMOVE, self.set_default_image, None)]
            utils.popup_menu(event, entries)
        else:
            self.on_open_imagechooser()

    def on_open_imagechooser(self, widget=None):
        chooser = filechooser.ImageChooser(self.parent)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            try:
                pb = gtk.gdk.pixbuf_new_from_file_at_size(filename, 200, 200)
            except gobject.GError, exc:
                logger.error("Can't set image '%s':%s", filename, exc)
                ErrorDialog(messages.MSG_INVALID_IMAGE, self.parent)
            else:
                self.imagepigeon.set_from_pixbuf(pb)
                self.imagepigeonedit.set_from_pixbuf(pb)
                self.imagepigeon.set_data('image-path', filename)
        elif response == chooser.RESPONSE_CLEAR:
            self.set_default_image()
        chooser.destroy()

    ## Status
    def on_buttonstatus_clicked(self, widget):
        if self.pigeon is None: return
        status = self.pigeon.get_active()
        self.labelstatus.set_markup("<b>%s</b>" %_(common.statusdic[status]))
        self.notebookstatus.set_current_page(status)
        self._set_status_editable(False)
        self.hboxstatusedit.hide()
        self.hboxstatusnormal.show()
        self.statusdialog.show()
        self.buttonstatusok.grab_focus()

    def on_buttonstatusedit_clicked(self, widget):
        self._set_status_editable(True)
        self.hboxstatusedit.show()
        self.hboxstatusnormal.hide()
        self.statusdialog.show()

    def on_combostatus_changed(self, widget):
        status = widget.get_active()
        self.notebookstatus.set_current_page(status)
        self._set_status_image(status)

    def on_statusdialog_close(self, widget, event=None):
        page = self.notebookstatus.get_current_page()
        table = self.notebookstatus.get_nth_page(page)
        for child in table.get_children():
            if isinstance(child, date.DateEntry):
                try:
                    # Just check the date, the value is used elsewhere
                    child.get_text()
                except errors.InvalidInputError, msg:
                    ErrorDialog(msg.value, self.parent)
                    return True
        self.statusdialog.hide()
        return True

    def on_findsire_clicked(self, widget):
        self._run_pigeondialog(const.SIRE)

    def on_finddam_clicked(self, widget):
        self._run_pigeondialog(const.DAM)

    # Public methods
    def get_widget(self):
        return self.root

    def get_child(self):
        return self.child

    def set_child(self, child):
        self.child = child

    def get_pedigree_mode(self):
        return self.pedigree_mode

    def set_pedigree_mode(self, mode):
        self.pedigree_mode = mode
        self.combosex.set_sensitive(not mode)

    def set_sex(self, value):
        self.combosex.set_active(value)

    def set_details(self, pigeon):
        self.pigeon = pigeon

        self.entryband.set_band(*pigeon.get_band())
        self.entrysire.set_band(*pigeon.get_sire())
        self.entrydam.set_band(*pigeon.get_dam())
        self.entrysex.set_text(pigeon.get_sex_string())
        self.entrystrain.set_text(pigeon.get_strain())
        self.entryloft.set_text(pigeon.get_loft())
        self.entrycolour.set_text(pigeon.get_colour())
        self.entryname.set_text(pigeon.get_name())
        extra1, extra2, extra3, extra4, extra5, extra6 = pigeon.get_extra()
        self.entryextra1.set_text(extra1)
        self.entryextra2.set_text(extra2)
        self.entryextra3.set_text(extra3)
        self.entryextra4.set_text(extra4)
        self.entryextra5.set_text(extra5)
        self.entryextra6.set_text(extra6)

        self._set_status(pigeon.get_pindex(), pigeon.get_active())

        imagepath = pigeon.get_image()
        if imagepath:
            pixbuf = thumbnail.get_image(imagepath)
            self.imagepigeon.set_data('image-path', imagepath)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(const.LOGO_IMG, 75, 75)
            self.imagepigeon.set_data('image-path', None)
        self.imagepigeon.set_from_pixbuf(pixbuf)

    def get_details(self):
        ring, year = self.entrybandedit.get_band()
        ringsire, yearsire = self.entrysireedit.get_band()
        ringdam, yeardam = self.entrydamedit.get_band()
        if self.pigeon is None:
            show = 0 if self.pedigree_mode else 1
        else:
            show = self.pigeon.get_visible()
        datalist = [ring, year,
                    self.combosex.get_active_text(),
                    show,
                    self.combostatus.get_active(),
                    self.combocolour.child.get_text(),
                    self.entrynameedit.get_text(),
                    self.combostrain.child.get_text(),
                    self.comboloft.child.get_text(),
                    self.imagepigeon.get_data('image-path'),
                    ringsire, yearsire, ringdam, yeardam,
                    self.entryextraedit1.get_text(),
                    self.entryextraedit2.get_text(),
                    self.entryextraedit3.get_text(),
                    self.entryextraedit4.get_text(),
                    self.entryextraedit5.get_text(),
                    self.entryextraedit6.get_text()]
        return datalist

    def set_default_image(self, widget=None, edit=False):
        logo = gtk.gdk.pixbuf_new_from_file_at_size(const.LOGO_IMG, 75, 75)
        self.imagepigeonedit.set_from_pixbuf(logo)
        self.imagepigeon.set_data('image-path', None)
        if not edit:
            self.imagepigeon.set_from_pixbuf(logo)

    def clear_details(self):
        self.entryband.clear()
        self.entrybandedit.clear()
        self.entrysire.clear()
        self.entrysireedit.clear()
        self.entrydam.clear()
        self.entrydamedit.clear()

        self.combocolour.child.set_text('')
        self.combostrain.child.set_text('')
        self.comboloft.child.set_text('')
        self.combosex.set_active(0)
        self.combostatus.set_active(1)
        self.combostatus.emit('changed')

        self.set_default_image()

        for entry in self.get_objects_from_prefix("entry"):
            if isinstance(entry, bandentry.BandEntry): continue
            if isinstance(entry, date.DateEntry): continue
            entry.set_text('')
        for text in self.get_objects_from_prefix("text"):
            text.get_buffer().set_text('')

    def start_edit(self, operation):
        self._operation = operation
        if operation == const.EDIT:
            logger.debug("Start editing pigeon '%s'", self.pigeon.get_pindex())
            self.entrybandedit.set_band(*self.entryband.get_band(validate=False))
            self.entrysireedit.set_band(*self.entrysire.get_band(validate=False))
            self.entrydamedit.set_band(*self.entrydam.get_band(validate=False))
            self.entrynameedit.set_text(self.entryname.get_text())
            self.entryextraedit1.set_text(self.entryextra1.get_text())
            self.entryextraedit2.set_text(self.entryextra2.get_text())
            self.entryextraedit3.set_text(self.entryextra3.get_text())
            self.entryextraedit4.set_text(self.entryextra4.get_text())
            self.entryextraedit5.set_text(self.entryextra5.get_text())
            self.entryextraedit6.set_text(self.entryextra6.get_text())
            self.combocolour.child.set_text(self.entrycolour.get_text())
            self.combostrain.child.set_text(self.entrystrain.get_text())
            self.comboloft.child.set_text(self.entryloft.get_text())
            self.combosex.set_active(int(self.pigeon.get_sex()))

            status = self.pigeon.get_active()
            self.combostatus.set_active(status)
            self.notebookstatus.set_current_page(status)

            image = self.imagepigeon.get_data('image-path')
            if image is None:
                self.set_default_image(edit=True)
            else:
                pixbuf = thumbnail.get_image(image)
                self.imagepigeonedit.set_from_pixbuf(pixbuf)
        else:
            logger.debug("Start adding a pigeon")

        self.detailbook.set_current_page(1)
        self.entrybandedit.grab_focus()
        self.buttonsave.grab_default()

    # Internal methods
    def _set_status_image(self, status):
        image = os.path.join(const.IMAGEDIR,
                             'status_%s.png' % common.statusdic[status].lower())
        self.imagestatus.set_from_file(image)
        self.imagestatus.set_tooltip_text(_(common.statusdic[status]))
        self.imagestatusedit.set_from_file(image)

    def _set_status(self, pindex, status):
        self._set_status_image(status)
        if status == const.DEAD:
            data = self.database.get_dead_data(pindex)
            if data:
                self.entrydatedead.set_text(data[0])
                self.textinfodead.get_buffer().set_text(data[1])
        elif status == const.SOLD:
            data = self.database.get_sold_data(pindex)
            if data:
                self.entrydatesold.set_text(data[1])
                self.entrybuyersold.set_text(data[0])
                self.textinfosold.get_buffer().set_text(data[2])
        elif status == const.LOST:
            data = self.database.get_lost_data(pindex)
            if data:
                self.entrydatelost.set_text(data[1])
                self.entrypointlost.set_text(data[0])
                self.textinfolost.get_buffer().set_text(data[2])
        elif status == const.BREEDER:
            data = self.database.get_breeder_data(pindex)
            if data:
                self.entrydatebreedfrom.set_text(data[0])
                self.entrydatebreedto.set_text(data[1])
                self.textinfobreeder.get_buffer().set_text(data[2])
        elif status == const.LOANED:
            data = self.database.get_loan_data(pindex)
            if data:
                self.entrydateloan.set_text(data[0])
                self.entrydateloanback.set_text(data[1])
                self.entrypersonloan.set_text(data[2])
                self.textinfoloan.get_buffer().set_text(data[3])

    def _set_status_editable(self, value):
        def set_editable(widget, value):
            if isinstance(widget, gtk.ScrolledWindow):
                set_editable(widget.get_child(), value)
            try:
                widget.set_editable(value)
            except:
                pass
        for table in self.notebookstatus.get_children():
            table.foreach(set_editable, value)

    def _finish_edit(self, datalist=None):
        self.detailbook.set_current_page(0)
        if datalist is not None:
            data = [(self.combocolour, datalist[6], self.database.COLOURS),
                    (self.combostrain, datalist[8], self.database.STRAINS),
                    (self.comboloft, datalist[9], self.database.LOFTS)]
            for combo, value, table in data:
                self._update_combo_data(combo, value, table)

    def _update_combo_data(self, combo, data, table):
        if not data: return
        try:
            self.database.insert_into_table(table, (data,))
        except database.InvalidValueError:
            return
        model = combo.get_model()
        for treerow in model:
            if data in treerow:
                return
        model.append([data])
        model.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def _get_status_info(self):
        bffr = self.textinfodead.get_buffer()
        dead = [self.entrydatedead.get_text(),
                bffr.get_text(*bffr.get_bounds())]

        bffr = self.textinfosold.get_buffer()
        sold = [self.entrybuyersold.get_text(),
                self.entrydatesold.get_text(),
                bffr.get_text(*bffr.get_bounds())]

        bffr = self.textinfolost.get_buffer()
        lost = [self.entrypointlost.get_text(),
                self.entrydatelost.get_text(),
                bffr.get_text(*bffr.get_bounds())]

        bffr = self.textinfobreeder.get_buffer()
        breed = [self.entrydatebreedfrom.get_text(),
                 self.entrydatebreedto.get_text(),
                 bffr.get_text(*bffr.get_bounds())]

        bffr = self.textinfoloan.get_buffer()
        loan = [self.entrydateloan.get_text(),
                self.entrydateloanback.get_text(),
                self.entrypersonloan.get_text(),
                bffr.get_text(*bffr.get_bounds())]

        return dead, sold, lost, breed, loan

    def _insert_status_data(self, status, pindex, data=None):
        if data is None:
            dead, sold, lost, breed, loan = self._get_status_info()
        else:
            dead, sold, lost, breed, loan = data

        if status == const.DEAD:
            dead.insert(0, pindex)
            self.database.insert_into_table(self.database.DEAD, dead)
        elif status == const.SOLD:
            sold.insert(0, pindex)
            self.database.insert_into_table(self.database.SOLD, sold)
        elif status == const.LOST:
            lost.insert(0, pindex)
            self.database.insert_into_table(self.database.LOST, lost)
        elif status == const.BREEDER:
            breed.insert(0, pindex)
            self.database.insert_into_table(self.database.BREEDER, breed)
        elif status == const.LOANED:
            loan.insert(0, pindex)
            self.database.insert_into_table(self.database.LOANED, loan)

    def _run_pigeondialog(self, sex):
        try:
            pindex = self.entrybandedit.get_pindex()
        except errors.InvalidInputError:
            ErrorDialog(messages.MSG_NO_PARENT, self.parent)
            return
        band, year = self.entrybandedit.get_band()
        dialog = dialogs.PigeonListDialog(self.parent)
        dialog.fill_treeview(self.parser, pindex, sex, year)
        response = dialog.run()
        if response == gtk.RESPONSE_APPLY:
            pigeon = dialog.get_selected()
            if pigeon.is_cock():
                self.entrysireedit.set_pindex(pigeon.get_pindex())
            else:
                self.entrydamedit.set_pindex(pigeon.get_pindex())
        dialog.destroy()

    def _update_pigeon_data(self, datalist):
        """
        Update the data when a pigeon is edited
        """

        pindex = self.pigeon.get_pindex()
        pindex_new = common.get_pindex_from_band(datalist[0], datalist[1])
        datalist.insert(0, pindex_new)
        datalist.append(pindex)

        # Update the data in the pigeon table
        # Raises an exception when the pigeon is a duplicate. We catch this in
        # the calling method so be sure this database call is the first!
        self.database.update_table(self.database.PIGEONS, datalist, 1, 1)
        # Update pindex in the results table
        if self.database.has_results(pindex):
            self.database.update_table(self.database.RESULTS,
                                       (pindex_new, pindex), 1, 1)
        # Update pindex in the medication table
        if self.database.has_medication(pindex):
            self.database.update_table(self.database.MED,
                                       (pindex_new, pindex), 2, 2)
        # Remove the old thumbnail (if exists)
        image = datalist[10]
        prev_image = self.pigeon.get_image()
        if image != prev_image and prev_image:
            try:
                os.remove(thumbnail.get_path(prev_image))
            except:
                pass
        # Update the status or create a new record
        status = self.combostatus.get_active()
        old_status = self.pigeon.get_active()
        dead, sold, lost, breed, loan = self._get_status_info()
        if status != old_status:
            if old_status != const.ACTIVE:
                self.database.delete_from_table(common.statusdic[old_status],
                                                pindex)
            self._insert_status_data(status, pindex,
                                     (dead, sold, lost, breed, loan))
        else:
            if status == const.DEAD:
                dead.append(pindex)
                self.database.update_table(self.database.DEAD, dead, 2, 1)
            elif status == const.SOLD:
                sold.append(pindex)
                self.database.update_table(self.database.SOLD, sold, 2, 1)
            elif status == const.LOST:
                lost.append(pindex)
                self.database.update_table(self.database.LOST, lost, 2, 1)
            elif status == const.BREEDER:
                breed.append(pindex)
                self.database.update_table(self.database.BREEDER, breed, 2, 1)
            elif status == const.LOANED:
                loan.append(pindex)
                self.database.update_table(self.database.LOANED, loan, 2, 1)

    def _add_pigeon_data(self, datalist):
        pindex = common.get_pindex_from_band(datalist[0], datalist[1])
        datalist.insert(0, pindex)

        # First we do some checks
        if self.database.has_pigeon(pindex):
            if self.parser.pigeons[pindex].show == 1:
                # The pigeon already exists, don't add it
                ErrorDialog(messages.MSG_PIGEON_EXISTS, self.parent)
                raise PigeonAlreadyExists(pindex)
            else:
                # The pigeon exists, but doesn't show, ask to show again
                if WarningDialog(messages.MSG_SHOW_PIGEON, self.parent).run():
                    self.parser.show = 1
                    self.database.update_table(self.database.PIGEONS,
                                               (1, pindex), 5, 1)
                # Always return here. Either way the user doesn't want it
                # to show, or it is already set to visible, so don't add it.
                return
        # Checks say that this is really a none existing pigeon, so add it
        self.database.insert_into_table(self.database.PIGEONS, datalist)
        status = self.combostatus.get_active()
        self._insert_status_data(status, pindex)

