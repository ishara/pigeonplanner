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

import Const
import Widgets


def check_entrys(entrys):
    '''
    Check the ring and year entry's if they contain valid text.

    @param entrys: Dic of entrys to check
    '''

    parent = entrys['ring'].get_toplevel()

    inputRing = entrys['ring'].get_text()
    inputYear = entrys['year'].get_text()
    checkPigeon = check_ring_entry(parent, inputRing, inputYear)
    if not checkPigeon: return False

    inputRingSire = entrys['sire'].get_text()
    inputYearSire = entrys['yearsire'].get_text()
    if inputRingSire:
        checkSire = check_ring_entry(parent, inputRingSire, inputYearSire, _('sire'))
        if not checkSire: return False

    inputRingDam = entrys['dam'].get_text()
    inputYearDam = entrys['yeardam'].get_text()
    if inputRingDam:
        checkDam = check_ring_entry(parent, inputRingDam, inputYearDam, _('dam'))
        if not checkDam: return False

    return True

def check_ring_entry(parent, inputRing, inputYear, pigeon=_('pigeon')):
    '''
        
    @param inputRing: The ringnumber to check
    @param inputYear: the year to check
    @param pigeon: Kind of pigeon
    '''

    if not inputRing or not inputYear:
        Widgets.message_dialog('error', Const.MSGINPUT %pigeon, parent)
        return False

    integerCheckRing = inputRing.isdigit()
    integerCheckJaar = inputYear.isdigit()
    if not integerCheckRing or not integerCheckJaar:
        Widgets.message_dialog('error', Const.MSGNUMBER %pigeon, parent)
        return False

    if not len(inputRing) == 7 or not len(inputYear) == 2:
        Widgets.message_dialog('error', Const.MSGLENGTH %pigeon, parent)
        return False

    return True

