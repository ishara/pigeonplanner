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
import sys
import random
import inspect
import urllib2
import os.path
import platform
import datetime
import webbrowser
import logging
logger = logging.getLogger(__name__)

import gtk
import glib

import const
from translation import gettext as _


def get_sexdic():
    return {'0': _('Cock'), '1': _('Hen'), '2': _('Young bird')}

def get_sex(sex):
    return get_sexdic()[sex]

statusdic = {0: 'Dead', 1: 'Active', 2: 'Sold', 3: 'Lost', 4: 'Breeder', 5: 'Loan'}
def get_status(status):
    return statusdic[status]

def create_stock_button(icons):
    """
    Register stock buttons from custom images.

    @param icons: A list of tuples containing filename, name and description
    """

    factory = gtk.IconFactory()
    factory.add_default()
    for img, name, description in icons:
        pb = gtk.gdk.pixbuf_new_from_file(os.path.join(const.IMAGEDIR, img))
        iconset = gtk.IconSet(pb)
        factory.add(name, iconset)
        gtk.stock_add([(name, description, 0, 0, 'pigeonplanner')])

def get_function_name():
    """
    Retrieve the name of the fnction/method
    """

    return inspect.stack()[1][3]

def get_operating_system():
    operatingsystem = platform.system()
    if operatingsystem == "Windows":
        release, version, csd, ptype = platform.win32_ver()
        distribution = "%s %s" % (release, csd)
    elif operatingsystem == "Linux":
        distname, version, nick = platform.linux_distribution()
        distribution = "%s %s" % (distname, version)
    elif operatingsystem == "Darwin":
        release, versioninfo, machine = platform.mac_ver()
        distribution = release
    else:
        distribution = ''
    return operatingsystem, distribution

def get_date():
    return datetime.date.today().strftime(const.DATE_FORMAT)

def encode_string(string):
    """
    Encode a string to utf-8

    @param string: A string which needs to be encoded
    """

    return string.decode(sys.getfilesystemencoding()).encode("utf-8")

def get_unicode_path(path):
    """
    Return the Unicode version of a path string.

    @param path: The path to be converted to Unicode
    @type path: str
    @returns: The Unicode version of path
    @rtype: unicode
    """

    if not isinstance(path, str):
        return path

    if const.WINDOWS:
        # In Windows path/filename returned from an environment variable
        # is in filesystemencoding
        try:
            return unicode(path, sys.getfilesystemencoding())
        except:
            print "Problem encountered converting string: %s." % path
            return unicode(path, sys.getfilesystemencoding(), errors='replace')
    else:
        try:
            return unicode(path)
        except:
            print "Problem encountered converting string: %s." % path
            return unicode(path, sys.getfilesystemencoding(), errors='replace')

def count_active_pigeons(database):
    """
    Count the active pigeons as total and seperate sexes

    @param database: A Pigeon Planner database instance
    """

    cocks = 0
    hens = 0
    ybirds = 0
    total = 0
    for pigeon in database.get_pigeons():
        if not pigeon[5]: continue

        total += 1

        if pigeon[4] == '0':
            cocks += 1
        elif pigeon[4] == '1':
            hens += 1
        elif pigeon[4] == '2':
            ybirds += 1

    return total, cocks, hens, ybirds

def get_own_address(database):
    """
    Retrieve the users personal info

    @param database: A Pigeon Planner database instance
    """

    userinfo = dict(name='', street='', code='', city='', country='',
                    phone='', email='', comment='')
    info = database.get_own_address()
    if info:
        userinfo['name'] = info[1]
        userinfo['street'] = info[2]
        userinfo['code'] = info[3]
        userinfo['city'] = info[4]
        userinfo['country'] = info[5]
        userinfo['phone'] = info[6]
        userinfo['email'] = info[7]
        userinfo['comment'] = info[8]
    return userinfo

def get_pindex_from_band(band, year):
    """
    Create the pindex from the pigeons band and year

    @param band: The pigeons band number
    @param year: The year of the pigeon
    """

    return band+year

def get_pindex_from_band_string(bandstring):
    """
    Create the pindex from a pigeons bandstring

    @param bandstring: The pigeons bandstring
    """

    band, year = bandstring.split('/')
    return get_pindex_from_band(band.strip(), year.strip())

def get_band_from_pindex(pindex):
    """
    Retrieve the pigeons band and year from a pindex

    @param pindex: The pindex of the pigeon
    """

    band = pindex[:-4]
    year = pindex[-4:]
    return band, year

def calculate_coefficient(place, out):
    """
    Calculate the coefficient of a result

    @param place: The pigeons place
    @param out: The total number of pigeons
    """

    return (float(place)/float(out))*100

def add_zero_to_time(value):
    """
    Add a zero in front of a one digit number

    @param value: The value to be checked
    """

    if value >= 0 and value < 10:
        return '0%s' % value
    return str(value)

def get_random_number(value):
    """
    Get a random number of the given length

    @param value: The length of the number
    """

    return ''.join([random.choice('0123456789') for x in range(value)])

def url_hook(about, link):
    webbrowser.open(link)

def email_hook(about, email):
    webbrowser.open("mailto:%s" % email)

def escape_text(text):
    if not text:
        return ""
    return glib.markup_escape_text(text)

def open_file(path):
    from ui.messagedialog import ErrorDialog

    norm_path = unicode(os.path.normpath(path), 'utf-8')
    if not os.path.exists(norm_path):
        ErrorDialog((_("Error: This file does not exist"), None, _("Error")))
        return

    if const.WINDOWS:
        try:
            os.startfile(norm_path)
        except WindowsError, exc:
            ErrorDialog((_("Error opening file:"), str(exc), _("Error")))
    else:
        if const.OSX:
            utility = 'open'
        else:
            utility = 'xdg-open'
        search = os.environ['PATH'].split(':')
        for lpath in search:
            prog = os.path.join(lpath, utility)
            if os.path.isfile(prog):
                import subprocess
                subprocess.call((prog, norm_path))
                return

def open_help(article):
    webbrowser.open(const.DOCURL % article)


class URLOpen:
    """
    A custom class to open URLs
    """
    def __init__(self, cookie=None):
        """
        Build our urllib2 opener

        @param cookie: Cookie to be used
        """

        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

    def open(self, url, body, headers=None):
        """
        Open a given url

        @param url: The url to open
        @param body: Extra data to send along
        @param headers: Optional header
        """

        if not headers:
            headers = const.USER_AGENT
        else:
            if not "User-Agent" in headers:
                headers.update(const.USER_AGENT)

        return self.opener.open(urllib2.Request(url, body, headers))

