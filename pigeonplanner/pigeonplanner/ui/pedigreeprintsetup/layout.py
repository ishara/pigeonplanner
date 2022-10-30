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
import json
import copy
import copyreg
import collections.abc
from typing import Any, Dict, List

from gi.repository import Gdk

from pigeonplanner.core import const
from pigeonplanner.reportlib.styles import PARA_ALIGN_RIGHT


Layout = Dict[str, Any]

# Make Gdk.RGBA available to copy.deepcopy()
copyreg.pickle(Gdk.RGBA, lambda obj: (Gdk.RGBA, (obj.red, obj.green, obj.blue)))


def update_recursively(base, custom):
    for key, value in custom.items():
        if isinstance(value, collections.abc.Mapping):
            base[key] = update_recursively(base.get(key, {}), value)
        else:
            base[key] = value
    return base


def apply_default_layout(layout):
    base = copy.deepcopy(_layout_base)
    return update_recursively(base, layout)


_layout_base: Layout = {
    "meta": {
        "name": "",
        "description": "",
        "author": ""
    },
    "paper_format": "A4",
    "margins": {
        "top": 2.5,
        "bottom": 2.5,
        "left": 1.0,
        "right": 1.0
    },
    "font_styles": {
        "Title": {
            "size": 18,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "UserInfo": {
            "size": 12,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "PigeonInfo": {
            "size": 10,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "PedigreeBoxBand": {
            "size": 8,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "PedigreeBoxDetailsLeft": {
            "size": 8,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "PedigreeBoxDetailsRight": {
            "size": 8,
            "color": Gdk.RGBA(0, 0, 0),
            "align": PARA_ALIGN_RIGHT
        },
        "PedigreeBoxComments": {
            "size": 8,
            "color": Gdk.RGBA(0, 0, 0)
        }
    },
    "graphics_styles": {
        "TitleSeparator": {
            "line_width": 1.0,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "HeaderSeparator": {
            "line_width": 1.0,
            "color": Gdk.RGBA(0, 0, 0)
        },
        "PedigreeLine": {
            "line_width": 0.6
        },
        "PedigreeBoxNone": {
            "line_width": 1.0
        },
        "PedigreeBoxCock": {
            "line_width": 1.0,
        },
        "PedigreeBoxHen": {
            "line_width": 1.0,
        },
        "PedigreeBoxUnknown": {
            "line_width": 1.0,
        },
    },
    "options": {
        "user_info": "left",
        "pigeon_info": "right",
        "pigeon_image": "no_show",
        "user_name": True,
        "user_address": True,
        "user_phone": True,
        "user_email": True,
        "pigeon_name": True,
        "pigeon_sex": True,
        "pigeon_colour": True,
        "pigeon_extra": True,
        "background_image": "",
        "background_width_perc": 100,
        "background_height_perc": 100,
        "background_x_align": "center",
        "background_y_align": "center",
        "pedigree_layout_pigeon": "image",
        "pedigree_gen_1_lines": 7,
        "pedigree_gen_2_lines": 7,
        "pedigree_gen_3_lines": 4,
        "pedigree_gen_4_lines": 2,
        "colour_edge": False,
        "colour_bg": False,
        "box_top_right": "empty",
        "box_middle_left": "empty",
        "box_middle_right": "empty",
        "box_bottom_left": "empty",
        "box_comments": True,
        "pedigree_sex_sign": False
    }
}

layout_original = {
    "meta": {
        "name": "Original",
        "author": "Pigeon Planner"
    }
}

layout_swapped = {
    "meta": {
        "name": "Swapped details",
        "author": "Pigeon Planner"
    },
    "options": {
        "pigeon_info": "no_show",
        "pigeon_image": "right",
        "pedigree_layout_pigeon": "details",
    }
}

default_layouts = {
    "original": apply_default_layout(layout_original),
    "swapped": apply_default_layout(layout_swapped)
}


def get_layout(layout_id: str, copy_: bool = True) -> Layout:
    all_layouts = {**default_layouts, **get_user_layouts()}
    if copy_:
        return copy.deepcopy(all_layouts[layout_id])
    return all_layouts[layout_id]


def get_user_layout_names() -> List[str]:
    return sorted([_filename_to_name(filename) for filename in os.listdir(const.PEDIGREEDIR)])


def get_user_layouts() -> Dict[str, Layout]:
    return {_filename_to_name(filename): load_layout(os.path.join(const.PEDIGREEDIR, filename))
            for filename in os.listdir(const.PEDIGREEDIR)}


def save_layout(layout_obj: dict, name: str) -> None:
    layout_obj["meta"]["name"] = name
    layout_obj["meta"]["description"] = ""
    layout_obj["meta"]["author"] = ""

    with open(_name_to_file_path(name), "w") as f:
        json.dump(layout_obj, f, cls=_CustomEncoder, indent=2)


def load_layout(filename: str) -> Layout:
    with open(filename) as f:
        return json.load(f, object_hook=_custom_decoder)


def remove_layout(name: str) -> None:
    os.remove(_name_to_file_path(name))


def _name_to_file_path(name: str) -> str:
    return os.path.join(const.PEDIGREEDIR, f"{name}.json")


def _filename_to_name(filename: str) -> str:
    return filename.split(".", -1)[0]


def _custom_decoder(dct):
    if "GdkRGBA" in dct:
        return Gdk.RGBA(dct["GdkRGBA"]["red"], dct["GdkRGBA"]["green"], dct["GdkRGBA"]["blue"])
    return dct


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Gdk.RGBA):
            return {"GdkRGBA": {"red": obj.red, "green": obj.green, "blue": obj.blue}}
        return json.JSONEncoder.default(self, obj)
