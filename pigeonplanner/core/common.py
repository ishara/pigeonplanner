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

try:
    import html
    import urllib.request
except ImportError:
    # Glade only supports Python 2 when using custom widgets. Catch these Python 3 libraries and
    # silently pass on, no widget calls functions that use these libraries.
    pass

import peewee

from pigeonplanner.core import const
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


def get_date():
    return datetime.date.today().strftime(const.DATE_FORMAT)


def count_active_pigeons(pigeons=None):
    """
    Count the active pigeons as total and seperate sexes
    """

    if pigeons is None:
        pigeons = Pigeon.select().where(Pigeon.visible == True)

    cocks = 0
    hens = 0
    ybirds = 0
    unknown = 0
    total = 0
    for pigeon in pigeons:
        total += 1
        if pigeon.is_cock():
            cocks += 1
        elif pigeon.is_hen():
            hens += 1
        elif pigeon.is_youngbird():
            ybirds += 1
        elif pigeon.is_unknown():
            unknown += 1

    return total, cocks, hens, ybirds, unknown


def get_own_address():
    """
    Retrieve the users personal info
    """

    try:
        person = Person.get(Person.me == True)
    except Person.DoesNotExist:
        person = None
    except peewee.OperationalError:
        # This function is called when an unexpected error occurs to get the
        # user's email address for the report dialog. When the error happens
        # during database creation or migration, there's no Person table yet.
        person = None
    except Exception:
        # When an unhandled exception occurs before a database is opened, this
        # function is called as well. PeeWee just throws a generic Exception.
        person = None
    return person


def calculate_coefficient(place, out, as_string=False):
    """Calculate the coefficient of a result

    :param place: The pigeons place
    :param out: The total number of pigeons
    :param as_string: Return a localized string
    """

    coef = (float(place)/float(out))*config.get("options.coef-multiplier")
    if as_string:
        return locale.format_string("%.4f", coef)
    return coef


def format_place_coef(place, out):
    coef = calculate_coefficient(place, out)
    if place == 0:
        coefstr = "-"
        placestr = "-"
    else:
        coefstr = calculate_coefficient(place, out, as_string=True)
        placestr = str(place)
    return placestr, coef, coefstr


def format_speed(value):
    if value <= 0.0:
        return ""
    return locale.format_string("%.2f", value)


def add_zero_to_time(value):
    """Add a zero in front of a one digit number

    :param value: The value to be checked
    """

    if value >= 0 and value < 10:
        return "0%s" % value
    return str(value)


def get_random_number(value):
    """Get a random number of the given length

    :param value: The length of the number
    """

    return "".join([random.choice("0123456789") for _ in range(value)])


def get_random_string(length):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def url_hook(about, link):
    webbrowser.open(link)


def email_hook(about, email):
    webbrowser.open("mailto:%s" % email)


def escape_text(text):
    if not text:
        return ""
    return html.escape(text, True)


def open_file(path):
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


def open_help(article):
    webbrowser.open(const.DOCURL % article)


def get_pagesize_from_opts():
    optvalue = config.get("printing.general-paper")
    if optvalue == 0:
        psize = "A4"
    elif optvalue == 1:
        psize = "Letter"
    return psize


class URLOpen:
    """
    A custom class to open URLs
    """
    def __init__(self, cookie=None):
        """
        Build our urllib.request opener

        @param cookie: Cookie to be used
        """

        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))

    def open(self, url, body, headers=None, timeout=8):
        """
        Open a given url

        @param url: The url to open
        @param body: Extra data to send along
        @param headers: Optional header
        @param timeout: timeout in seconds
        """

        if not headers:
            headers = const.USER_AGENT
        else:
            if "User-Agent" not in headers:
                headers.update(const.USER_AGENT)

        return self.opener.open(urllib.request.Request(url, body, headers), timeout=timeout)
