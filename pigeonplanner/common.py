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


import urllib2
import os.path

import gtk
import gobject

import const
import widgets


def create_stock_button(icons):
    """
    Register stock buttons from custom or stock images.

    @param icons: A list of tuples containing filename or stock, name and description
    """

    factory = gtk.IconFactory()
    factory.add_default()
    for image, name, description in icons:
        if image.startswith('gtk-'):
            # We need a widget (any widget) here to use the render_icon() method.
            pixbuf = gtk.Window().render_icon(image, gtk.ICON_SIZE_BUTTON)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(const.IMAGEDIR, image))
        iconset = gtk.IconSet(pixbuf)
        factory.add(name, iconset)
        gtk.stock_add([(name, description, 0, 0, 'pigeonplanner')])

def count_active_pigeons(database):
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

def search_file(filename, search_path):
    paths = search_path.split(':')
    path_found = None
    for path in paths:
        if os.path.exists(os.path.join(path, filename)):
            path_found = os.path.abspath(os.path.join(path, filename))
            break

    return path_found


class URLOpen:
    def __init__(self, cookie=None):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

    def open(self, url, body, headers=None):
        if not headers:
            headers = const.USER_AGENT
        else:
            if not "User-Agent" in headers:
                headers.update(const.USER_AGENT)

        return self.opener.open(urllib2.Request(url, body, headers))

