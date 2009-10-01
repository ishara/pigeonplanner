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


import os
import urllib
import logging
logger = logging.getLogger(__name__)

import const


def update():
    new = False

    local = os.path.join(const.PREFDIR, const.UPDATEURL.split('/')[-1])

    try:
        urllib.urlretrieve(const.UPDATEURL, local)
        versionfile = open(local, 'r')
        version = versionfile.readline().strip()
        versionfile.close()
        os.remove(local)
    except IOError, e:
        logger.error(e)
        version = None

    if not version:
        msg = const.MSG_UPDATE_ERROR
    elif const.VERSION < version:
        msg = const.MSG_UPDATE_AVAILABLE
        new = True
    elif const.VERSION == version:
        msg = const.MSG_NO_UPDATE
    elif const.VERSION > version:
        msg = const.MSG_UPDATE_DEVELOPMENT

    return msg, new

