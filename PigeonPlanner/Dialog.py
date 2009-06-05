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


import gtk


def messageDialog(sort, text, parent=None):
    '''
    Display a message dialog.

    @param parent: The parent window
    @param sort: The sort of dialog
    @param text: The text to display
    '''

    if sort == 'error':
        sort = gtk.MESSAGE_ERROR
        buttons = gtk.BUTTONS_OK
    elif sort == 'warning':
        sort = gtk.MESSAGE_WARNING
        buttons = gtk.BUTTONS_YES_NO
    elif sort == 'question':
        sort = gtk.MESSAGE_QUESTION
        buttons = gtk.BUTTONS_YES_NO
    elif sort == 'info':
        sort = gtk.MESSAGE_INFO
        buttons = gtk.BUTTONS_OK

    dialog = gtk.MessageDialog(parent=parent, type=sort, message_format=text, buttons=buttons)
    result = dialog.run()
    if result == -9:
        dialog.destroy()
        return 'no'
    elif result == -8:
        dialog.destroy()
        return 'yes'
    dialog.destroy()
