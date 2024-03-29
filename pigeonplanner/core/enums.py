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


class Sex:
    cock = 0
    hen = 1
    youngbird = 2
    unknown = 3

    mapping = {
        cock: _("Cock"),
        hen: _("Hen"),
        youngbird: _("Young bird"),
        unknown: _("Unknown")
    }

    @classmethod
    def get_string(cls, sex):
        return cls.mapping[sex]


class Status:
    dead = 0
    active = 1
    sold = 2
    lost = 3
    breeder = 4
    loaned = 5
    widow = 6

    mapping = {
        dead: _("Dead"),
        active: _("Active"),
        sold: _("Sold"),
        lost: _("Lost"),
        breeder: _("Breeder"),
        loaned: _("On loan"),
        widow: _("Widow"),
    }

    @classmethod
    def get_string(cls, status):
        return cls.mapping[status]


class Action:
    add = 1
    edit = 2


class Backup:
    create = 1
    restore = 2
