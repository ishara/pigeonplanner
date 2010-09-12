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


import random
import urllib2
import os.path
import webbrowser

import gtk
import gobject

from pigeonplanner import const
from pigeonplanner import messages


def create_stock_button(icons):
    """
    Register stock buttons from custom or stock images.

    @param icons: A list of tuples containing filename or stock,
                  name and description
    """

    factory = gtk.IconFactory()
    factory.add_default()
    for image, name, description in icons:
        if image.startswith('gtk-'):
            # We need a widget (any widget) here to use render_icon()
            pixbuf = gtk.Window().render_icon(image, gtk.ICON_SIZE_BUTTON)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(const.IMAGEDIR,
                                                               image))
        iconset = gtk.IconSet(pixbuf)
        factory.add(name, iconset)
        gtk.stock_add([(name, description, 0, 0, 'pigeonplanner')])

def encode_string(string):
    """
    Encode a string to utf-8

    @param string: A string which needs to be encoded
    """

    return string.decode(const.ENCODING).encode("utf-8")

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

    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(img_path, 200, 200)
    pixbuf.save(os.path.join(const.THUMBDIR,
                         "%s.png") %get_image_name(img_path), 'png')

def get_thumb_path(image):
    """
    Get the thumbnail from an image

    @param image: the full path to the image
    """

    return os.path.join(const.THUMBDIR, "%s.png") %get_image_name(image)

def get_image_name(name):
    """
    Get the filename from a full image path

    @param name: the full path to the image
    """

    return os.path.splitext(os.path.basename(name))[0]

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

