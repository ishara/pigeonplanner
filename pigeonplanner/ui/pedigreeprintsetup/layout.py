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

import json
import copy
import typing
import copyreg

from gi.repository import Gdk

from pigeonplanner.reportlib.styles import PARA_ALIGN_RIGHT


# layout_original: typing.Dict[typing.Any, typing.Any] = {
layout_original: typing.Dict[str, typing.Any] = {
    "meta": {
        "name": "Original",
        "description": "",
        "author": "Pigeon Planner"
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


layout_swapped: typing.Dict[typing.Any, typing.Any] = {
    "meta": {
        "name": "Swapped details",
        "description": "",
        "author": "Pigeon Planner"
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
        "pigeon_info": "no_show",
        "pigeon_image": "right",
        "user_name": True,
        "user_address": True,
        "user_phone": True,
        "user_email": True,
        "pigeon_name": True,
        "pigeon_sex": True,
        "pigeon_colour": True,
        "pigeon_extra": True,
        "pedigree_layout_pigeon": "details",
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


layouts = {
    "original": layout_original,
    "swapped": layout_swapped
}


def get_layout(layout_id, copy_=True):
    if copy_:
        return copy.deepcopy(layouts[layout_id])
    return layouts[layout_id]


# Make Gdk.RGBA available to copy.deepcopy()
copyreg.pickle(Gdk.RGBA, lambda obj: (Gdk.RGBA, (obj.red, obj.green, obj.blue)))


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Gdk.RGBA):
            return {"GdkRGBA": {"red": obj.red, "green": obj.green, "blue": obj.blue}}
        return json.JSONEncoder.default(self, obj)


def _custom_decoder(dct):
    if "GdkRGBA" in dct:
        return Gdk.RGBA(dct["GdkRGBA"]["red"], dct["GdkRGBA"]["green"], dct["GdkRGBA"]["blue"])
    return dct


# TODO: what and where to save?
def save_layout():
    json.dumps(layouts, cls=_CustomEncoder, indent=2)


# TODO: what and from where to load?
def load_layout(foo):
    json.loads(foo, object_hook=_custom_decoder)
