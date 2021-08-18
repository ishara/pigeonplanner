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
Functions for some common tasks
"""


import os
import string
import random
import locale
import logging
import datetime
import functools
import webbrowser
import subprocess
from typing import List, Dict, Tuple, Optional, Union

try:
    import html  # noqa
except ImportError:
    # Glade only supports Python 2 when using custom widgets. Catch these Python 3 libraries and
    # silently pass on, no widget calls functions that use these libraries.
    pass

import peewee

from pigeonplanner.core import const
from pigeonplanner.core import enums
from pigeonplanner.core import config
from pigeonplanner.database.models import Pigeon, Person


class LogFunctionCall:
    def __init__(self, logger=None):
        self.logger = logger

    def __call__(self, func):
        if self.logger is None:
            self.logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.debug("Called function: {}".format(func.__name__))
            result = func(*args, **kwargs)
            return result
        return wrapper


def get_date() -> str:
    return datetime.date.today().strftime(const.DATE_FORMAT)


def count_active_pigeons(pigeons: Optional[List[Pigeon]] = None) -> Dict[Union[str, int], int]:
    """Count the number of active pigeons in the database. If an optional list of pigeons
    is given, count those.

    :param pigeons: Optional. List of Pigeon objects.
    :returns: A dictionary containing total number of pigeons and numbers per sex.
    """

    counts = {
        "total": 0,
        enums.Sex.cock: 0,
        enums.Sex.hen: 0,
        enums.Sex.youngbird: 0,
        enums.Sex.unknown: 0
    }

    if pigeons is None:
        query = (Pigeon
               .select(Pigeon.sex, peewee.fn.Count(Pigeon.sex).alias("count"))
               .where(Pigeon.visible == True)  # noqa
               .group_by(Pigeon.sex))
        for row in query:
            counts[row.sex] = row.count
    else:
        for pigeon in pigeons:
            counts[pigeon.sex] += 1

    counts["total"] = sum(counts.values())

    return counts


def get_own_address() -> Optional[Person]:
    """
    Retrieve the users personal info
    """

    try:
        person = Person.get(Person.me == True)  # noqa
    except Person.DoesNotExist:
        person = None
    except peewee.OperationalError:
        # This function is called when an unexpected error occurs to get the
        # user's email address for the report dialog. When the error happens
        # during database creation or migration, there's no Person table yet.
        person = None
    except Exception:  # noqa
        # When an unhandled exception occurs before a database is opened, this
        # function is called as well. PeeWee just throws a generic Exception.
        person = None
    return person


def calculate_coefficient(place: int, out: int, as_string: Optional[bool] = False) -> Union[str, float]:
    """Calculate the coefficient of a result

    :param place: The pigeons place
    :param out: The total number of pigeons
    :param as_string: Return a localized string
    """

    coef = (float(place)/float(out))*config.get("options.coef-multiplier")
    if as_string:
        return locale.format_string("%.4f", coef)
    return coef


def format_place_coef(place: int, out: int) -> Tuple[str, float, str]:
    coef = calculate_coefficient(place, out)
    if place == 0:
        coefstr = "-"
        placestr = "-"
    else:
        coefstr = calculate_coefficient(place, out, as_string=True)
        placestr = str(place)
    return placestr, coef, coefstr


def format_speed(value: float) -> str:
    if value <= 0.0:
        return ""
    return locale.format_string("%.2f", value)


def add_zero_to_time(value: int) -> str:
    """Add a zero in front of a one digit number

    :param value: The value to be checked
    """

    if value >= 0 and value < 10:
        return "0%s" % value
    return str(value)


def get_random_string(length: int) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def url_hook(_about, link: str):
    webbrowser.open(link)


def email_hook(_about, email: str):
    webbrowser.open("mailto:%s" % email)


def escape_text(text: str) -> str:
    if not text:
        return ""
    return html.escape(text, True)


def open_file(path: str):
    from pigeonplanner.ui.messagedialog import ErrorDialog

    norm_path = os.path.normpath(path)
    if not os.path.exists(norm_path):
        ErrorDialog((_("Error: This file does not exist"), None, _("Error")))
        return

    if const.WINDOWS:
        try:
            os.startfile(norm_path)
        except WindowsError as exc:
            ErrorDialog((_("Error opening file:"), str(exc), _("Error")))
    else:
        if const.OSX:
            utility = "open"
        else:
            utility = "xdg-open"
        search = os.environ["PATH"].split(":")
        for lpath in search:
            prog = os.path.join(lpath, utility)
            if os.path.isfile(prog):
                import subprocess
                subprocess.call((prog, norm_path))
                return


def open_folder(path: str):
    if const.WINDOWS:
        cmd = ["explorer", "/root,", path]
    elif const.OSX:
        cmd = ["open", path]
    else:
        cmd = ["xdg-open", path]
    subprocess.run(cmd)


def open_help(article: int):
    webbrowser.open(const.DOCURL % article)


def get_pagesize_from_opts() -> str:
    optvalue = config.get("printing.general-paper")
    if optvalue == 0:
        psize = "A4"
    elif optvalue == 1:
        psize = "Letter"
    else:
        raise ValueError("Invalid paper size option: %s" % optvalue)
    return psize
