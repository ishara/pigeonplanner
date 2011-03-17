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
import datetime
import webbrowser
import logging
logger = logging.getLogger(__name__)

import gtk
import gobject

from pigeonplanner import const


def get_sexdic():
    return {'0': _('Cock'), '1': _('Hen'), '2': _('Young bird')}

def get_sex(sex):
    return get_sexdic()[sex]

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

def get_windows_version():
    ver = os.sys.getwindowsversion()
    ver_format = ver[3], ver[0], ver[1]
    win_versions = {
                (1, 4, 0): '95',
                (1, 4, 10): '98',
                (1, 4, 90): 'ME',
                (2, 4, 0): 'NT',
                (2, 5, 0): '2000',
                (2, 5, 1): 'XP',
                (2, 5, 2): '2003',
                (2, 6, 0): 'Vista',
                (2, 6, 1): '7',
            }
    if ver_format in win_versions:
        return win_versions[ver_format]
    else:
        return ", ".join(str(n) for n in sys.getwindowsversion())

def get_date():
    return datetime.date.today().strftime(const.DATE_FORMAT)

def encode_string(string):
    """
    Encode a string to utf-8

    @param string: A string which needs to be encoded
    """

    return string.decode(const.ENCODING).encode("utf-8")

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

def add_statusbar_message(statusbar, message):
    statusbar.pop(0)
    statusbar.push(0, message)
    gobject.timeout_add_seconds(4, pop_statusbar_message, statusbar)

def pop_statusbar_message(statusbar):
    statusbar.pop(0)
    return False

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
        return '0%s' %value
    return str(value)

def get_random_number(value):
    """
    Get a random number of the given length

    @param value: The length of the number
    """

    return ''.join([random.choice('0123456789') for x in range(value)])

def image_to_thumb(img_path):
    """
    Convert an image to a thumbnail

    @param img_path: the full path to the image
    """

    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(img_path, 200, 200)
    except gobject.GError:
        logger.error("Couldn't create thumbnail from: %s", img_path)
    else:
        pixbuf.save(get_thumb_path(img_path), 'png')

def get_thumb_path(image):
    """
    Get the thumbnail from an image

    @param image: the full path to the image
    """

    path = os.path.join(const.THUMBDIR, "%s.png") % get_image_name(image)
    return get_unicode_path(path)

def get_image_name(name):
    """
    Get the filename from a full image path

    @param name: the full path to the image
    """

    return os.path.splitext(os.path.basename(name))[0]

def build_thumbnails(pigeons):
    for pigeon in pigeons.values():
        img_path = pigeon.get_image()
        if img_path != '' and img_path is not None:
            image_to_thumb(img_path)

def url_hook(about, link):
    webbrowser.open(link)

def email_hook(about, email):
    webbrowser.open("mailto:%s" % email)


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

