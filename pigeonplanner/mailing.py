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


import os
import os.path
import urllib
import random
import mimetypes
import threading

import gtk
import gobject

import const
import common
import widgets
import messages
from gtkbuilderapp import GtkbuilderApp


def send_email(recipient='', sender='', subject='', body='', attachment=None):
    files = []
    if attachment:
        files.append(("file", open(attachment, "rb")))

    fields = [("mail_to", recipient),
                ("mail_from", sender),
                ("subject", urllib.quote(subject)),
                ("comment", urllib.quote(body))
            ]

    post_multipart(const.MAILURL, fields, files)

def post_multipart(url, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    headers = {'Content-type': content_type, 'Content-length': str(len(body))}

    return common.URLOpen().open(url, body, headers).read().strip()

def encode_multipart_formdata(fields, files):
    BOUNDARY = '----------%s' %''.join([random.choice('0123456789') for x in range(20)])
    body = []
    for (key, value) in fields:
        body.append('--' + BOUNDARY)
        body.append('Content-Disposition: form-data; name="%s"' % key)
        body.append('')
        body.append(value)
    for (key, fd) in files:
        filename = fd.name.split('/')[-1]
        contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        body.append('--%s' % BOUNDARY)
        body.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        body.append('Content-Type: %s' % contenttype)
        fd.seek(0)
        body.append('\r\n' + fd.read())
    body.append('--' + BOUNDARY + '--')
    body.append('')

    return 'multipart/form-data; boundary=%s' % BOUNDARY, '\r\n'.join(body)


class MailDialog(GtkbuilderApp):
    def __init__(self, parent, database, attachment, kind='pdf'):
        GtkbuilderApp.__init__(self, const.GLADEDIALOGS, const.DOMAIN)

        self.maildialog.set_transient_for(parent)

        self.send.set_use_stock(True)
        self.attachment = attachment
        self.sending = False

        if kind == 'pdf':
            self.frame_to.show()
            self.frame_subject.show()
        else:
            import uuid
            self.entry_subject.set_text("Pigeon Planner errorlog [%s]" %str(uuid.uuid1()))
            self.entry_to.set_text(const.REPORTMAIL)
            self.rename.hide()

        self.textbuffer = gtk.TextBuffer()
        self.textview_message.set_buffer(self.textbuffer)

        name, email = '', ''
        if database:
            info = common.get_own_address(database)
            if info:
                name = info['name']
                email = info['email']

        self.entry_name.set_text(name)
        self.entry_mail.set_text(email)
        self.label_attachment.set_text(os.path.basename(attachment))

        if kind == 'log':
            self.entry_name.grab_focus()
            self.entry_name.set_position(-1)
        self.maildialog.show()

    def close_dialog(self, widget=None, event=None):
        if not self.sending:
            try:
                os.remove(self.attachment)
            except:
                pass

            self.maildialog.destroy()

    def on_cancel_clicked(self, widget):
        self.close_dialog()

    def on_close_clicked(self, widget):
        self.close_dialog()

    def on_rename_clicked(self, widget):
        self.entry_attachment.set_text(os.path.basename(self.attachment))

        self.hbox_label.hide()
        self.hbox_entry.show()

    def on_apply_clicked(self, widget):
        filename = self.entry_attachment.get_text()
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        new_attachment = os.path.join(const.TEMPDIR, filename)

        os.rename(self.attachment, new_attachment)

        self.attachment = new_attachment
        self.label_attachment.set_text(filename)

        self.hbox_entry.hide()
        self.hbox_label.show()

    def on_send_clicked(self, widget):
        if not self.entry_to.get_text() or not self.entry_mail.get_text():
            widgets.message_dialog('error', messages.MSG_NEED_EMAIL, self.maildialog)
            return

        self.progressbar.show()
        self.vbox_fields.set_sensitive(False)
        self.action_area.set_sensitive(False)
        th = threading.Thread(group=None, target=self.sendmail_thread, name=None)
        th.start()

    def sendmail_thread(self):
        self.sending = True
        gobject.timeout_add(100, self.pulse_progressbar)

        recipient = self.entry_to.get_text()
        subject = self.entry_subject.get_text()
        body = self.textbuffer.get_text(*self.textbuffer.get_bounds()).strip()
        sender = "%s <%s>" %(self.entry_name.get_text(), self.entry_mail.get_text())

        send_email(recipient, sender, subject, body, self.attachment)

        self.sending = False
        gobject.idle_add(self.send_finished)

    def send_finished(self):
        self.progressbar.hide()
        self.send.hide()
        self.cancel.hide()
        self.close.show()
        self.action_area.set_sensitive(True)
        self.label_result.set_markup("<b>%s</b>" %_("The e-mail has been sent succesfully!"))
        self.label_result.show()

    def pulse_progressbar(self):
        if self.sending:
            self.progressbar.pulse()
            return True

