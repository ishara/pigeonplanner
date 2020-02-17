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


from pigeonplanner.core import enums
from pigeonplanner.ui import utils
from pigeonplanner.ui.widgets import displayentry


class SexEntry(displayentry.DisplayEntry):
    __gtype_name__ = "SexEntry"

    def __init__(self):
        displayentry.DisplayEntry.__init__(self)
        self.set_icon_activatable(0, False)

    def set_sex(self, sex):
        if sex is None:
            text = ""
            icon_name = None
        else:
            text = enums.Sex.get_string(sex)
            icon_name = utils.get_sex_icon_name(sex)
        self.set_text(text)
        self.set_icon_from_icon_name(0, icon_name)
