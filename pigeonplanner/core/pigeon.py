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

import peewee

from . import enums
from . import errors
from pigeonplanner import thumbnail
from pigeonplanner.database.models import Pigeon, Image, Status, database

logger = logging.getLogger(__name__)


def add_pigeon(data, status, statusdata):
    """Add a pigeon

    :param data:
    :param status: One of the status constants
    :param statusdata:
    """

    _check_input_data(data)
    _apply_status_out_of_sync_workaround()

    # Handle sire and dam
    data["sire"] = get_or_create_pigeon(data.get("sire", None), enums.Sex.cock, False)
    data["dam"] = get_or_create_pigeon(data.get("dam", None), enums.Sex.hen, False)
    # Handle these after pigeon creation
    image = data.pop("image", None)
    # Try to create the pigeon
    try:
        with database.transaction():
            pigeon = Pigeon.create(**data)
            query = Status.insert(pigeon=pigeon, status_id=status, **statusdata)
            query.execute()
    except peewee.IntegrityError:
        pigeon = Pigeon.get_for_band(
            (data["band_country"], data["band_letters"], data["band_number"], data["band_year"])
        )
        if pigeon.visible:
            logger.debug("Pigeon already exists %s", pigeon.band_tuple)
            raise errors.PigeonAlreadyExists(pigeon)
        else:
            raise errors.PigeonAlreadyExistsHidden(pigeon)

    _create_image(pigeon, image)

    return pigeon


def update_pigeon(pigeon, data, status, statusdata):
    """Update the pigeon

    :param pigeon:
    :param data:
    :param status: One of the status constants
    :param statusdata:
    """

    _check_input_data(data)
    _apply_status_out_of_sync_workaround()

    data["sire"] = get_or_create_pigeon(data.get("sire", None), enums.Sex.cock, False)
    data["dam"] = get_or_create_pigeon(data.get("dam", None), enums.Sex.hen, False)
    imagepath = data.pop("image", None)

    try:
        pigeon = pigeon.update_and_return(**data)
    except peewee.IntegrityError:
        pigeon = Pigeon.get_for_band(
            (data["band_country"], data["band_letters"], data["band_number"], data["band_year"])
        )
        if pigeon.visible:
            logger.debug("Pigeon already exists id=%s band=%s", pigeon.id, pigeon.band_tuple)
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
    logger.debug("Start removing pigeon id=%s band=%s", pigeon.id, pigeon.band_tuple)

    try:
        os.remove(thumbnail.get_path(pigeon.main_image))
    except:
        pass

    # TODO PW: this removes the pigeon_id in the through model. The medication table
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

    :param band_tuple: tuple of (country, letters, number, year) or None
    :param sex: one of the sex constants
    :param visible: boolean
    """
    if band_tuple is not None and band_tuple != ("", "", "", ""):
        country, letters, number, year = band_tuple
        try:
            with database.transaction():
                pigeon = Pigeon.create(band_country=country, band_letters=letters,
                                       band_number=number, band_year=year,
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
    if not data["sex"] in (enums.Sex.cock, enums.Sex.hen, enums.Sex.youngbird, enums.Sex.unknown):
        raise ValueError("Sex value has to be of type enums.Sex, but got '%r'" % data["sex"])


def _apply_status_out_of_sync_workaround():
    # TODO: This is a HACK, not a fix!
    #       There's a bug since version 3.0.0 where there's a possibility that the
    #       Pigeon and Status database tables become out of sync. They have a
    #       one-to-one relationship with the Status having a UNIQUE backref to
    #       the Pigeon. Some user reports show that a Status row is left behind
    #       after removing a Pigeon row. Thus adding a Pigeon row with the same
    #       ID will trigger an IntegrityError. Especially messing up get or create
    #       functionality. The current workaround is to remove the extra Status row(s)
    #       where the Pigeon ID references to a non-existing Pigeon row. This
    #       workaround is put here because it affects different parts in the code
    #       and to keep this in one place only. The user has to re-open the database
    #       though for having effect.
    #       The reason why this problem happens was not found during some testing.
    #       The Status row is deleted on database level (ON DELETE CASCADE).
    #       Fix it as soon as possible.
    if Pigeon.select().count() < Status.select().count():
        logger.warning("The Pigeon and Status tables are out of sync, applying fix.")
        pigeon_ids = Pigeon.select(Pigeon.id)
        Status.delete().where(Status.pigeon.not_in(pigeon_ids)).execute()
