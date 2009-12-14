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
if sys.platform.startswith('win'):
    os.environ['PATH'] += ";bin"
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


class  NullFile(object):
    def __init__(self, *arg, **kwarg):
        pass

    def write(self, data):
        pass

    def close(self):
        pass


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
            try:
	            sys.stdout = open("nul", "w")
	            sys.stderr = open("nul", "w")
            except IOError:
                # "nul" doesn't exist, use our own class
	            sys.stdout = NullFile()
	            sys.stderr = NullFile()

        # Options
        import pigeonplanner.options as options
        self.options = options.GetOptions()

        # Locale setup
        currentPath = ''

        if not win32:
            currentPath = os.path.abspath(os.path.dirname(__file__))

        if currentPath.startswith('/usr/bin'):
            LOCALE_PATH = '/usr/share/locale'
        else:
            LOCALE_PATH = os.path.join(currentPath, 'languages')

        APP_NAME = 'pigeonplanner'

        if win32:
            import pigeonplanner.libi18n as libi18n
            libi18n.fix_locale()

        gettext.textdomain(APP_NAME)

        language = self.options.optionList.language
        if language == 'def':
            language = ''

        try:
            langTranslation = gettext.translation(APP_NAME, LOCALE_PATH, [language])
            langTranslation.install()
        except:
            langTranslation = gettext

        locale_error = None
        if win32:
            libi18n._putenv('LC_ALL', language)
        else:
            try:
                locale.setlocale(locale.LC_ALL, locale.normalize(language).split('.')[0]+'.UTF-8')
            except locale.Error, e:
                try:
                    locale.setlocale(locale.LC_ALL, locale.normalize(language))
                except locale.Error, e:
                    locale_error = "Force lang failed: '%(language)s' (%(second)s and %(third)s tested)" % {'language': e, 'second': locale.normalize(language).split('.')[0]+'.UTF-8', 'third': locale.normalize(language)}

        for module in (gettext, gtk.glade):
            module.bindtextdomain(APP_NAME, LOCALE_PATH)
            module.textdomain(APP_NAME)

        __builtin__._ = langTranslation.gettext

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
        if win32:
            self.logger.debug("Current path: %s" % os.getcwd())
            self.logger.debug("Windows version: %s" % ", ".join(str(n) for n in sys.getwindowsversion()))
        else:
            self.logger.debug("Current path: %s" % const.topPath)
        self.logger.debug("Python version: %s" % sys.version)
        self.logger.debug("GTK+ version: %s" % ".".join(str(n) for n in gtk.gtk_version))
        self.logger.debug("PyGTK version: %s" % ".".join(str(n) for n in gtk.pygtk_version))
        if locale_error:
            self.logger.debug("Locale error: %s" % locale_error)
        else:
            if win32:
                loc = libi18n._getlang()
            else:
                loc = locale.getlocale()[0]
            self.logger.debug("Locale: %s" % loc)

        # Set theme
        if win32:
            themes = os.listdir('.\\share\\themes')
            themefile = os.path.join('.\\share\\themes', themes[self.options.optionList.theme], 'gtk-2.0\\gtkrc')
            gtk.rc_parse(themefile)

        # Check database
        import pigeonplanner.database as database

        db = database.DatabaseOperations()

        UPDATE_DB = False
        db_version = db.get_db_version()
        if db_version < 2:
            UPDATE_DB = True

        if UPDATE_DB:
            import pigeonplanner.dbassistant as dbass

            assistant = dbass.DBAssistant(db, db_version)
            gtk.main()

            if assistant.cancelled:
                exit(0)

    def exception_hook(self, type_, value, tb):
        import traceback
        from cStringIO import StringIO

        import pigeonplanner.const as const
        import pigeonplanner.logdialog as logdialog

        file_name = tb.tb_frame.f_code.co_filename
        line_no = tb.tb_lineno
        exception = type_.__name__
        trace = StringIO()
        traceback.print_exception(type_, value, tb, None, trace)
        self.logger.critical("File %s line %i - %s: %s" % (file_name, line_no, exception, value))
        tbtext = ''
        for line in trace.getvalue().split('\n'):
            if line:
                tbtext += "TRACEBACK: %s\n" % line
        logfile = open(const.LOGFILE, "a")
        logfile.write(tbtext)
        logfile.close()
        print trace.getvalue()
        logdialog.LogDialog()

        try:
            os.remove(os.path.join(const.TEMPDIR, 'pigeonplanner.pid'))
        except:
            pass

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

