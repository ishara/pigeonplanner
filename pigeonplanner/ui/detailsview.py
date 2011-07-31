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
import checks
import builder
import messages
import thumbnail
from ui import tools
from ui import dialogs
from ui import filechooser
from ui.widgets import date
from ui.widgets import menus
from ui.widgets import bandentry
from ui.widgets import comboboxes


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


class DetailsView(builder.GtkBuilder):
    __gsignals__ = {'edit-finished': (gobject.SIGNAL_RUN_LAST,
                                      None, (object, int)),
                    'edit-cancelled': (gobject.SIGNAL_RUN_LAST,
                                       None, ()),
                    }
    def __init__(self, parent, database, parser, in_dialog=False):
        builder.GtkBuilder.__init__(self, "DetailsView.ui")

        self.parent = parent
        self.database = database
        self.parser = parser
        self.in_dialog = in_dialog
        self.pedigree_mode = False
        self.pigeon = None
        self.child = None

        self.entryband = bandentry.BandEntry()
        self.hbox.pack_start(self.entryband)
        self.entrysire = bandentry.BandEntry()
        self.table.attach(self.entrysire, 1, 2, 4, 5, 0, 0)
        self.entrydam = bandentry.BandEntry()
        self.table.attach(self.entrydam, 1, 2, 5, 6, 0, 0)
        self.entrybandedit = bandentry.BandEntry(True)
        self.hboxedit.pack_start(self.entrybandedit)
        self.entrysireedit = bandentry.BandEntry(True)
        self.hboxsire.pack_start(self.entrysireedit)
        self.entrydamedit = bandentry.BandEntry(True)
        self.hboxdam.pack_start(self.entrydamedit)

        self.combosex = comboboxes.SexCombobox()
        self.tableedit.attach(self.combosex, 1, 2, 1, 2, gtk.SHRINK, gtk.FILL)

        combos = {self.combocolour: self.database.COLOURS,
                  self.combostrain: self.database.STRAINS,
                  self.comboloft: self.database.LOFTS}
        for combo, value in combos.items():
            comboboxes.fill_combobox(combo, self.database.select_from_table(value))
            comboboxes.set_entry_completion(combo)
            combo.child.set_activates_default(True)

        self.entrydatedead = date.DateEntry()
        self.tabledead.attach(self.entrydatedead, 1, 2, 0, 1, 0, 0)
        self.entrydatesold = date.DateEntry()
        self.tablesold.attach(self.entrydatesold, 1, 2, 0, 1, 0, 0)
        self.entrydatelost = date.DateEntry()
        self.tablelost.attach(self.entrydatelost, 1, 2, 0, 1, 0, 0)

        ag = gtk.AccelGroup()
        key, modifier = gtk.accelerator_parse('Escape')
        self.buttoncancel.add_accelerator('clicked', ag, key, modifier,
                                                     gtk.ACCEL_VISIBLE)
        self.parent.add_accel_group(ag)

        self.finddialog.set_transient_for(parent)
        self.statusdialog.set_transient_for(parent)
        self.root.unparent()
        self.root.show_all()

    # Callbacks
    def on_buttonsave_clicked(self, widget):
        entries = [self.entrybandedit, self.entrysireedit, self.entrydamedit]
        for entry in entries:
            ring, year = entry.get_band()
            # Sire and dam input are not required
            if (ring == '' and year == '') and entry != self.entrybandedit:
                continue
            try:
                checks.check_ring_entry(ring, year)
            except checks.InvalidInputError, msg:
                dialogs.MessageDialog(const.ERROR, msg.value, self.parent)
                return
        data = self.get_details()
        if self._operation == const.EDIT:
            self._update_pigeon_data(data)
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
            menus.popup_menu(event, entries)
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
                dialogs.MessageDialog(const.ERROR, messages.MSG_INVALID_IMAGE,
                                      self.parent)
            else:
                self.imagepigeon.set_from_pixbuf(pb)
                self.imagepigeonedit.set_from_pixbuf(pb)
                self.imagepigeon.set_data('image-path', filename)
        elif response == chooser.RESPONSE_CLEAR:
            self.set_default_image()
        chooser.destroy()

    ## Status
    def on_dialog_delete(self, dialog, event):
        dialog.hide()
        return True

    def on_buttonstatus_clicked(self, widget):
        if self.pigeon is None: return
        status = self.pigeon.get_active()
        self.labelstatus.set_markup("<b>%s</b>" %_(common.statusdic[status]))
        self.notebookstatus.set_current_page(status)
        self._set_status_editable(False)
        self.hboxstatusedit.hide()
        self.hboxstatusnormal.show()
        self.statusdialog.show()
        self.buttonstatusclose.grab_focus()

    def on_buttonstatusedit_clicked(self, widget):
        self._set_status_editable(True)
        self.hboxstatusedit.show()
        self.hboxstatusnormal.hide()
        self.statusdialog.show()

    def on_combostatus_changed(self, widget):
        status = widget.get_active()
        self.notebookstatus.set_current_page(status)
        self._set_status_image(status)

    def on_buttonstatusclose_clicked(self, widget):
        self.statusdialog.hide()

    def on_findsire_clicked(self, widget):
        self._fill_find_treeview(const.SIRE, self.entrybandedit.get_band())

    def on_finddam_clicked(self, widget):
        self._fill_find_treeview(const.DAM, self.entrybandedit.get_band())

    def on_findadd_clicked(self, widget):
        model, rowiter = self.treeviewfind.get_selection().get_selected()
        if not rowiter: return
        pindex = model[rowiter][0]
        ring = model[rowiter][1]
        year = model[rowiter][2]
        if int(self.parser.pigeons[pindex].sex) == const.SIRE:
            self.entrysireedit.set_band(ring, year)
        else:
            self.entrydamedit.set_band(ring, year)
        self.finddialog.hide()

    def on_findcancel_clicked(self, widget):
        self.finddialog.hide()

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
            pixbuf = const.LOGO_IMG
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
        self.imagepigeonedit.set_from_pixbuf(const.LOGO_IMG)
        self.imagepigeon.set_data('image-path', None)
        if not edit:
            self.imagepigeon.set_from_pixbuf(const.LOGO_IMG)

    def clear_details(self):
        self.entryband.set_band('', '')
        self.entrybandedit.set_band('', '')
        self.entrysire.set_band('', '')
        self.entrysireedit.set_band('', '')
        self.entrydam.set_band('', '')
        self.entrydamedit.set_band('', '')

        self.combocolour.child.set_text('')
        self.combostrain.child.set_text('')
        self.comboloft.child.set_text('')
        self.combosex.set_active(0)
        self.combostatus.set_active(1)
        self.combostatus.emit('changed')

        self.set_default_image()

        for entry in self.get_objects_from_prefix("entry"):
            entry.set_text('')
        for text in self.get_objects_from_prefix("text"):
            text.get_buffer().set_text('')

    def start_edit(self, operation):
        self._operation = operation
        if operation == const.EDIT:
            logger.debug("Start editing pigeon '%s'", self.pigeon.get_pindex())
            self.entrybandedit.set_band(*self.entryband.get_band())
            self.entrysireedit.set_band(*self.entrysire.get_band())
            self.entrydamedit.set_band(*self.entrydam.get_band())
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
                                    '%s.png' % common.statusdic[status].lower())
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

    def _set_status_editable(self, value):
        self.entrydatedead.set_editable(value)
        self.textinfodead.set_editable(value)

        self.entrydatesold.set_editable(value)
        self.entrybuyersold.set_editable(value)
        self.textinfosold.set_editable(value)

        self.entrydatelost.set_editable(value)
        self.entrypointlost.set_editable(value)
        self.textinfolost.set_editable(value)

    def _fill_find_treeview(self, sex, band):
        """
        Fill the 'find'-treeview with pigeons of the wanted sex

        @param sex: sex of the pigeons
        @param band: bandand year tuple of the pigeon
        """

        ring, year = band
        self.liststorefind.clear()
        for pigeon in self.parser.pigeons.values():
            ring_new, year_new = pigeon.get_band()
            if str(sex) == pigeon.get_sex()and \
               ring != ring_new and year >= year_new:
                self.liststorefind.insert(0, [pigeon.get_pindex(),
                                              ring_new, year_new,
                                              pigeon.get_name()])
        self.liststorefind.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.liststorefind.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self.treeviewfind.get_selection().select_path(0)
        self.finddialog.show()

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
        self.database.insert_into_table(table, (data,))
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

        return dead, sold, lost

    def _insert_status_data(self, status, pindex, data=None):
        if data is None:
            dead, sold, lost = self._get_status_info()
        else:
            dead, sold, lost = data

        if status == const.DEAD:
            dead.insert(0, pindex)
            self.database.insert_into_table(self.database.DEAD, dead)
        elif status == const.SOLD:
            sold.insert(0, pindex)
            self.database.insert_into_table(self.database.SOLD, sold)
        elif status == const.LOST:
            lost.insert(0, pindex)
            self.database.insert_into_table(self.database.LOST, lost)

    def _update_pigeon_data(self, datalist):
        """
        Update the data when a pigeon is edited
        """

        pindex = self.pigeon.get_pindex()
        pindex_new = common.get_pindex_from_band(datalist[0], datalist[1])
        datalist.insert(0, pindex_new)
        datalist.append(pindex)

        # Update pindex in the results table
        if self.database.has_results(pindex):
            self.database.update_table(self.database.RESULTS,
                                       (pindex_new, pindex), 1, 1)
        # Update pindex in the medication table
        if self.database.has_medication(pindex):
            self.database.update_table(self.database.MED,
                                       (pindex_new, pindex), 2, 2)
        # Update the data in the pigeon table
        self.database.update_table(self.database.PIGEONS, datalist, 1, 1)
        # Remove the old thumbnail (if exists)
        image = datalist[10]
        prev_image = self.pigeon.get_image()
        if image != prev_image and prev_image:
            os.remove(thumbnail.get_path(prev_image))
        # Update the status or create a new record
        status = self.combostatus.get_active()
        old_status = self.pigeon.get_active()
        dead, sold, lost = self._get_status_info()
        if status != old_status:
            if old_status != const.ACTIVE:
                self.database.delete_from_table(common.statusdic[old_status],
                                                pindex)
            self._insert_status_data(status, pindex, (dead, sold, lost))
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

    def _add_pigeon_data(self, datalist):
        pindex = common.get_pindex_from_band(datalist[0], datalist[1])
        datalist.insert(0, pindex)

        # First we do some checks
        if self.database.has_pigeon(pindex):
            if self.parser.pigeons[pindex].show == 1:
                # The pigeon already exists, don't add it
                dialogs.MessageDialog(const.ERROR, messages.MSG_PIGEON_EXISTS,
                                      self.parent)
                raise PigeonAlreadyExists(pindex)
            else:
                # The pigeon exists, but doesn't show, ask to show again
                d = dialogs.MessageDialog(const.WARNING,
                                          messages.MSG_SHOW_PIGEON,
                                          self.parent)
                if d.yes:
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

