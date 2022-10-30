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


import logging
import webbrowser
from threading import Thread

from gi.repository import GLib

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.core import const
from pigeonplanner.core import update

logger = logging.getLogger(__name__)


class UpdateDialog(builder.GtkBuilder):
    def __init__(self, parent, in_background):
        builder.GtkBuilder.__init__(self, "UpdateDialog.ui")
        self._in_background = in_background

        self.widgets.current_label.set_text(const.VERSION)

        self.widgets.window.set_transient_for(parent)
        if not self._in_background:
            self.widgets.window.show()

    def close_window(self, _widget, _event=None):
        self.widgets.window.destroy()

    # noinspection PyMethodMayBeStatic
    def on_download_button_clicked(self, _widget):
        webbrowser.open(const.DOWNLOADURL)

    def on_search_button_clicked(self, _widget):
        self.search_updates()

    def search_updates(self):
        self.widgets.latest_stack.set_visible_child(self.widgets.search_spinner)
        updatethread = Thread(None, self._search_updates_thread, None)
        updatethread.start()

    def _search_updates_thread(self):
        try:
            update_info = update.get_update_info()
        except update.UpdateError as exc:
            GLib.idle_add(self._search_updates_failed, exc)
        else:
            GLib.idle_add(self._search_updates_finished, update_info)

    def _search_updates_finished(self, update_info):
        logger.debug(update_info.message)
        self.widgets.latest_stack.set_visible_child(self.widgets.latest_label)
        self.widgets.latest_label.set_text(update_info.latest_version)
        self.widgets.message_label.set_text(update_info.message)
        self.widgets.download_button.set_visible(update_info.update_available)
        if self._in_background and update_info.update_available:
            self.widgets.window.show()

    def _search_updates_failed(self, exc):
        logger.error(exc.message)
        self.widgets.latest_stack.set_visible_child(self.widgets.failed_image)
        self.widgets.message_label.set_text(messages.MSG_CONNECTION_ERROR)
        self.widgets.error_label.set_text("Error message: %s" % exc.message)
        if self._in_background:
            self.widgets.window.show()
