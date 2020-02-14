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


import sys
import signal
import logging

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import Gio
    from gi.repository import GLib
    from gi.repository import GObject
except ImportError:
    print("The GTK+ runtime and GObject introspection bindings are required to run this program.")
    sys.exit(0)

from pigeonplanner.core import const

logger = logging.getLogger()
GLib.threads_init()


class GtkLogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        from pigeonplanner.ui import exceptiondialog
        exceptiondialog.ExceptionDialog(record.getMessage())


def setup_logging():
    formatter = logging.Formatter(const.LOG_FORMAT)
    handler = GtkLogHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.CRITICAL)
    logger.addHandler(handler)

    logger.debug("Python version: %s" % ".".join(map(str, sys.version_info[:3])))
    logger.debug("GTK+ version: %s.%s.%s" % (Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION))
    logger.debug("PyGObject version: %s" % ".".join(map(str, GObject.pygobject_version)))
    import peewee
    logger.debug("Peewee version: %s" % peewee.__version__)


def setup_icons():
    from pigeonplanner.ui import utils
    # Register custom stock icons
    utils.create_stock_button([
            ("icon_pedigree_detail.png", "pedigree-detail", _("Pedigree")),
            ("icon_email.png", "email", _("E-mail")),
            ("icon_send.png", "send", _("Send")),
            ("icon_report.png", "report", _("Report")),
            ("icon_columns.png", "columns", "columns"),
        ])

    # Ideally our custom icons should go into icons/hicolor/WxH/<category>, but for
    # simplicity sake we just add the directory that contains them to the search path.
    # This makes sure icons are found in all scenarios, especially running from source
    # where icons aren't installed yet.
    icon_theme = Gtk.IconTheme.get_default()
    icon_theme.append_search_path(const.IMAGEDIR)

    # Set default icon for all windows
    Gtk.Window.set_default_icon_from_file(const.LOGO_IMG)


def setup_custom_style():
    screen = Gdk.Screen.get_default()
    style_context = Gtk.StyleContext()
    provider = Gtk.CssProvider()
    provider.load_from_path(const.CSSFILE)
    style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class Application(Gtk.Application):
    def __init__(self, missing_libs):
        super(Application, self).__init__(application_id="net.launchpad.pigeonplanner",
                                          flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(const.NAME)
        GLib.set_prgname(const.NAME)

        if const.UNIX:
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.quit)

        self._missing_libs = missing_libs
        self._window = None
        self._actions = [
            ("about", True, self.on_about),
            ("quit",  True, self.on_quit),
        ]

    def do_startup(self):
        Gtk.Application.do_startup(self)

        menu = Gio.Menu()
        for action, is_menu_item, callback in self._actions:
            if is_menu_item:
                menu.append(action.capitalize(), "app.%s" % action)
            simple_action = Gio.SimpleAction.new(action, None)
            simple_action.connect("activate", callback)
            self.add_action(simple_action)
        # TODO GTK3: application icon is way too large if menu is attached to title bar
        # self.set_app_menu(menu)

        # Import widgets that are used in GtkBuilder files (no idea why these and not others)
        from pigeonplanner.ui.widgets import statusbar
        from pigeonplanner.ui.widgets import checkbutton
        from pigeonplanner.ui.widgets import latlongentry
        from pigeonplanner.ui.widgets import displayentry

        # Do this as soon as possible to avoid importing files that import a missing module
        self.notify_missing_libs()
        setup_logging()
        setup_icons()
        setup_custom_style()

    def do_activate(self):
        if not self._window:
            from pigeonplanner.ui import mainwindow
            from pigeonplanner.core import config
            self._window = mainwindow.MainWindow(application=self)
            if config.get("options.check-for-updates"):
                from pigeonplanner.ui import updatedialog
                dialog = updatedialog.UpdateDialog(self._window, True)
                dialog.search_updates()

        self._window.present()

    def on_about(self, _action, _param):
        from pigeonplanner.ui import dialogs
        dialogs.AboutDialog(self._window)

    def on_quit(self, _action, _param):
        self.quit()

    def notify_missing_libs(self):
        if len(self._missing_libs) > 0:
            # TODO: create a helppage on the website? Link to PyPI?
            from pigeonplanner.ui.messagedialog import ErrorDialog
            libs_label = "\n".join(self._missing_libs)
            help_label = "Pigeon Planner requires the following libraries to run correctly:"
            ErrorDialog((help_label, libs_label, None))
            self.quit()
