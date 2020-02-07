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
Interface for checking program updates
"""


import json
import logging
from collections import namedtuple
from urllib.error import URLError
from urllib.request import urlopen

from pigeonplanner import messages
from pigeonplanner.core import const

logger = logging.getLogger(__name__)
UpdateInfo = namedtuple("UpdateInfo", ["update_available", "message", "latest_version"])


class UpdateError(Exception):
    def __init__(self, message):
        self.message = message


def version_to_tuple(version: str) -> tuple:
    """Convert version string to tuple"""
    return tuple(map(int, (version.split("."))))


def get_latest_version() -> str:
    try:
        response = urlopen(const.UPDATEURL)
    except URLError as exc:
        raise UpdateError(exc.reason)
    data = response.read().decode("utf-8")
    versiondict = json.loads(data)
    return versiondict["stable"]


def get_update_info() -> UpdateInfo:
    latest = get_latest_version()
    latest_tuple = version_to_tuple(latest)
    message = ""
    update_available = False
    if const.VERSION_TUPLE < latest_tuple:
        message = messages.MSG_UPDATE_AVAILABLE
        update_available = True
    elif const.VERSION_TUPLE == latest_tuple:
        message = messages.MSG_NO_UPDATE
    elif const.VERSION_TUPLE > latest_tuple:
        message = messages.MSG_UPDATE_DEVELOPMENT

    return UpdateInfo(update_available, message, latest)
