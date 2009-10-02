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
import os.path
import sys
import gettext
import locale
import logging

try:
    import pygtk; pygtk.require('2.0')
except:
    print "Can not find PyGTK. This is necessary to run this program."
    sys.exit(1)

import gobject

try:
    import gtk
    import gtk.glade
except:
    print "The GTK+ runtime is required to run this program."
    sys.exit(1)

import __builtin__


class PigeonPlanner:
    def __init__(self):
        # Customized exception hook
        self.old_exception_hook = sys.excepthook
        sys.excepthook = self.exception_hook

        # Windows/py2exe detection
        win32 = sys.platform.startswith("win")
        py2exe = False
        if win32 and hasattr(sys, 'frozen'):
	        py2exe = True
	
        # Disable py2exe log feature
        if win32 and py2exe:
	        sys.stdout = open("nul", "w")
	        sys.stderr = open("nul", "w")

        # Locale setup
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

        # Options
        import pigeonplanner.options as options
        self.options = options.GetOptions()

		# Logging setup
        import pigeonplanner.const as const

        if os.path.exists(const.LOGFILE):
            if os.path.exists("%s.old" % const.LOGFILE):
                os.remove("%s.old" % const.LOGFILE)
            os.rename(const.LOGFILE, "%s.old" % const.LOGFILE)
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(name)s %(levelname)s: %(message)s', filename=const.LOGFILE, filemode='w')
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Version: %s" % const.VERSION)
        self.logger.debug("Home path: %s" % const.HOMEDIR)
        self.logger.debug("Prefs path: %s" % const.PREFDIR)
        self.logger.debug("Current path: %s" % os.getcwd())
        if win32:
            self.logger.debug("Windows version: %s" % ", ".join(str(n) for n in sys.getwindowsversion()))
        self.logger.debug("Python version: %s" % sys.version)
        self.logger.debug("GTK+ version: %s" % ".".join(str(n) for n in gtk.gtk_version))
        self.logger.debug("PyGTK version: %s" % ".".join(str(n) for n in gtk.pygtk_version))

    def exception_hook(self, type, value, trace):
        import pigeonplanner.logdialog as logdialog

        file_name = trace.tb_frame.f_code.co_filename
        line_no = trace.tb_lineno
        exception = type.__name__
        self.logger.critical("File %s line %i - %s: %s" % (file_name, line_no, exception, value))
        print self.old_exception_hook(type, value, trace)
        logdialog.LogDialog()

if __name__ == "__main__":
    app = PigeonPlanner()

    import pigeonplanner.mainwindow as main

    try:
        pigeonplanner = main.MainWindow(app.options)
        gtk.main()
    except KeyboardInterrupt:
        pass
    except:
        raise

