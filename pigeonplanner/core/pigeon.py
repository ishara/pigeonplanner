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
import logging
logger = logging.getLogger(__name__)

import peewee

from . import enums
from . import errors
from pigeonplanner import thumbnail
from pigeonplanner.database import session
from pigeonplanner.database.models import Pigeon, Image, Status


def add_pigeon(data, status, statusdata):
    """
    Add a pigeon

    @param data:
    @param status: One of the status constants
    @param statusdata:
    """

    _check_input_data(data)

    # Handle sire and dam
    data["sire"] = get_or_create_pigeon(data.get("sire", None), enums.Sex.cock, False)
    data["dam"] = get_or_create_pigeon(data.get("dam", None), enums.Sex.hen, False)
    # Handle these after pigeon creation
    image = data.pop("image", None)
    # Try to create the pigeon
    try:
        with session.connection.transaction():
            pigeon = Pigeon.create(**data)
            query = Status.insert(pigeon=pigeon, status_id=status, **statusdata)
            query.execute()
    except peewee.IntegrityError:
        pigeon = Pigeon.get_for_band((data["band"], data["year"]))
        if pigeon.visible:
            logger.debug("Pigeon already exists '%s'", pigeon.band_string)
            raise errors.PigeonAlreadyExists(pigeon)
        else:
            raise errors.PigeonAlreadyExistsHidden(pigeon)

    _create_image(pigeon, image)

    return pigeon

def update_pigeon(pigeon, data, status, statusdata):
    """
    Update the pigeon

    @param pigeon: 
    @param data:
    @param status: One of the status constants
    @param statusdata:
    """

    _check_input_data(data)

    data["sire"] = get_or_create_pigeon(data.get("sire", None), enums.Sex.cock, False)
    data["dam"] = get_or_create_pigeon(data.get("dam", None), enums.Sex.hen, False)
    imagepath = data.pop("image", None)

    try:
        pigeon = pigeon.update_and_return(**data)
    except peewee.IntegrityError:
        pigeon = Pigeon.get_for_band((data["band"], data["year"]))
        if pigeon.visible:
            logger.debug("Pigeon already exists '%s'", pigeon.band_string)
            raise errors.PigeonAlreadyExists(pigeon)
        else:
            raise errors.PigeonAlreadyExistsHidden(pigeon)

    # Update the images
    if pigeon.main_image is None:
        _create_image(pigeon, imagepath) 
    else:
        if imagepath != pigeon.main_image.path:
            # Remove the old thumbnail (if exists)
            try:
                os.remove(thumbnail.get_path(pigeon.main_image.path))
            except:
                pass
            if imagepath:
                query = Image.update(path=imagepath).where(
                    (Image.pigeon == pigeon) & (Image.main == True))
                query.execute()
            else:
                pigeon.main_image.delete_instance()

    # Update the status
    query = Status.update(pigeon=pigeon, status_id=status, **statusdata).where(
        Status.pigeon == pigeon)
    query.execute()

    return pigeon

def remove_pigeon(pigeon):
    logger.debug("Start removing pigeon '%s'", pigeon.band_string)

    try:
        os.remove(thumbnail.get_path(pigeon.main_image))
    except:
        pass

    #TODO PW: this removes the pigeon_id in the through model. The medication table
    #         entry will remain. How to make sure this is also deleted? Note: only
    #         if this is the only remaining pigeon for this record.
    pigeon.medication.clear()
    pigeon.delete_instance()

def build_pedigree_tree(pigeon, index, depth, lst):
    if depth > 5 or pigeon is None or index >= len(lst):
        return

    lst[index] = pigeon
    build_pedigree_tree(pigeon.sire, (2*index)+1, depth+1, lst)
    build_pedigree_tree(pigeon.dam, (2*index)+2, depth+1, lst)

def get_or_create_pigeon(band_tuple, sex, visible):
    """

    @param band_tuple: tuple of (band, year) or None
    @param sex: one of the sex constants
    @param visible: boolean
    """
    if band_tuple is not None and band_tuple != ("", ""):
        band, year = band_tuple
        try:
            with session.connection.transaction():
                pigeon = Pigeon.create(band=band, year=year,
                                       sex=sex, visible=visible)
                query = Status.insert(pigeon=pigeon)
                query.execute()
        except peewee.IntegrityError:
            pigeon = Pigeon.get_for_band(band_tuple)
    else:
        pigeon = None
    return pigeon

def _create_image(pigeon, path):
    if path:
        query = Image.insert(pigeon=pigeon, path=path, main=True)
        query.execute()

def _check_input_data(data):
    if not data["sex"] in (enums.Sex.cock, enums.Sex.hen, enums.Sex.unknown):
        raise ValueError("Sex value has to be of type enums.Sex, but got '%r'" % data["sex"])

