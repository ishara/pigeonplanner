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
Interface for sending mails
"""


import urllib.parse

import requests

from pigeonplanner.core import const


class MailError(Exception):
    pass


def send_email(recipient="", sender="", subject="", body="", attachment=None):
    data = {
        "mail_to": recipient,
        "mail_from": sender,
        "subject": urllib.parse.quote(subject),
        "comment": urllib.parse.quote(body)
    }
    files = {}
    if attachment:
        files["file"] = open(attachment, "rb")

    try:
        response = requests.post(const.MAILURL, data=data, files=files)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as exc:
        raise MailError("Error sending email") from exc
