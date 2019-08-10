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

from pigeonplanner import messages
from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui import component
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.ui.detailsview import DetailsDialog
from pigeonplanner.ui.messagedialog import ErrorDialog
from pigeonplanner.core import enums
from pigeonplanner.core import common
from pigeonplanner.core import errors
from pigeonplanner.core import pigeon as corepigeon
from pigeonplanner.database.models import Pigeon, Breeding


(COL_OBJ,
 COL_MATE,
 COL_DATA) = range(3)


class BreedingTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self):
        builder.GtkBuilder.__init__(self, "BreedingView.ui")
        basetab.BaseTab.__init__(self, "BreedingTab", _("Breeding"), "icon_breeding.png")

        self.maintreeview = component.get("Treeview")
        self.widgets.selection = self.widgets.treeview.get_selection()
        self.widgets.selection.connect("changed", self.on_selection_changed)
        self.widgets.editdialog.set_transient_for(self._parent)

    # Tab
    def on_selection_changed(self, selection):
        model, rowiter = selection.get_selected()

        widgets = [self.widgets.buttonremove, self.widgets.buttonedit]
        utils.set_multiple_sensitive(widgets, not rowiter is None)

        if rowiter is None:
            defaults = Breeding.get_fields_with_defaults()
            self.widgets.datelaid1.set_text(defaults["laid1"])
            self.widgets.datehatched1.set_text(defaults["hatched1"])
            self.widgets.bandentry1.set_pigeon(defaults["child1"])
            self.widgets.successcheck1.set_active(defaults["success1"])
            self.widgets.datelaid2.set_text(defaults["laid2"])
            self.widgets.datehatched2.set_text(defaults["hatched2"])
            self.widgets.bandentry2.set_pigeon(defaults["child2"])
            self.widgets.successcheck2.set_active(defaults["success2"])
            self.widgets.entryclutch.set_text(defaults["clutch"])
            self.widgets.entrybox.set_text(defaults["box"])
            self.widgets.textviewcomment.get_buffer().set_text(defaults["comment"])

            p1 = not self.widgets.bandentry1.is_empty()
            p2 = not self.widgets.bandentry2.is_empty()
            self.widgets.buttoninfo1.set_sensitive(p1)
            self.widgets.buttongoto1.set_sensitive(p1)
            self.widgets.buttoninfo2.set_sensitive(p2)
            self.widgets.buttongoto2.set_sensitive(p2)
            return

        # Never select parent rows. Expand them and select first child row.
        if rowiter is not None and self.widgets.treestore.iter_depth(rowiter) == 0:
            path = self.widgets.treestore.get_path(rowiter)
            self.widgets.treeview.expand_row(path, False)
            rowiter = self.widgets.treestore.iter_children(rowiter)
            selection.select_iter(rowiter)

        record = model[rowiter][COL_OBJ]
        self.widgets.datelaid1.set_text(record.laid1)
        self.widgets.datehatched1.set_text(record.hatched1)
        self.widgets.bandentry1.set_pigeon(record.child1)
        self.widgets.successcheck1.set_active(record.success1)
        self.widgets.datelaid2.set_text(record.laid2)
        self.widgets.datehatched2.set_text(record.hatched2)
        self.widgets.bandentry2.set_pigeon(record.child2)
        self.widgets.successcheck2.set_active(record.success2)
        self.widgets.entryclutch.set_text(record.clutch)
        self.widgets.entrybox.set_text(record.box)
        self.widgets.textviewcomment.get_buffer().set_text(record.comment)
        self.widgets.buttoninfo1.set_sensitive(record.child1 is not None)
        self.widgets.buttongoto1.set_sensitive(record.child1 is not None and record.child1.visible)
        self.widgets.buttoninfo2.set_sensitive(record.child2 is not None)
        self.widgets.buttongoto2.set_sensitive(record.child2 is not None and record.child2.visible)

    def on_buttonadd_clicked(self, widget):
        self._mode = enums.Action.add
        self._set_dialog_fields()
        self.widgets.editdialog.show()

    def on_buttonedit_clicked(self, widget):
        self._mode = enums.Action.edit
        model, rowiter = self.widgets.selection.get_selected()
        self._set_dialog_fields(model[rowiter][COL_OBJ], model[rowiter][COL_MATE])
        self.widgets.editdialog.show()

    def on_buttonremove_clicked(self, widget):
        model, rowiter = self.widgets.selection.get_selected()
        path = self.widgets.treestore.get_path(rowiter)
        obj = model.get_value(rowiter, COL_OBJ)
        obj.delete_instance()
        self._remove_record(rowiter)
        self.widgets.selection.select_path(path)

    def on_buttoninfo1_clicked(self, widget):
        band_tuple = self.widgets.bandentry1.get_band()
        pigeon = Pigeon.get_for_band(band_tuple)
        DetailsDialog(pigeon, self._parent)

    def on_buttongoto1_clicked(self, widget):
        band_tuple = self.widgets.bandentry1.get_band()
        pigeon = Pigeon.get_for_band(band_tuple)
        self.maintreeview.select_pigeon(None, pigeon)

    def on_buttoninfo2_clicked(self, widget):
        band_tuple = self.widgets.bandentry2.get_band()
        pigeon = Pigeon.get_for_band(band_tuple)
        DetailsDialog(pigeon, self._parent)

    def on_buttongoto2_clicked(self, widget):
        band_tuple = self.widgets.bandentry2.get_band()
        pigeon = Pigeon.get_for_band(band_tuple)
        self.maintreeview.select_pigeon(None, pigeon)

    # Edit dialog
    def on_editdialog_delete_event(self, widget, event):
        self.widgets.editdialog.hide()
        return True

    def on_buttonhelp_clicked(self, widget):
        common.open_help(14)

    def on_buttoncancel_clicked(self, widget):
        self.widgets.editdialog.hide()

    def on_buttonsave_clicked(self, widget):
        # Get and check bands
        try:
            band_tuple_mate = self.widgets.bandmateedit.get_band()
            band_tuple1 = self.widgets.bandentryedit1.get_band()
            band_tuple2 = self.widgets.bandentryedit2.get_band()
        except errors.InvalidInputError as msg:
            ErrorDialog(msg.value, self.widgets.editdialog)
            return
        # Get and check dates
        try:
            date = self.widgets.dateedit.get_text()
            laid1 = self.widgets.datelaidedit1.get_text()
            hatched1 = self.widgets.datehatchededit1.get_text()
            laid2 = self.widgets.datelaidedit2.get_text()
            hatched2 = self.widgets.datehatchededit2.get_text()
        except errors.InvalidInputError as msg:
            ErrorDialog(msg.value, self.widgets.editdialog)
            return

        try:
            mate = Pigeon.get_for_band(band_tuple_mate)
        except Pigeon.DoesNotExist:
            ErrorDialog(messages.MSG_INVALID_MATE, self.widgets.editdialog)
            return
        if self.pigeon.is_cock():
            sire = self.pigeon
            dam = mate
        else:
            sire = mate
            dam = self.pigeon
        child1 = self._add_child_pigeon(band_tuple1, sire, dam,
                                        self.widgets.listcheckedit1.get_active())
        child2 = self._add_child_pigeon(band_tuple2, sire, dam,
                                        self.widgets.listcheckedit2.get_active())

        textbuffer = self.widgets.textviewcommentedit.get_buffer()
        data = {"sire": sire, "dam": dam, "date": date,
                "laid1": laid1, "hatched1": hatched1, "child1": child1,
                "success1": self.widgets.successcheckedit1.get_active(),
                "laid2": laid2, "hatched2": hatched2, "child2": child2,
                "success2": self.widgets.successcheckedit2.get_active(),
                "clutch": self.widgets.entryclutchedit.get_text(),
                "box": self.widgets.entryboxedit.get_text(),
                "comment": textbuffer.get_text(*textbuffer.get_bounds(), include_hidden_chars=True)}

        # Update when editing record
        if self._mode == enums.Action.edit:
            model, rowiter = self.widgets.selection.get_selected()
            old_record = self.widgets.treestore.get_value(rowiter, COL_OBJ)
            record = old_record.update_and_return(**data)
            parent = self._get_or_create_parent_record(mate)
            if not self.widgets.treestore.is_ancestor(parent, rowiter):
                # It is not possible to move a row to another parent.
                self._remove_record(rowiter)
                rowiter = self.widgets.treestore.append(parent, [record, mate, date])
            else:
                self.widgets.treestore.set(rowiter, COL_OBJ, record, COL_DATA, date)

            self.widgets.selection.emit("changed")
        # Insert when adding record
        elif self._mode == enums.Action.add:
            record = Breeding.create(**data)
            parent = self._get_or_create_parent_record(mate)
            rowiter = self.widgets.treestore.append(parent, [record, mate, date])

        parent_path = self.widgets.treestore.get_path(parent)
        self.widgets.treeview.expand_row(parent_path, False)
        self.widgets.selection.select_iter(rowiter)
        path = self.widgets.treestore.get_path(rowiter)
        self.widgets.treeview.scroll_to_cell(path)
        self.widgets.editdialog.hide()

    def on_bandmateedit_search_clicked(self, widget):
        sex = enums.Sex.cock if self.pigeon.is_hen() else enums.Sex.hen
        return None, sex, None

    def on_successcheckedit1_toggled(self, widget):
        self.widgets.vboxpigeonedit1.set_sensitive(widget.get_active())

    def on_successcheckedit2_toggled(self, widget):
        self.widgets.vboxpigeonedit2.set_sensitive(widget.get_active())

    # Public methods
    def set_pigeon(self, pigeon):
        self.pigeon = pigeon

        parent = None
        last = None
        self.widgets.treestore.clear()
        this, mate = (Breeding.sire, Breeding.dam) if pigeon.is_cock() else (Breeding.dam, Breeding.sire)
        query = (Breeding.select()
                 .where(this == pigeon)
                 .order_by(mate, Breeding.date))
        for record in query:
            mate_obj = getattr(record, mate.name)
            if parent is None or mate_obj.id != last:
                parent = self._add_parent_record(mate_obj)
            self.widgets.treestore.append(parent, [record, mate_obj, str(record.date)])
            last = mate_obj.id
        self.widgets.treestore.set_sort_column_id(COL_DATA, Gtk.SortType.ASCENDING)

    def clear_pigeon(self):
        self.widgets.treestore.clear()

    def get_pigeon_state_widgets(self):
        return [self.widgets.buttonadd]

    # Private methods
    def _set_dialog_fields(self, obj=None, mate=None):
        if obj is None:
            data = Breeding.get_fields_with_defaults()
            data["mate"] = None
        else:
            data = {
                "date": obj.date,
                "clutch": obj.clutch,
                "box": obj.box,
                "comment": obj.comment,
                "mate": mate,
                "laid1": obj.laid1,
                "hatched1": obj.hatched1,
                "child1": obj.child1,
                "success1": obj.success1,
                "laid2": obj.laid2,
                "hatched2": obj.hatched2,
                "child2": obj.child2,
                "success2": obj.success2
            }

        self.widgets.dateedit.set_text(data["date"])
        self.widgets.bandmateedit.set_pigeon(data["mate"])
        self.widgets.entryclutchedit.set_text(data["clutch"])
        self.widgets.entryboxedit.set_text(data["box"])
        self.widgets.textviewcommentedit.get_buffer().set_text(data["comment"])

        self.widgets.datelaidedit1.set_text(data["laid1"])
        self.widgets.datehatchededit1.set_text(data["hatched1"])
        self.widgets.bandentryedit1.set_pigeon(data["child1"])
        self.widgets.successcheckedit1.set_active(data["success1"])
        self.widgets.datelaidedit2.set_text(data["laid2"])
        self.widgets.datehatchededit2.set_text(data["hatched2"])
        self.widgets.bandentryedit2.set_pigeon(data["child2"])
        self.widgets.successcheckedit2.set_active(data["success2"])

        self.widgets.listcheckedit1.set_active(False)
        self.widgets.listcheckedit2.set_active(False)

    def _add_child_pigeon(self, band_tuple, sire, dam, visible):
        pigeon = corepigeon.get_or_create_pigeon(band_tuple, enums.Sex.youngbird, visible)
        if pigeon is None:
            return None

        pigeon.sire = sire
        pigeon.dam = dam
        if visible:
            # Only go from invisible to visible, not the other way around
            pigeon.visible = visible
        pigeon.save()

        if pigeon.visible and not self.maintreeview.has_pigeon(pigeon):
            self.maintreeview.add_pigeon(pigeon, False)

        return pigeon

    def _add_parent_record(self, pigeon):
        rowiter = self.widgets.treestore.append(None,
            [None, pigeon, pigeon.band])
        return rowiter

    def _get_or_create_parent_record(self, pigeon):
        for row in self.widgets.treestore:
            if row[COL_MATE] == pigeon:
                return row.iter
        return self._add_parent_record(pigeon)

    def _remove_record(self, rowiter):
        parent = self.widgets.treestore.iter_parent(rowiter)
        self.widgets.treestore.remove(rowiter)
        if not self.widgets.treestore.iter_has_child(parent):
            self.widgets.treestore.remove(parent)
