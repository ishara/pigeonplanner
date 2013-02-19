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


import os
import json
import urllib
import logging
logger = logging.getLogger(__name__)

from pigeonplanner import const
from pigeonplanner import config
from pigeonplanner import messages


class UpdateError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Updater: %s" % self.msg


def update():
    local = os.path.join(const.TEMPDIR, 'pigeonplanner_update')

    try:
        urllib.urlretrieve(const.UPDATEURL, local)
        with open(local, 'r') as versionfile:
            versiondict = json.load(versionfile)
    except IOError, e:
        logger.error(e)
        raise UpdateError(messages.MSG_UPDATE_ERROR)

    try:
        os.remove(local)
    except:
        pass

    # See what version we need to check for
    dev = versiondict["dev"]
    stable = versiondict["stable"]
    if config.get('options.check-for-dev-updates'):
        if stable > dev:
            version = stable
        else:
            version = dev
    else:
        version = stable

    new = False
    if const.VERSION < version:
        msg = messages.MSG_UPDATE_AVAILABLE
        new = True
    elif const.VERSION == version:
        msg = messages.MSG_NO_UPDATE
    elif const.VERSION > version:
        msg = messages.MSG_UPDATE_DEVELOPMENT

    return new, msg

