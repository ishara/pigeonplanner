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
import sys
import locale
import gettext
import logging
import platform
from optparse import OptionParser

from pigeonplanner.core import const


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
        distribution = ""
    return operatingsystem, distribution


class NullFile(object):
    def __init__(self, *arg, **kwarg):
        pass

    def write(self, data):
        pass

    def close(self):
        pass


class Startup(object):
    def __init__(self):
        # Customized exception hook
        self.old_exception_hook = sys.excepthook
        sys.excepthook = self.exception_hook

        # Disable py2exe log feature
        if const.WINDOWS and hasattr(sys, "frozen"):
            try:
                sys.stdout = open(os.devnull, "w")
                sys.stderr = open(os.devnull, "w")
            except IOError:
                # "nul" doesn't exist, use our own class
                sys.stdout = NullFile()
                sys.stderr = NullFile()

        # Create the needed configuration folders
        if not os.path.exists(const.PREFDIR):
            os.makedirs(const.PREFDIR, 0755)
        if not os.path.isdir(const.THUMBDIR):
            os.mkdir(const.THUMBDIR)
        if not os.path.isdir(os.path.join(const.PLUGINDIR, "resultparsers")):
            os.makedirs(os.path.join(const.PLUGINDIR, "resultparsers"))

        # Parse arguments
        parser = OptionParser(version=const.VERSION)
        parser.add_option("-d", action="store_true", dest="debug",
                          help="Print debug messages to the console")
        opts, args = parser.parse_args()
        self._loglevel = logging.DEBUG if opts.debug else logging.WARNING

        # Always setup logging
        try:
            self.setup_logging()
        except WindowsError:
            # Pigeon Planner is already running
            sys.exit(0)

    def setup_locale(self, gtk_ui):
        from pigeonplanner.core import config
        language = config.get("options.language")
        localedomain = const.DOMAIN
        localedir = const.LANGDIR

        if language in ("def", "Default"):
            if const.OSX:
                # TODO: get default language
                language = "C"
            else:
                language = ""
                try:
                    language = os.environ["LANG"]
                except KeyError:
                    language = locale.getlocale()[0]
                    if not language:
                        try:
                            language = locale.getdefaultlocale()[0] + ".UTF-8"
                        except (TypeError, ValueError):
                            pass
        else:
            language = locale.normalize(language).split(".")[0] + ".UTF-8"

        os.environ["LANG"] = language
        os.environ["LANGUAGE"] = language

        gettext.bindtextdomain(localedomain, localedir)
        gettext.bind_textdomain_codeset(localedomain, "UTF-8")
        gettext.textdomain(localedomain)
        gettext.install(localedomain, localedir, unicode=True)
        try:
            locale.bindtextdomain(localedomain, localedir)
        except AttributeError:
            # locale has no bindtextdomain on Windows, fall back to intl.dll
            if const.WINDOWS:
                if gtk_ui and hasattr(sys, "frozen"):
                    # There is a weird issue where cdll.intl throws an exception
                    # when built with py2exe. Apparently GTK links some libraries
                    # on import (details needed!). So this is a little workaround
                    # to detect if we're running a py2exe'd package and the gtk
                    # interface is requested.
                    # Also shut up any code analysers...
                    import gtk; gtk

                from ctypes import cdll
                cdll.msvcrt._putenv("LANG=%s" % language)
                cdll.msvcrt._putenv("LANGUAGE=%s" % language)

                libintl = cdll.intl
                libintl.bindtextdomain(localedomain, localedir)
                libintl.bind_textdomain_codeset(localedomain, "UTF-8")
                libintl.textdomain(localedomain)
                del libintl

    def setup_logging(self):
        """
        Setup logging and add some debug messages
        """

        # Capture warnings and add them to the log, useful for GTK warnings.
        logging.captureWarnings(True)

        if os.path.exists(const.LOGFILE):
            if os.path.exists("%s.old" % const.LOGFILE):
                os.remove("%s.old" % const.LOGFILE)
            os.rename(const.LOGFILE, "%s.old" % const.LOGFILE)
        formatter = logging.Formatter(const.LOG_FORMAT)
        handler = logging.FileHandler(const.LOGFILE, encoding="UTF-8")
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

    def exception_hook(self, type_, value, tb):
        import traceback
        tb = "".join(traceback.format_exception(type_, value, tb))
        self.logger.critical("Unhandled exception\n%s" % tb)


def run(gtk_ui=True):
    app = Startup()
    app.setup_locale(gtk_ui)

    missing_libs = []
    try:
        # The initial migration uses a feature which had a bug <3.5.1
        # https://github.com/coleifer/peewee/issues/1645
        import peewee
        if not tuple([int(x) for x in peewee.__version__.split(".")]) >= (3, 5, 1):
            raise ImportError
    except ImportError:
        app.logger.error("Peewee >= 3.5.1 not found!")
        missing_libs.append("Peewee >= 3.5.1")
    else:
        from pigeonplanner.database import manager
        manager.init_manager()

    if gtk_ui:
        from pigeonplanner.ui import gtkmain
        gtkmain.run_ui(missing_libs)


if __name__ == "__main__":
    run()
