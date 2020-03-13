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


from gi.repository import Gtk

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.widgets import dateentry
from pigeonplanner.ui.widgets import comboboxes
from pigeonplanner.ui.messagedialog import ErrorDialog, QuestionDialog
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.database.models import Pigeon, Medication, Loft


(COL_OBJECT,
 COL_DATE,
 COL_DESCRIPTION) = range(3)

(COL_SEL_CAN_ACTIVE,
 COL_SEL_TOGGLED,
 COL_SEL_PIGEON,
 COL_SEL_BAND,
 COL_SEL_YEAR) = range(5)


class MedicationTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self):
        builder.GtkBuilder.__init__(self, "MedicationView.ui")
        basetab.BaseTab.__init__(self, "MedicationTab", _("Medication"), "icon_medication.png")

        self.pigeon = None
        self._mode = None
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)
        self.widgets.dialog.set_transient_for(self._parent)

    # Callbacks
    def on_dialog_delete(self, _widget, _event):
        self.widgets.dialog.hide()
        return True

    # noinspection PyMethodMayBeStatic
    def on_buttonhelp_clicked(self, _widget):
        common.open_help(15)

    def on_treeview_press(self, treeview, event):
        pthinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pthinfo is None:
            return
        if event.button == 3:
            entries = [
                (Gtk.STOCK_EDIT, self.on_buttonedit_clicked, None, None),
                (Gtk.STOCK_REMOVE, self.on_buttonremove_clicked, None, None)]

            utils.popup_menu(event, entries)

    def on_buttonadd_clicked(self, _widget):
        self._mode = enums.Action.add
        self._clear_dialog_widgets()
        self._fill_select_treeview()
        comboboxes.fill_combobox(self.widgets.comboloft, Loft.get_data_list())
        self.widgets.dialog.show()
        self.widgets.entrydate2.grab_focus()

    def on_buttonedit_clicked(self, _widget):
        self._mode = enums.Action.edit
        self._fill_select_treeview()
        comboboxes.fill_combobox(self.widgets.comboloft, Loft.get_data_list())
        med = self._get_selected_medication()
        self.widgets.entrydate2.set_text(med.date)
        self.widgets.entrydescription2.set_text(med.description)
        self.widgets.entryby2.set_text(med.doneby)
        self.widgets.entrymedication2.set_text(med.medication)
        self.widgets.entrydosage2.set_text(med.dosage)
        self.widgets.entrycomment2.set_text(med.comment)
        self.widgets.checkvaccination2.set_active(med.vaccination)
        for row in self.widgets.liststoreselect:
            if not row[COL_SEL_CAN_ACTIVE]:
                continue
            if row[COL_SEL_PIGEON] in med.pigeons:
                row[COL_SEL_TOGGLED] = True

        self.widgets.dialog.show()
        self.widgets.entrydate2.grab_focus()

    def on_buttonremove_clicked(self, _widget):
        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.liststore.get_path(rowiter)
        med = model[rowiter][COL_OBJECT]

        primary_text = _("Removing the selected medication entry")
        secondary_text = _("Are you sure?")
        check_multiple = Gtk.CheckButton(_("Remove this entry for all pigeons?"))
        dialog = QuestionDialog((primary_text, secondary_text, ""), self._parent)
        if med.pigeons.count() > 1:
            message_area = dialog.get_message_area()
            message_area.pack_start(check_multiple, False, False, 0)
            check_multiple.show()
        if dialog.run():
            if check_multiple.get_active():
                med.pigeons.clear()
                med.delete_instance()
            else:
                med.pigeons.remove(self.pigeon)
                # Delete this medication entry completely when it has no pigeons
                if med.pigeons.count() == 0:
                    med.delete_instance()
            self.widgets.liststore.remove(rowiter)
            self.widgets.selection.select_path(path)

    def on_buttonsave_clicked(self, _widget):
        try:
            data = self._get_entry_data()
        except dateentry.InvalidDateInput as exc:
            ErrorDialog(exc.format_error(), self._parent)
            return
        pigeons_toggled = [row[COL_SEL_PIGEON] for row in self.widgets.liststoreselect if row[COL_SEL_TOGGLED]]
        if self._mode == enums.Action.add:
            record = Medication.create(**data)
            record.pigeons.add(pigeons_toggled)
            rowiter = self.widgets.liststore.insert(0, [record, data["date"], data["description"]])
            self.widgets.selection.select_iter(rowiter)
            path = self.widgets.liststore.get_path(rowiter)
            self.widgets.treeview.scroll_to_cell(path)
        else:
            med = self._get_selected_medication()
            # Replace all pigeons with the new selection
            med.pigeons.add(pigeons_toggled, clear_existing=True)
            med.date = data["date"]
            med.description = data["description"]
            med.doneby = data["doneby"]
            med.medication = data["medication"]
            med.dosage = data["dosage"]
            med.comment = data["comment"]
            med.vaccination = data["vaccination"]
            med.save()
            model, rowiter = self.widgets.selection.get_selected()
            self.widgets.liststore.set(rowiter, COL_DATE, data["date"], COL_DESCRIPTION, data["description"])
            self.widgets.selection.emit("changed")
        self.widgets.dialog.hide()

    def on_buttoncancel_clicked(self, _widget):
        self.widgets.dialog.hide()

    def on_checkloft_toggled(self, widget):
        if widget.get_active():
            self._select_loft()
        else:
            for row in self.widgets.liststoreselect:
                if not row[COL_SEL_CAN_ACTIVE]:
                    continue
                row[COL_SEL_TOGGLED] = False

    def on_comboloft_changed(self, _widget):
        if self.widgets.checkloft.get_active():
            self._select_loft()

    def on_celltoggle_toggled(self, _cell, path):
        self.widgets.liststoreselect[path][COL_SEL_TOGGLED] =\
                            not self.widgets.liststoreselect[path][COL_SEL_TOGGLED]

    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()
        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        if rowiter is not None:
            utils.set_multiple_sensitive(widgets, True)
        else:
            utils.set_multiple_sensitive(widgets, False)

            for entry in self.get_objects_from_prefix("entry"):
                entry.set_text("")
            self.widgets.entrydate.set_text("")
            self.widgets.checkvaccination.set_active(False)
            return

        med = model[rowiter][COL_OBJECT]
        self.widgets.entrydate.set_text(med.date)
        self.widgets.entrydescription.set_text(med.description)
        self.widgets.entryby.set_text(med.doneby)
        self.widgets.entrymedication.set_text(med.medication)
        self.widgets.entrydosage.set_text(med.dosage)
        self.widgets.entrycomment.set_text(med.comment)
        self.widgets.checkvaccination.set_active(med.vaccination)

    # Public methods
    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        self.widgets.liststore.clear()
        for med in pigeon.medication:
            self.widgets.liststore.insert(0, [med, str(med.date), med.description])
        self.widgets.liststore.set_sort_column_id(COL_DATE, Gtk.SortType.ASCENDING)

    def clear_pigeon(self):
        self.widgets.liststore.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    # Internal methods
    def _fill_select_treeview(self):
        self.widgets.liststoreselect.clear()
        for pigeon in Pigeon.select().where(Pigeon.visible == True):
            active = not self.pigeon == pigeon
            self.widgets.liststoreselect.insert(0, [active, not active, pigeon, pigeon.band, pigeon.band_year])
        self.widgets.liststoreselect.set_sort_column_id(COL_SEL_BAND, Gtk.SortType.ASCENDING)
        self.widgets.liststoreselect.set_sort_column_id(COL_SEL_YEAR, Gtk.SortType.ASCENDING)

    def _select_loft(self):
        loft = self.widgets.comboloft.get_active_text()
        for row in self.widgets.liststoreselect:
            if not row[COL_SEL_CAN_ACTIVE]:
                continue
            pigeon = row[COL_SEL_PIGEON]
            row[COL_SEL_TOGGLED] = pigeon.loft == loft

    def _clear_dialog_widgets(self):
        for entry in self.get_objects_from_prefix("entry"):
            entry.set_text("")
        self.widgets.entrydate2.set_text(common.get_date())
        self.widgets.checkvaccination2.set_active(False)

    def _get_selected_medication(self):
        model, rowiter = self.widgets.selection.get_selected()
        return model[rowiter][COL_OBJECT]

    def _get_entry_data(self):
        return {"date": self.widgets.entrydate2.get_text(),
                "description": self.widgets.entrydescription2.get_text(),
                "doneby": self.widgets.entryby2.get_text(),
                "medication": self.widgets.entrymedication2.get_text(),
                "dosage": self.widgets.entrydosage2.get_text(),
                "comment": self.widgets.entrycomment2.get_text(),
                "vaccination": self.widgets.checkvaccination2.get_active()}
