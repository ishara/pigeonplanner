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
import messages
from toolswindow import ToolsWindow


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

def get_own_address(database):
    userinfo = dict(name='', street='', code='', city='', country='', phone='', email='', comment='')
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

def check_userinfo(parent, main, name):
    if name == '':
        if widgets.message_dialog('question', messages.MSG_NO_INFO, parent):
            tw = ToolsWindow(main)
            tw.toolsdialog.set_keep_above(True)
            tw.treeview.set_cursor(3)
            tw.on_adadd_clicked(None, pedigree_call=True)
            tw.chkme.set_active(True)

            return False

    return True

def get_pindex_from_band(band, year):
    return band+year

def get_band_from_pindex(pindex):
    band = pindex[:len(pindex)-4]
    year = pindex[-4:]
    return band, year

def add_zero_to_time(value):
    if value >= 0 and value < 10:
        return '0%s' %value
    return str(value)


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

