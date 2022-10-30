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


from gi.repository import Gio

from pigeonplanner.core import const


def get_type(filename: str) -> str:
    """
    Get the mime type of the given file
    """
    if filename is None:
        return ""
    mimetype, result_uncertain = Gio.content_type_guess(filename)
    if const.WINDOWS:
        mimetype = Gio.content_type_get_mime_type(mimetype)
    return mimetype


def get_basetype(mimetype: str) -> str:
    """
    Get the basetype from a mimetype of format basetype/subtype
    """
    if mimetype is None:
        return ""
    return mimetype.split("/")[0]


def get_icon(mimetype: str) -> Gio.ThemedIcon:
    return Gio.content_type_get_icon(mimetype)


def is_image(mimetype: str) -> bool:
    return get_basetype(mimetype) == "image"


def is_directory(mimetype: str) -> bool:
    return get_basetype(mimetype) == "x-directory"
