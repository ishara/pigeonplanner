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
import logging
import webbrowser

import gtk
import gobject

from pigeonplanner import const


WIN32 = sys.platform.startswith("win")


class  NullFile(object):
    def __init__(self, *arg, **kwarg):
        pass

    def write(self, data):
        pass

    def close(self):
        pass


class Startup(object):
    def __init__(self):
        self.db = None
        self.parser = None
        self.logger = None

        # Customized exception hook
        self.old_exception_hook = sys.excepthook
        sys.excepthook = self.exception_hook

        # py2exe detection
        py2exe = False
        if WIN32 and hasattr(sys, 'frozen'):
            py2exe = True
	
        # Disable py2exe log feature
        if WIN32 and py2exe:
            try:
                sys.stdout = open("nul", "w")
                sys.stderr = open("nul", "w")
            except IOError:
                # "nul" doesn't exist, use our own class
                sys.stdout = NullFile()
                sys.stderr = NullFile()

        # Detect if program is running for the first time
        self.firstrun = not os.path.isdir(const.PREFDIR)

        # Initialize options
        from pigeonplanner import options
        self.options = options.GetOptions()

    def setup_locale(self):
        from pigeonplanner import intl

        language = self.options.language
        intl.install(const.DOMAIN, const.LANGDIR, language)

    def setup_logging(self):
        """
        Setup logging and add some debug messages
        """

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
        if WIN32:
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
        if self.firstrun:
            self.logger.debug("First run")

    def setup_theme(self):
        # Set theme
        if WIN32 and os.path.exists('.\\share\\themes'):
            themes = os.listdir('.\\share\\themes')
            themefile = os.path.join('.\\share\\themes',
                                     themes[self.options.theme],
                                     'gtk-2.0\\gtkrc')
            gtk.rc_parse(themefile)

        # Register custom stock icons
        from pigeonplanner import common

        common.create_stock_button([
                ('icon_pedigree_detail.png', 'pedigree-detail', _('Pedigree')),
                ('icon_email.png', 'email', _('E-mail')),
                ('icon_send.png', 'send', _('Send')),
                ('icon_report.png', 'report', _('Report')),
            ])

    def setup_database(self):
        """
        Setup the database and check if it needs an update
        """

        from pigeonplanner import database

        self.db = database.DatabaseOperations()
        self.db.check_schema()

    def setup_pigeons(self):
        """
        Setup the pigeon parser object which will hold all the pigeons and
        build the image thumbnails if needed.
        """

        from pigeonplanner import pigeonparser

        self.parser = pigeonparser.PigeonParser(self.db)
        self.parser.build_pigeons()
        if not os.path.isdir(const.THUMBDIR):
            from pigeonplanner import common
            self.logger.debug("Make thumbnail folder and building thumbnails")
            os.mkdir(const.THUMBDIR)
            common.build_thumbnails(self.parser.pigeons)

    def search_updates(self):
        from pigeonplanner import update

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
        from pigeonplanner.ui.dialogs import MessageDialog

        d = MessageDialog(const.QUESTION, messages.MSG_UPDATE_NOW, None)
        if d.yes:
            webbrowser.open(const.DOWNLOADURL)

        return False

    def exception_hook(self, type_, value, tb):
        import traceback

        # Just fallback when an exception is raised before locale setup
        try:
            s = ""
            _(s)
        except NameError:
            self.setup_locale()

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
        logdialog.LogDialog(self.db)

        if self.db is not None:
            self.db.close()

