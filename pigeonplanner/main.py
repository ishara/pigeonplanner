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
This files holds all the data to startup. This needs to be used by the
main Pigeon Planner program and the database tool script.
"""


import os
import os.path
import sys
import locale
import gettext
import logging
import platform
import webbrowser
from optparse import OptionParser
from threading import Thread

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

from pigeonplanner import const


def get_operating_system():
    operatingsystem = platform.system()
    if operatingsystem == "Windows":
        release, version, csd, ptype = platform.win32_ver()
        distribution = "%s %s" % (release, csd)
    elif operatingsystem == "Linux":
        distname, version, nick = platform.linux_distribution()
        distribution = "%s %s" % (distname, version)
    elif operatingsystem == "Darwin":
        operatingsystem = "Mac OS X"
        release, versioninfo, machine = platform.mac_ver()
        distribution = release
    else:
        distribution = ''
    return operatingsystem, distribution


class  NullFile(object):
    def __init__(self, *arg, **kwarg):
        pass

    def write(self, data):
        pass

    def close(self):
        pass


class Startup(object):
    def __init__(self):
        self.logger = None

        # Customized exception hook
        self.old_exception_hook = sys.excepthook
        sys.excepthook = self.exception_hook

        # py2exe detection
        py2exe = False
        if const.WINDOWS and hasattr(sys, 'frozen'):
            py2exe = True
	
        # Disable py2exe log feature
        if const.WINDOWS and py2exe:
            try:
                sys.stdout = open("nul", "w")
                sys.stderr = open("nul", "w")
            except IOError:
                # "nul" doesn't exist, use our own class
                sys.stdout = NullFile()
                sys.stderr = NullFile()

        # Detect if program is running for the first time
        self.firstrun = False
        if not os.path.exists(const.PREFDIR):
            os.makedirs(const.PREFDIR, 0755)
            self.firstrun = True

        # Parse arguments
        parser = OptionParser(version=const.VERSION)
        parser.add_option("-d", action="store_true", dest="debug",
                          help="Print debug messages to the console")
        opts, args = parser.parse_args()
        self._loglevel = logging.DEBUG if opts.debug else logging.WARNING

        if not os.path.isdir(const.THUMBDIR):
            os.mkdir(const.THUMBDIR)

        if not os.path.isdir(os.path.join(const.PLUGINDIR, "resultparsers")):
            os.makedirs(os.path.join(const.PLUGINDIR, "resultparsers"))

        # Always setup logging
        #TODO: find a better (and crossplatform) way
        try:
            self.setup_logging()
        except WindowsError:
            text = "The program or database tool is already running!"
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, text)
            dialog.set_title("Already running - Pigeon Planner")
            dialog.run()
            dialog.destroy()
            raise SystemExit(text)

    def setup_locale(self):
        from pigeonplanner import config
        language = config.get('options.language')
        localedomain = const.DOMAIN
        localedir = const.LANGDIR

        if language in ('def', 'Default'):
            if const.OSX:
                #TODO: get default language
                language = 'C'
            else:
                language = ''
                try:
                    language = os.environ["LANG"]
                except KeyError:
                    language = locale.getlocale()[0]
                    if not language:
                        try:
                            language = locale.getdefaultlocale()[0] + '.UTF-8'
                        except (TypeError, ValueError):
                            pass
        else:
            language = locale.normalize(language).split('.')[0] + '.UTF-8'

        os.environ["LANG"] = language
        os.environ["LANGUAGE"] = language

        gettext.bindtextdomain(localedomain, localedir)
        gettext.bind_textdomain_codeset(localedomain, 'UTF-8')
        gettext.textdomain(localedomain)
        gettext.install(localedomain, localedir, unicode=True)
        try:
            locale.bindtextdomain(localedomain, localedir)
        except AttributeError:
            # locale has no bindtextdomain on Windows, fall back to intl.dll
            if const.WINDOWS:
                from ctypes import cdll
                cdll.msvcrt._putenv('LANG=%s' % language)
                cdll.msvcrt._putenv('LANGUAGE=%s' % language)

                libintl = cdll.intl
                libintl.bindtextdomain(localedomain, localedir)
                libintl.bind_textdomain_codeset(localedomain, 'UTF-8')
                libintl.textdomain(localedomain)
                del libintl

    def setup_logging(self):
        """
        Setup logging and add some debug messages
        """

        if os.path.exists(const.LOGFILE):
            if os.path.exists("%s.old" % const.LOGFILE):
                os.remove("%s.old" % const.LOGFILE)
            os.rename(const.LOGFILE, "%s.old" % const.LOGFILE)
        formatter = logging.Formatter(const.LOG_FORMAT)
        handler = logging.FileHandler(const.LOGFILE, encoding='UTF-8')
        handler.setFormatter(formatter)
        self.logger = logging.getLogger()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(self._loglevel)
        formatter = logging.Formatter(const.LOG_FORMAT_CLI)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        self.logger.info("Version: %s" % const.VERSION)
        self.logger.debug("Home path: %s" % const.HOMEDIR)
        self.logger.debug("Prefs path: %s" % const.PREFDIR)
        self.logger.debug("Current path: %s" % const.ROOTDIR)
        self.logger.debug("Running on: %s %s" % (get_operating_system()))
        self.logger.debug("Python version: %s" % ".".join(str(n) for n in
                                                        sys.version_info[:3]))
        self.logger.debug("GTK+ version: %s" % ".".join(str(n) for n in
                                                        gtk.gtk_version))
        self.logger.debug("PyGTK version: %s" % ".".join(str(n) for n in
                                                         gtk.pygtk_version))
        if self.firstrun:
            self.logger.debug("First run")

    def setup_theme(self):
        from pigeonplanner import config
        # Set theme
        themedir = '.\\share\\themes'
        if const.WINDOWS and os.path.exists(themedir):
            themes = os.listdir(themedir)
            try:
                theme = themes[config.get('interface.theme')]
            except IndexError:
                theme = themes[1]
                config.set('interface.theme', 1)
            themefile = os.path.join(themedir, theme, 'gtk-2.0\\gtkrc')
            gtk.rc_parse(themefile)

        from pigeonplanner import common
        # Register custom stock icons
        common.create_stock_button([
                ('icon_pedigree_detail.png', 'pedigree-detail', _('Pedigree')),
                ('icon_email.png', 'email', _('E-mail')),
                ('icon_send.png', 'send', _('Send')),
                ('icon_report.png', 'report', _('Report')),
                ('icon_columns.png', 'columns', 'columns'),
            ])

        # Set default icon for all windows
        gtk.window_set_default_icon_from_file(os.path.join(const.IMAGEDIR, "icon_logo.png"))

    def setup_database(self):
        """
        Setup the database and check if it needs an update
        """

        from pigeonplanner import database

        if database.session.get_database_version() > database.SCHEMA_VERSION:
            from pigeonplanner import messages
            from pigeonplanner.ui.messagedialog import ErrorDialog
            ErrorDialog(messages.MSG_NEW_DATABASE)
            raise SystemExit()

        changed = database.session.check_schema()
        if changed:
            from pigeonplanner import messages
            from pigeonplanner.ui.messagedialog import InfoDialog
            InfoDialog(messages.MSG_UPDATED_DATABASE)

    def setup_pigeons(self):
        """
        Setup the pigeon parser object which will hold all the pigeons
        """

        from pigeonplanner import pigeonparser

        pigeonparser.parser.build_pigeons()

    def search_updates(self):
        from pigeonplanner.core import update

        try:
            new, msg = update.update()
        except update.UpdateError, exc:
            self.logger.error(exc)
            return

        if new:
            gobject.idle_add(self.update_dialog)
        else:
            self.logger.info("AutoUpdate: %s" %msg)

    def update_dialog(self):
        from pigeonplanner import messages
        from pigeonplanner.ui.messagedialog import QuestionDialog

        if QuestionDialog(messages.MSG_UPDATE_NOW).run():
            webbrowser.open(const.DOWNLOADURL)

        return False

    def exception_hook(self, type_, value, tb):
        import traceback

        tb = "".join(traceback.format_exception(type_, value, tb))
        self.logger.critical("Unhandled exception\n%s" % tb)

        from pigeonplanner.ui import exceptiondialog
        exceptiondialog.ExceptionDialog(tb)


def start_ui():
    app = Startup()
    app.setup_locale()
    app.setup_theme()
    app.setup_database()
    app.setup_pigeons()

    try:
        geopy_log = logging.getLogger("geopy")
        geopy_log.setLevel(logging.ERROR)
        import geopy
        if not geopy.VERSION >= (0, 95, 0):
            raise ValueError
    except (ImportError, ValueError):
        from pigeonplanner.ui.messagedialog import ErrorDialog
        ErrorDialog((_("Pigeon Planner needs geopy 0.95.0 or higher to run."), None, ""))
        return

    try:
        import yapsy
    except ImportError:
        from pigeonplanner.ui.messagedialog import ErrorDialog
        ErrorDialog((_("Pigeon Planner needs Yapsy to run."), None, ""))
        return

    from pigeonplanner import config
    if config.get('options.check-for-updates'):
        updatethread = Thread(None, app.search_updates, None)
        updatethread.start()

    from pigeonplanner.ui import mainwindow
    mainwindow.MainWindow()

    gtk.main()


if __name__ == '__main__':
    start_ui()

