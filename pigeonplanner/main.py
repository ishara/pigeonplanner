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
import logging.handlers
import platform
import argparse
import subprocess

from pigeonplanner.core import const


def get_operating_system():
    operatingsystem = platform.system()
    if operatingsystem == "Windows":
        release, version, csd, ptype = platform.win32_ver()
        distribution = "%s %s" % (release, csd)
    elif operatingsystem == "Linux":
        try:
            distribution = subprocess.check_output(["lsb_release", "-ds"])
            distribution = distribution.decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            distribution = ""
    elif operatingsystem == "Darwin":
        operatingsystem = "Mac OS X"
        release, versioninfo, machine = platform.mac_ver()
        distribution = release
    else:
        distribution = ""
    return operatingsystem, distribution


class Startup:
    def __init__(self):
        self.logger = None

        # Customized exception hook
        self.old_exception_hook = sys.excepthook
        sys.excepthook = self.exception_hook

        # Create the needed configuration folders
        if not os.path.exists(const.PREFDIR):
            os.makedirs(const.PREFDIR, 0o755)
        if not os.path.isdir(const.THUMBDIR):
            os.mkdir(const.THUMBDIR)
        if not os.path.isdir(os.path.join(const.PLUGINDIR, "resultparsers")):
            os.makedirs(os.path.join(const.PLUGINDIR, "resultparsers"))

        # Parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--version", action="version", version="%(prog)s {}".format(const.VERSION))
        parser.add_argument(
            "-d", "--debug", action="store_true", dest="debug", help="Print debug messages to the console"
        )
        parser.add_argument(
            "-t", "--tab", type=int, help="select this tab on startup", default=0
        )
        self.cmdline_args = parser.parse_args()
        self._loglevel = logging.DEBUG if self.cmdline_args.debug else logging.WARNING

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

        if language in ("def", "Default", None):
            if const.WINDOWS:
                import ctypes

                windll = ctypes.windll.kernel32
                cid = windll.GetUserDefaultUILanguage()
                language = locale.windows_locale[cid]
                detection_type = "windll"
            else:
                try:
                    language = os.environ["LANG"]
                    detection_type = "$LANG"
                except KeyError:
                    language = locale.getlocale()[0]
                    if not language:
                        try:
                            language = locale.getdefaultlocale()[0] + ".UTF-8"
                            detection_type = "getdefaultlocale()"
                        except (TypeError, ValueError):
                            language = "C"
                            detection_type = "fallback"
                    else:
                        language = language + ".UTF-8"
                        detection_type = "getlocale()"
            self.logger.debug("Detected language from %s: %s", detection_type, language)
        else:
            language = locale.normalize(language).split(".")[0] + ".UTF-8"
            self.logger.debug("Language from config: %s", language)

        os.environ["LANG"] = language
        os.environ["LANGUAGE"] = language

        gettext.bindtextdomain(localedomain, localedir)
        gettext.bind_textdomain_codeset(localedomain, "UTF-8")
        gettext.textdomain(localedomain)
        gettext.install(localedomain, localedir)
        try:
            locale.bindtextdomain(localedomain, localedir)
        except AttributeError:
            if const.WINDOWS:
                if gtk_ui:
                    # For some reason we need to import GTK before loading the
                    # libintl DLL. Do this by importing our own main GTK module
                    # so all checks are done as well.
                    from pigeonplanner.ui import gtkmain

                from ctypes import cdll

                cdll.msvcrt._putenv("LANG=%s" % language)  # noqa
                cdll.msvcrt._putenv("LANGUAGE=%s" % language)  # noqa

                # locale has no bindtextdomain on Windows, try to fall back to libintl
                try:
                    libintl = cdll.LoadLibrary("libintl-8.dll")
                except OSError:
                    self.logger.warning("Can not find libintl-8.dll for localisation.")
                    return
                else:
                    # Important! libintl only accepts encoded strings and will fail silently otherwise.
                    libintl.bindtextdomain(localedomain.encode("utf-8"), localedir.encode("utf-8"))
                    libintl.bind_textdomain_codeset(localedomain.encode("utf-8"), "UTF-8")
                    libintl.textdomain(localedomain.encode("utf-8"))
            else:
                # Most likely on macOS and safe to ignore
                pass

    def setup_logging(self):
        """
        Setup logging and add some debug messages
        """

        # Capture warnings and add them to the log, useful for GTK warnings.
        logging.captureWarnings(True)

        formatter = logging.Formatter(const.LOG_FORMAT)
        handler = logging.handlers.RotatingFileHandler(const.LOGFILE, encoding="UTF-8", backupCount=4)
        handler.doRollover()
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
    from pigeonplanner.core import config

    loaded_config = config.load()

    app = Startup()
    app.setup_locale(gtk_ui)

    missing_libs = []
    try:
        # The initial migration uses a feature which had a bug <3.5.1
        # https://github.com/coleifer/peewee/issues/1645
        import peewee  # noqa

        if not tuple([int(x) for x in peewee.__version__.split(".")]) >= (3, 5, 1):
            raise ImportError
    except ImportError:
        app.logger.error("Peewee >= 3.5.1 not found!")
        missing_libs.append("Peewee >= 3.5.1")
    else:
        from pigeonplanner.database import manager

        manager.init_manager()

    logging.getLogger("urllib3").setLevel(logging.WARNING)

    if gtk_ui:
        from pigeonplanner.ui import gtkmain

        gtkapp = gtkmain.Application(missing_libs, loaded_config, app.cmdline_args)
        gtkapp.run()


if __name__ == "__main__":
    run()
