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

from pigeonplanner.ui import builder
from pigeonplanner.database import session
from pigeonplanner.database.models import Pigeon, Racepoint

logger = logging.getLogger(__name__)


class PigeonEmptyYearChecker:
    def __init__(self):
        self.description = _("Check for pigeons with an empty value as year.")
        self.action = _("Delete pigeon.")

    def repair(self):  # noqa
        query = Pigeon.delete().where(Pigeon.band_year == "")
        num_repaired = query.execute()
        logger.debug("Database check: PigeonEmptyYearChecker deleted %s row(s)", num_repaired)
        return _("Deleted %s object(s)") % num_repaired


class RacepointUnitChecker:
    def __init__(self):
        self.description = _("Check for racepoints with an invalid unit value.")
        self.action = _("Reset unit value to the default.")

    def repair(self):  # noqa
        query = Racepoint.update(unit=0).where(Racepoint.unit.cast("text") == "")
        num_repaired = query.execute()
        logger.debug("Database check: RacepointUnitChecker updated %s row(s)", num_repaired)
        return _("Updated %s object(s)") % num_repaired


checkers = [
    PigeonEmptyYearChecker(),
    RacepointUnitChecker(),
]


class DatabaseRepairDialog(builder.GtkBuilder):
    (COL_CHECKER,
     COL_TOGGLE,
     COL_DESCRIPTION,
     COL_ACTION,
     COL_RESULT) = range(5)

    def __init__(self, dbobj, parent=None):
        builder.GtkBuilder.__init__(self, "DatabaseRepairDialog.ui")
        self._dbobj = dbobj

        for checker in checkers:
            self.widgets.liststore.append([checker, True, checker.description, checker.action, ""])

        self.widgets.dialog.set_transient_for(parent)
        self.widgets.dialog.show_all()

    def on_dialog_delete_event(self, _widget, _event):  # noqa
        return False

    def on_button_close_clicked(self, _widget):
        self.widgets.dialog.destroy()

    def on_cell_toggle_toggled(self, _cell, path):
        self.widgets.liststore[path][self.COL_TOGGLE] =\
                            not self.widgets.liststore[path][self.COL_TOGGLE]
        active = [row for row in self.widgets.liststore if row[self.COL_TOGGLE]]
        self.widgets.button_repair.set_sensitive(len(active) > 0)

    def on_button_repair_clicked(self, _widget):
        session.open(self._dbobj.path)
        if session.needs_update():
            self.widgets.message_label.set_text(_("Can't repair database that needs an update."))
            self.widgets.message_revealer.set_reveal_child(True)
            return

        for row in self.widgets.liststore:
            row[self.COL_RESULT] = ""
            toggled = row[self.COL_TOGGLE]
            if toggled:
                checker = row[self.COL_CHECKER]
                row[self.COL_RESULT] = checker.repair()

        session.close()
