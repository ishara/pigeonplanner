#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import sys
import gettext
import locale
import pygtk; pygtk.require('2.0')
import gobject
import gtk
import gtk.glade
import __builtin__


def main():
    win32 = sys.platform.startswith("win")

    currentPath = ''

    if not win32:
        currentPath = os.path.abspath(os.path.dirname(__file__))

    if currentPath.startswith('/usr/bin'):
        LOCALE_PATH = '/usr/share/locale'
    else:
        LOCALE_PATH = os.path.join(currentPath, 'languages')

    if win32:
        import pigeonplanner.libi18n as libi18n
        libi18n.fix_locale()
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass
        
    APP_NAME = 'pigeonplanner'

    for module in (gettext, gtk.glade):
        module.bindtextdomain(APP_NAME, LOCALE_PATH)
        module.textdomain(APP_NAME)

    __builtin__._ = gettext.gettext


    import pigeonplanner.mainwindow as main

    try:
        pigeonplanner = main.MainWindow()
        gtk.main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except:
        raise

if __name__ == "__main__":
    main()

