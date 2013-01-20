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
from ui import utils
from ui import dialogs
from ui.tabs import basetab
from ui.widgets import comboboxes
from ui.messagedialog import ErrorDialog
from translation import gettext as _


class MedicationTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self, parent, database, parser, main):
        basetab.BaseTab.__init__(self, _("Medication"), "icon_medication.png")
        builder.GtkBuilder.__init__(self, "MedicationView.ui")

        self.parent = parent
        self.database = database
        self.parser = parser
        self.main = main
        self._mode = None
        self._expanded = False
        self._selection = self.treeview.get_selection()
        self._selection.connect('changed', self.on_selection_changed)
        self._root.unparent()
        self.dialog.set_transient_for(parent)

    # Callbacks
    def on_dialog_delete(self, widget, event):
        self.dialog.hide()
        return True

    def on_buttonhelp_clicked(self, widget):
        common.open_help(15)

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        if event.button == 3:
            entries = [
                (gtk.STOCK_EDIT, self.on_buttonedit_clicked, None),
                (gtk.STOCK_REMOVE, self.on_buttonremove_clicked, None)]

            utils.popup_menu(event, entries)

    def on_treeviewselect_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None: return
        path, col, cellx, celly = pthinfo
        pindex = treeview.get_model()[path][2]
        if event.button == 3:
            entries = [
                (gtk.STOCK_INFO, self.main.show_pigeon_details, (pindex,))
                ]

            utils.popup_menu(event, entries)

    def on_buttonadd_clicked(self, widget):
        self._mode = const.ADD
        self._clear_dialog_widgets()
        self._fill_select_treeview()
        comboboxes.fill_combobox(self.comboloft,
                        self.database.select_from_table(self.database.LOFTS))
        self.dialog.show()
        self.entrydate2.grab_focus()

    def on_buttonedit_clicked(self, widget):
        self._mode = const.EDIT
        self._fill_select_treeview()
        comboboxes.fill_combobox(self.comboloft,
                        self.database.select_from_table(self.database.LOFTS))
        med = self.database.get_medication_from_id(self._get_selected_medid())
        self.entrydate2.set_text(med[3])
        self.entrydescription2.set_text(med[4])
        self.entryby2.set_text(med[5])
        self.entrymedication2.set_text(med[6])
        self.entrydosage2.set_text(med[7])
        self.entrycomment2.set_text(med[8])
        self.checkvaccination2.set_active(med[9])
        for row in self.liststoreselect:
            if not row[0]: continue
            if row[2] in self.database.get_pigeons_from_medid(med[1]):
                row[1] = True

        self.dialog.show()
        self.entrydate2.grab_focus()

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self._selection.get_selected()
        path = self.liststore.get_path(rowiter)
        medid = model[rowiter][0]

        multiple = self.database.count_medication_entries(medid) > 1
        dialog = dialogs.MedicationRemoveDialog(self.parent, multiple)
        dialog.check.set_active(multiple)
        resp = dialog.run()
        if resp == gtk.RESPONSE_NO or resp == gtk.RESPONSE_DELETE_EVENT:
            dialog.destroy()
            return

        if dialog.check.get_active():
            self.database.delete_from_table(self.database.MED, medid)
        else:
            self.database.delete_medication_from_id_pindex(medid, self.pindex)
        dialog.destroy()

        self.liststore.remove(rowiter)
        self._selection.select_path(path)

    def on_buttonsave_clicked(self, widget):
        try:
            data = self._get_entry_data()
        except errors.InvalidInputError, msg:
            ErrorDialog(msg.value, self.parent)
            return
        pigeons = [row[2] for row in self.liststoreselect if row[1]]
        if self._mode == const.ADD:
            medid = data[0] + common.get_random_number(10)
            for pindex in pigeons:
                self.database.insert_into_table(self.database.MED,
                                                (medid, pindex, ) + data)
                # Only fill med treeview on current pigeon
                if not pindex == self.pindex: continue
                rowiter = self.liststore.insert(0, [medid, data[0], data[1]])
                self._selection.select_iter(rowiter)
                path = self.liststore.get_path(rowiter)
                self.treeview.scroll_to_cell(path)
        else:
            medid = self._get_selected_medid()
            pigeons_current = self.database.get_pigeons_from_medid(medid)
            for pindex in [pindex for pindex in pigeons
                           if pindex not in pigeons_current]:
                self.database.insert_into_table(self.database.MED,
                                                (medid, pindex, ) + data)
            for pindex in [p for p in pigeons_current if p not in pigeons]:
                self.database.delete_medication_from_id_pindex(medid, pindex)
            data += (medid, )
            self.database.update_table(self.database.MED, data, 3, 1)
            model, rowiter = self._selection.get_selected()
            self.liststore.set(rowiter, 1, data[0], 2, data[1])
            self._selection.emit('changed')
        self.dialog.hide()

    def on_buttoncancel_clicked(self, widget):
        self.dialog.hide()

    def on_buttonexpand_clicked(self, widget):
        self._set_pigeon_list(not self._expanded)

    def on_checkloft_toggled(self, widget):
        if widget.get_active():
            self._select_loft()
        else:
            for row in self.liststoreselect:
                if not row[0]: continue
                row[1] = False

    def on_comboloft_changed(self, widget):
        if self.checkloft.get_active():
            self._select_loft()

    def on_celltoggle_toggled(self, cell, path):
        self.liststoreselect[path][1] = not self.liststoreselect[path][1]

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.buttonremove, self.buttonedit]
        if rowiter is not None:
            utils.set_multiple_sensitive(widgets, True)
        else:
            utils.set_multiple_sensitive(widgets, False)

            for entry in self.get_objects_from_prefix('entry'):
                entry.set_text('')
            self.entrydate.set_text('')
            self.checkvaccination.set_active(False)
            return

        data = self.database.get_medication_from_id(model[rowiter][0])
        self.entrydate.set_text(data[3])
        self.entrydescription.set_text(data[4])
        self.entryby.set_text(data[5])
        self.entrymedication.set_text(data[6])
        self.entrydosage.set_text(data[7])
        self.entrycomment.set_text(data[8])
        self.checkvaccination.set_active(data[9])

    # Public methods
    def set_pigeon(self, pigeon):
        self.pindex = pigeon.get_pindex()
        self.liststore.clear()
        for med in self.database.get_pigeon_medication(self.pindex):
            self.liststore.insert(0, [med[1], med[3], med[4]])
        self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def clear_pigeon(self):
        self.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.buttonadd]

    # Internal methods
    def _fill_select_treeview(self):
        self.liststoreselect.clear()
        for pindex, pigeon in self.parser.pigeons.items():
            if not pigeon.get_visible():
                continue
            active = not self.pindex == pindex
            ring, year = pigeon.get_band()
            self.liststoreselect.insert(0, [active, not active, pindex,
                                            ring, year])
        self.liststoreselect.set_sort_column_id(3, gtk.SORT_ASCENDING)
        self.liststoreselect.set_sort_column_id(4, gtk.SORT_ASCENDING)

    def _set_pigeon_list(self, value):
        self._expanded = value
        utils.set_multiple_visible([self.seperator, self.vboxexpand], value)
        img = gtk.STOCK_GO_BACK if value else gtk.STOCK_GO_FORWARD
        self.imageexpand.set_from_stock(img, gtk.ICON_SIZE_BUTTON)

    def _select_loft(self):
        loft = self.comboloft.get_active_text()
        for row in self.liststoreselect:
            if not row[0]: continue
            pigeon = self.parser.get_pigeon(row[2])
            row[1] = pigeon.get_loft() == loft

    def _clear_dialog_widgets(self):
        for entry in self.get_objects_from_prefix('entry'):
            entry.set_text('')
        self.entrydate2.set_text(common.get_date())
        self.checkvaccination2.set_active(False)

    def _get_selected_medid(self):
        model, rowiter = self._selection.get_selected()
        return model[rowiter][0]

    def _get_entry_data(self):
        return (
                self.entrydate2.get_text(),
                self.entrydescription2.get_text(),
                self.entryby2.get_text(),
                self.entrymedication2.get_text(),
                self.entrydosage2.get_text(),
                self.entrycomment2.get_text(),
                int(self.checkvaccination2.get_active())
                )

