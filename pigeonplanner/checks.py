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


import const
import widgets
import messages


def check_entrys(entrys):
    """
    Check the ring and year entry's if they contain valid text.

    @param entrys: Dic of entrys to check
    """

    parent = entrys['ring'].get_toplevel()

    inputRing = entrys['ring'].get_text()
    inputYear = entrys['year'].get_text()
    checkPigeon = check_ring_entry(parent, inputRing, inputYear)
    if not checkPigeon: return False

    inputRingSire = entrys['sire'].get_text()
    inputYearSire = entrys['yearsire'].get_text()
    if inputRingSire:
        checkSire = check_ring_entry(parent, inputRingSire, inputYearSire)
        if not checkSire: return False

    inputRingDam = entrys['dam'].get_text()
    inputYearDam = entrys['yeardam'].get_text()
    if inputRingDam:
        checkDam = check_ring_entry(parent, inputRingDam, inputYearDam)
        if not checkDam: return False

    return True

def check_ring_entry(parent, inputRing, inputYear):
    """
        
    @param inputRing: The ringnumber to check
    @param inputYear: the year to check
    """

    if not inputRing or not inputYear:
        widgets.message_dialog(const.ERROR, messages.MSG_EMPTY_FIELDS, parent)
        return False

    if not inputYear.isdigit():
        widgets.message_dialog(const.ERROR, messages.MSG_INVALID_NUMBER,
                               parent)
        return False

    if not len(inputYear) == 4:
        widgets.message_dialog(const.ERROR, messages.MSG_INVALID_LENGTH,
                               parent)
        return False

    return True

