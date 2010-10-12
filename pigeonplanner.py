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

"""
Pigeon Planner startup script
"""


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
    print "The Python GTK (PyGTK) bindings are required to run this program."
    sys.exit(1)

import gobject
gobject.threads_init()

try:
    import gtk
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


class PigeonPlanner(object):
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

        # Detect if program is running for the first time
        from pigeonplanner import const

        if os.path.isdir(const.PREFDIR):
            firstrun = False
        else:
            firstrun = True

        # Initialize options
        from pigeonplanner import options
        self.options = options.GetOptions()

        # Locale setup
        currentPath = ''

        if not win32:
            currentPath = os.path.abspath(os.path.dirname(__file__))

        if currentPath.startswith('/usr/bin'):
            LOCALE_PATH = '/usr/share/locale'
        else:
            LOCALE_PATH = os.path.join(currentPath, 'languages')

        if win32:
            from pigeonplanner import libi18n
            libi18n.fix_locale()

        language = self.options.optionList.language
        if language == 'def':
            language = ''

        try:
            langTranslation = gettext.translation(const.DOMAIN, LOCALE_PATH,
                                                  [language])
            langTranslation.install()
        except:
            langTranslation = gettext

        locale_error = None
        if win32:
            libi18n._putenv('LC_ALL', language)
        else:
            s = locale.normalize(language).split('.')[0]+'.UTF-8'
            try:
                locale.setlocale(locale.LC_ALL, s)
            except locale.Error, e:
                try:
                    locale.setlocale(locale.LC_ALL, locale.normalize(language))
                except locale.Error, e:
                    locale_error = "Force lang failed: '%s' \
                                    (%s and %s tested)" \
                                    %(e, s, locale.normalize(language))

        if win32:
            # Module locale has no method bindtextdomain on MS Windows.
            # Use the gettext library directly through ctypes.
            # Info: https://bugzilla.gnome.org/show_bug.cgi?id=574520
            self.setup_windows_gettext(const.DOMAIN, LOCALE_PATH, "intl.dll")
        else:
            locale.bindtextdomain(const.DOMAIN, LOCALE_PATH)

        gettext.bindtextdomain(const.DOMAIN, LOCALE_PATH)
        gettext.textdomain(const.DOMAIN)

        __builtin__._ = langTranslation.gettext

		# Logging setup
        if os.path.exists(const.LOGFILE):
            if os.path.exists("%s.old" % const.LOGFILE):
                os.remove("%s.old" % const.LOGFILE)
            os.rename(const.LOGFILE, "%s.old" % const.LOGFILE)
        logging.basicConfig(level=logging.DEBUG,
                            format=const.LOG_FORMAT,
                            filename=const.LOGFILE,
                            filemode='w')
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Version: %s" % const.VERSION)
        self.logger.debug("Home path: %s" % const.HOMEDIR)
        self.logger.debug("Prefs path: %s" % const.PREFDIR)
        if win32:
            self.logger.debug("Current path: %s" % os.getcwd())

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
                win_ver = win_versions[ver_format]
            else:
                win_ver = ", ".join(str(n) for n in sys.getwindowsversion())

            self.logger.debug("Windows version: %s" % win_ver)
        else:
            self.logger.debug("Current path: %s" % const.topPath)
        self.logger.debug("Python version: %s" % sys.version)
        self.logger.debug("GTK+ version: %s" % ".".join(str(n) for n in
                                                        gtk.gtk_version))
        self.logger.debug("PyGTK version: %s" % ".".join(str(n) for n in
                                                         gtk.pygtk_version))
        if locale_error:
            self.logger.debug("Locale error: %s" % locale_error)
        else:
            if win32:
                loc = libi18n._getlang()
            else:
                loc = locale.getlocale()[0]
            self.logger.debug("Locale: %s" % loc)
        if firstrun:
            self.logger.debug("First run")

        # Set theme
        if win32 and os.path.exists('.\\share\\themes'):
            themes = os.listdir('.\\share\\themes')
            themefile = os.path.join('.\\share\\themes',
                                     themes[self.options.optionList.theme],
                                     'gtk-2.0\\gtkrc')
            gtk.rc_parse(themefile)

        # Register custom stock icons
        from pigeonplanner import common

        common.create_stock_button([
                ('icon_pedigree_detail.png', 'pedigree-detail', _('Pedigree')),
                ('icon_email.png', 'email', _('E-mail')),
                ('icon_send.png', 'send', _('Send')),
                ('icon_report.png', 'report', _('Report')),
                ('gtk-find', 'view-all', _('View all')),
                ('gtk-execute', 'calculate', _('Calculate')),
                ('gtk-find', 'search-database', _('Search database')),
                ('gtk-properties', 'optimize', _('Optimize')),
                ('gtk-redo', 'backup', _('Backup')),
                ('gtk-undo', 'restore', _('Restore')),
                ('gtk-find', 'check', _('Check now!')),
            ])

        # Check database
        from pigeonplanner import database

        self.db = database.DatabaseOperations()

        # Check if all tables are present
        for s_table, s_columns in self.db.SCHEMA.items():
            if not s_table in self.db.get_tablenames():
                self.logger.info("Adding table '%s'" %s_table)
                self.db.add_table_from_schema(s_table)

        # Check if all columns are present
        for table in self.db.get_tablenames(): # Get all tables again
            columns = self.db.get_columnnames(table)
            if table == 'Pigeons' and 'alive' in columns:
                # This column has been renamed somewhere
                # between version 0.4.0 and 0.6.0
                self.logger.info("Renaming 'alive' column")
                self.db.change_column_name(table)
                # Get all columns again in this table
                columns = self.db.get_columnnames(table)
            for column_def in self.db.SCHEMA[table][1:-1].split(', '):
                column = column_def.split(' ')[0]
                if not column in columns:
                    # Note: no need to show a progressbar. According to the
                    # SQLite website:
                    # The execution time of the ALTER TABLE command is
                    # independent of the amount of data in the table.
                    # The ALTER TABLE command runs as quickly on a table
                    # with 10 million rows as it does on a table with 1 row.
                    self.logger.info("Adding column '%s' to table '%s'"
                                     %(column, table))
                    self.db.add_column(table, column_def)

    def setup_windows_gettext(self, domain, localedir, intl_path):
        import ctypes

        libintl = ctypes.cdll.LoadLibrary(intl_path)
        encoding = sys.getfilesystemencoding()
        libintl.bindtextdomain(domain, localedir.encode(encoding))
        libintl.textdomain(domain)
        libintl.bind_textdomain_codeset(domain, "UTF-8")
        libintl.gettext.restype = ctypes.c_char_p

    def exception_hook(self, type_, value, tb):
        import traceback

        from pigeonplanner import const
        from pigeonplanner.ui import logdialog

        tb = "".join(traceback.format_exception(type_, value, tb))
        print >> sys.stderr, tb

        tbtext = ''
        for line in tb.split('\n'):
            if line:
                tbtext += "TRACEBACK: %s\n" % line
        logfile = open(const.LOGFILE, "a")
        logfile.write(tbtext)
        logfile.close()
        logdialog.LogDialog()

if __name__ == "__main__":
    app = PigeonPlanner()

    from pigeonplanner.ui import mainwindow

    try:
        pigeonplanner = mainwindow.MainWindow(app.options, app.db)
        gtk.main()
    except KeyboardInterrupt:
        pass
    except:
        raise

