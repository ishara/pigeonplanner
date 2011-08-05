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


import datetime

import const
import messages


class InvalidInputError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def check_ring_entry(inputRing, inputYear):
    """
    Check if the ring and year input are valid
    
    @param inputRing: The ringnumber to check
    @param inputYear: the year to check
    """

    if not inputRing or not inputYear:
        raise InvalidInputError(messages.MSG_EMPTY_FIELDS)

    elif not inputYear.isdigit():
        raise InvalidInputError(messages.MSG_INVALID_NUMBER)

    elif not len(inputYear) == 4:
        raise InvalidInputError(messages.MSG_INVALID_LENGTH)

def check_date_input(date):
    try:
        datetime.datetime.strptime(date, const.DATE_FORMAT)
    except ValueError:
        raise InvalidInputError(messages.MSG_INVALID_FORMAT)

def check_lat_long(value):
    # Accepted values are:
    #    DD.dddddd°
    #    DD°MM.mmm’
    #    DD°MM’SS.s”
    value = value.replace(u',', u'.')
    for char in u' -+':
        value = value.replace(char, u'')
    if __check_float_repr(value) is not None:
        return
    if __check_dms_repr(value) is not None: 
        return
    raise InvalidInputError(value)

def __check_float_repr(value):
    value = value.replace(u'°', u'')
    try : 
        return float(value)      
    except ValueError:
        return None

def __check_dms_repr(value):
    # Replace the degree and quotes by colons...
    for char in u"°'\"":
        value = value.replace(char, u':')
    value = value.rstrip(u':')
    # ... so we can easily split the value up
    splitted = value.split(u':')

    # First value always should be all digits
    if not splitted[0].isdigit():
        return
    # Depending on format...
    if len(splitted) == 2:
        # ... minutes should be a valid float
        try:
            float(splitted[1])
        except ValueError:
            return
    elif len(splitted) == 3:
        # ... minutes should be all digits ...
        if not splitted[1].isdigit():
            return
        # ... and seconds a valid float
        try:
            float(splitted[2])
        except ValueError:
            return
    else:
        # Too many or little splitted values
        return
    return value

