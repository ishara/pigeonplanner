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


import gettext as orig_gettext


def setup(language):
    import os
    import locale

    import const
    LOCALEDOMAIN = const.DOMAIN
    LOCALEDIR = const.LANGDIR

    if language in ('def', 'Default'):
        language = ''
        try:
            language = os.environ["LANG"]
        except KeyError:
            language = locale.getlocale()[0]
            if not language:
                try:
                    language = locale.getdefaultlocale()[0] + '.UTF-8'
                except TypeError:
                    pass
    else:
        language = locale.normalize(language).split('.')[0] + '.UTF-8'

    if const.OSX and 'LANG' not in os.environ:
        import subprocess
        loc_cmd = ('defaults', 'read', 'NSGlobalDomain', 'AppleLocale')
        process = subprocess.Popen(loc_cmd, stdout=subprocess.PIPE)
        output, error_output = process.communicate()
        language = output.strip() + '.UTF-8'

    os.environ["LANG"] = language
    os.environ["LANGUAGE"] = language

    orig_gettext.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
    orig_gettext.bind_textdomain_codeset(LOCALEDOMAIN, 'UTF-8')
    orig_gettext.textdomain(LOCALEDOMAIN)
    try:
        locale.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
    except AttributeError:
        # locale has no bindtextdomain on Windows, fall back to intl.dll
        if const.WINDOWS:
            from ctypes import cdll
            libintl = cdll.intl
            libintl.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
            libintl.bind_textdomain_codeset(LOCALEDOMAIN, 'UTF-8')
            libintl.textdomain(LOCALEDOMAIN)
            del libintl

def gettext(msgid):
    # Don't return header on empty string
    if msgid.strip() == '':
        return msgid
    return unicode(orig_gettext.gettext(msgid))

