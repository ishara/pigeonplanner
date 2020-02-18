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

from pigeonplanner.ui import utils
from pigeonplanner.ui import builder
from pigeonplanner.ui.tabs import basetab
from pigeonplanner.core import config


class PedigreeTab(builder.GtkBuilder, basetab.BaseTab):
    def __init__(self):
        builder.GtkBuilder.__init__(self, "PedigreeView.ui")
        basetab.BaseTab.__init__(self, "PedigreeTab", _("Pedigree"), "icon_pedigree.png")

        self.widgets.combogenerations.set_active_id(config.get("interface.pedigree-tab-generations"))

    def set_pigeon(self, pigeon=None):
        utils.draw_pedigree(self.widgets.gridsire, pigeon.sire if pigeon else None)
        utils.draw_pedigree(self.widgets.griddam, pigeon.dam if pigeon else None)

    def clear_pigeon(self):
        self.set_pigeon()

    def set_num_generations(self, num_generations):
        if num_generations == "3":
            left_attach_limit = 4
        elif num_generations == "4":
            left_attach_limit = 6
        else:
            raise ValueError("Argument num_generations must be 3 or 4.")

        for grid in [self.widgets.gridsire, self.widgets.griddam]:
            for grid_child in grid.get_children():
                visible = grid.child_get_property(grid_child, "left-attach") <= left_attach_limit
                grid_child.set_visible(visible)

        config.set("interface.pedigree-tab-generations", num_generations)

    def on_combogenerations_changed(self, widget):
        self.set_num_generations(widget.get_active_text())
