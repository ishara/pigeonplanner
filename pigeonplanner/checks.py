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

"""
Provides functions to check band and year entries
"""


from pigeonplanner import messages


def check_ring_entry(inputRing, inputYear):
    """
    Check if the ring and year input are valid
    
    @param inputRing: The ringnumber to check
    @param inputYear: the year to check
    """

    msg = ""
    error = False

    if not inputRing or not inputYear:
        error = True
        msg = messages.MSG_EMPTY_FIELDS

    elif not inputYear.isdigit():
        error = True
        msg = messages.MSG_INVALID_NUMBER

    elif not len(inputYear) == 4:
        error = True
        msg = messages.MSG_INVALID_LENGTH

    return error, msg

