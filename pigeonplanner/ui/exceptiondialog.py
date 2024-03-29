# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.
# Parts taken and inspired by Tucan.

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


from gi.repository import Gtk
from gi.repository import GLib

from pigeonplanner.core import const
from pigeonplanner.ui import maildialog


class ExceptionDialog(Gtk.Dialog):
    def __init__(self, errortext):
        Gtk.Dialog.__init__(self)

        self._errortext = errortext

        self._create_dialog()
        self._size = self.get_size()
        self.run()
        self.destroy()

    def report_log(self, _widget):
        maildialog.MailDialog(self, const.LOGFILE, "log")

    def on_expander_activate(self, widget):
        def resize_timeout():
            self.resize(*self._size)
            return False

        # Reverse logic, "expanded" property is set *after* this signal
        if widget.get_expanded():
            # Wait a small amount of time to resize. The expander takes a
            # moment to collapse all widgets and resizing won't work until then.
            GLib.timeout_add(100, resize_timeout)

    def _create_dialog(self):
        self.set_title("")
        self.vbox.set_spacing(4)
        self.set_border_width(12)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.set_spacing(12)
        image = Gtk.Image()
        image.set_from_icon_name("dialog-error", Gtk.IconSize.DIALOG)
        label = Gtk.Label(
            '<span size="larger" weight="bold">%s</span>' % _("Pigeon Planner has experienced an unexpected error")
        )
        label.set_use_markup(True)

        hbox.pack_start(image, False, False, 0)
        hbox.add(label)

        self.vbox.pack_start(hbox, False, False, 4)

        label = Gtk.Label(_("You can help the Pigeon Planner developers by taking the time to report this bug."))
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.CENTER)

        self.vbox.pack_start(label, False, False, 4)

        textview = Gtk.TextView()
        textview.get_buffer().set_text(self._errortext)
        textview.set_border_width(6)
        textview.set_editable(False)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(-1, 240)
        scroll.add(textview)

        expander = Gtk.Expander(label="<b>%s</b>" % _("Error Detail"))
        expander.connect("activate", self.on_expander_activate)
        expander.set_use_markup(True)
        expander.add(scroll)

        self.vbox.pack_start(expander, True, True, 4)

        button_report = Gtk.Button.new_with_label(_("Report"))
        button_report.connect("clicked", self.report_log)
        self.action_area.pack_start(button_report, False, False, 0)
        button_close = Gtk.Button.new_with_label(_("Close"))
        button_close.connect("clicked", lambda w: self.destroy())
        self.action_area.pack_start(button_close, False, False, 0)

        self.show_all()
