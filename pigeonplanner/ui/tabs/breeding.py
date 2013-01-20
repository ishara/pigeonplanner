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

import const
import common
import errors
import builder
import database
from ui import utils
from ui.tabs import basetab
from ui.widgets import checkbutton
from ui.dialogs import PigeonListDialog
from ui.detailsview import DetailsDialog
from ui.messagedialog import ErrorDialog
from translation import gettext as _


class BreedingTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, mainwindow, database, parser):
        basetab.BaseTab.__init__(self, _("Breeding"), "icon_breeding.png")
        builder.GtkBuilder.__init__(self, "BreedingView.ui")
        self._root.unparent()

        self.mainwindow = mainwindow
        self.database = database
        self.parser = parser
        self.maintreeview = mainwindow.get_treeview()
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)
        self.editdialog.set_transient_for(self.mainwindow)

    ## Tab
    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.buttonremove, self.buttonedit]
        utils.set_multiple_sensitive(widgets, not rowiter is None)
        try:
            (key, sire, dam, date, laid1, hatched1, pindex1, success1,
             laid2, hatched2, pindex2, success2, clutch, 
             box, comment) = self.database.get_breeding_from_id(model[rowiter][0])
        except TypeError:
            (laid1, hatched1, pindex1, success1,
             laid2, hatched2, pindex2, success2,
             clutch, box, comment) = '', '', '', 0, '', '', '', 0, '', '', ''
        self.datelaid1.set_text(laid1)
        self.datehatched1.set_text(hatched1)
        self.bandentry1.set_pindex(pindex1)
        self.successcheck1.set_active(success1)
        self.datelaid2.set_text(laid2)
        self.datehatched2.set_text(hatched2)
        self.bandentry2.set_pindex(pindex2)
        self.successcheck2.set_active(success2)
        self.entryclutch.set_text(clutch)
        self.entrybox.set_text(box)
        self.textviewcomment.get_buffer().set_text(comment)

        self.buttoninfo1.set_sensitive(success1)
        self.buttongoto1.set_sensitive(success1)
        self.buttoninfo2.set_sensitive(success2)
        self.buttongoto2.set_sensitive(success2)

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        self._set_dialog_fields()
        self.editdialog.show()

    def on_buttonedit_clicked(self, widget):
        self._mode = const.EDIT
        model, rowiter = self._selection.get_selected()
        self._set_dialog_fields(model[rowiter][0],
                        common.get_pindex_from_band_string(model[rowiter][2]))
        self.editdialog.show()

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        rowid = model.get_value(rowiter, 0)
        self.database.delete_from_table(self.database.BREEDING, rowid, 0)
        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def on_buttoninfo1_clicked(self, widget):
        pigeon = self.parser.get_pigeon(self.bandentry1.get_pindex())
        DetailsDialog(self.database, self.parser, pigeon, self.mainwindow)

    def on_buttongoto1_clicked(self, widget):
        pindex = self.bandentry1.get_pindex()
        self.maintreeview.select_pigeon(None, pindex)

    def on_buttoninfo2_clicked(self, widget):
        pigeon = self.parser.get_pigeon(self.bandentry2.get_pindex())
        DetailsDialog(self.database, self.parser, pigeon, self.mainwindow)

    def on_buttongoto2_clicked(self, widget):
        pindex = self.bandentry2.get_pindex()
        self.maintreeview.select_pigeon(None, pindex)

    ## Edit dialog
    def on_editdialog_delete_event(self, widget, event):
        self.editdialog.hide()
        return True

    def on_buttonhelp_clicked(self, widget):
        common.open_help(14)

    def on_buttoncancel_clicked(self, widget):
        self.editdialog.hide()

    def on_buttonsave_clicked(self, widget):
        # Get and check bands
        try:
            mate = self.bandmateedit.get_pindex()
            pindex1 = self.bandentryedit1.get_pindex()
            pindex2 = self.bandentryedit2.get_pindex()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.editdialog)
            return
        # Get and check dates
        try:
            date = self.dateedit.get_text()
            laid1 = self.datelaidedit1.get_text()
            hatched1 = self.datehatchededit1.get_text()
            laid2 = self.datelaidedit2.get_text()
            hatched2 = self.datehatchededit2.get_text()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.editdialog)
            return

        if self.pigeon.is_cock():
            sire = self.pigeon.get_pindex()
            dam = mate
        else:
            sire = mate
            dam = self.pigeon.get_pindex()
        textbuffer = self.textviewcommentedit.get_buffer()
        data = [sire, dam, date,
                laid1, hatched1, pindex1,
                int(self.successcheckedit1.get_active()),
                laid2, hatched2, pindex2,
                int(self.successcheckedit2.get_active()),
                self.entryclutchedit.get_text(),
                self.entryboxedit.get_text(),
                textbuffer.get_text(*textbuffer.get_bounds())]

        # Add the child pigeons if needed
        self._add_child_pigeon(pindex1, sire, dam, self.listcheckedit1.get_active())
        self._add_child_pigeon(pindex2, sire, dam, self.listcheckedit2.get_active())

        # Update when editing record
        if self._mode == const.EDIT:
            model, rowiter = self._selection.get_selected()
            data.append(self.liststore.get_value(rowiter, 0))
            self.database.update_table(self.database.BREEDING, data, 1, 0)
            self.liststore.set(rowiter, 1, date, 2, self._format_mate(mate))
            self._selection.emit('changed')
        # Insert when adding record
        elif self._mode == const.ADD:
            rowid = self.database.insert_into_table(self.database.BREEDING, data)
            rowiter = self.liststore.insert(0, [rowid, date,
                                                self._format_mate(mate)])
            self._selection.select_iter(rowiter)
            path = self.liststore.get_path(rowiter)
            self.treeview.scroll_to_cell(path)
        self.editdialog.hide()

    def on_buttonsearchmate_clicked(self, widget):
        sex = const.SIRE if self.pigeon.is_hen() else const.DAM
        dialog = PigeonListDialog(self.editdialog)
        dialog.fill_treeview(self.parser, sex=sex)
        response = dialog.run()
        if response == gtk.RESPONSE_APPLY:
            pigeon = dialog.get_selected()
            self.bandmateedit.set_pindex(pigeon.get_pindex())
        dialog.destroy()

    def on_successcheckedit1_toggled(self, widget):
        self.vboxpigeonedit1.set_sensitive(widget.get_active())

    def on_successcheckedit2_toggled(self, widget):
        self.vboxpigeonedit2.set_sensitive(widget.get_active())

    # Public methods
    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        matecol = 1 if pigeon.is_hen() else 2
        self.liststore.clear()
        for data in self.database.get_pigeon_breeding(pigeon.pindex):
            self.liststore.insert(0, [data[0], data[3],
                                      self._format_mate(data[matecol])])
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def clear_pigeon(self):
        self.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.buttonadd]

    # Private methods
    def _set_dialog_fields(self, key=None, mate=''):
        if key is not None:
            (key, sire, dam, date, laid1, hatched1, pindex1, success1,
             laid2, hatched2, pindex2, success2, clutch, 
             box, comment) = self.database.get_breeding_from_id(key)
        else:
            (sire, dam, date, clutch, box, comment,
             laid1, hatched1, pindex1, success1,
             laid2, hatched2, pindex2, success2) = (
                        '', '', '', '', '', '', '', '', '', 0, '', '', '', 0)

        self.dateedit.set_text(date)
        self.bandmateedit.set_pindex(mate)
        self.entryclutchedit.set_text(clutch)
        self.entryboxedit.set_text(box)
        self.textviewcommentedit.get_buffer().set_text(comment)

        self.datelaidedit1.set_text(laid1)
        self.datehatchededit1.set_text(hatched1)
        self.bandentryedit1.set_pindex(pindex1)
        self.successcheckedit1.set_active(success1)
        self.datelaidedit2.set_text(laid2)
        self.datehatchededit2.set_text(hatched2)
        self.bandentryedit2.set_pindex(pindex2)
        self.successcheckedit2.set_active(success2)

    def _format_mate(self, pindex):
        pigeon = self.parser.get_pigeon(pindex)
        try:
            return pigeon.get_band_string()
        except AttributeError:
            # This pigeon was removed from the database
            return "%s / %s" % common.get_band_from_pindex(pindex)

    def _add_child_pigeon(self, pindex, sire, dam, active):
        pigeon = None
        try:
            pigeon = self.parser.add_empty_pigeon(pindex, const.YOUNG,
                                                  active, sire, dam)
        except ValueError:
            # Empty bandnumber
            return
        except database.InvalidValueError:
            # Pigeon does exist, update parents
            pigeon = self.parser.get_pigeon(pindex)

            s, sy = common.get_band_from_pindex(sire)
            d, dy = common.get_band_from_pindex(dam)
            pigeon.sire = s
            pigeon.yearsire = sy
            pigeon.dam = d
            pigeon.yeardam = dy
            self.database.update_table(self.database.PIGEONS,
                                       (s, sy, d, dy, pigeon.get_pindex()), 12, 1)
            if active:
                # Pigeon isn't visible, but user checked the "add to list" option
                pigeon.show = 1
                self.database.update_table(self.database.PIGEONS,
                                           (1, pigeon.get_pindex()), 5, 1)

        if pigeon.get_visible() and not self.maintreeview.has_pigeon(pigeon):
            self.maintreeview.add_pigeon(pigeon, False)

