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


import os.path
import logging
logger = logging.getLogger(__name__)

import gtk

import const
import common
import builder
import messages
from ui import logdialog
from ui.messagedialog import WarningDialog
from translation import gettext as _


(EXECUTE,
 ERROR,
 CANCEL,
 OK) = range(4)

IMAGES = {EXECUTE: (gtk.STOCK_EXECUTE, _("Executing...")),
          ERROR: (gtk.STOCK_DIALOG_ERROR, 
                  _("Error: see the logfile for more info.")),
          CANCEL: (gtk.STOCK_CANCEL, _("Operation cancelled")),
          OK: (gtk.STOCK_OK, _("Operation completed"))}


class DBWindow(builder.GtkBuilder):
    def __init__(self, database):
        builder.GtkBuilder.__init__(self, "DatabaseTool.ui")

        self.database = database

        # Needed to prevent quitting when a task is busy
        self.__can_quit = True
        # Set the buttons sensitive
        self.__set_buttons()
        # Get the textview buffers
        self.textbuffer_sql = self.textview_sql.get_buffer()
        self.textbuffer_sql.connect('changed', self.on_textbuffer_sql_changed)
        self.textbuffer_output = self.textview_output.get_buffer()

        self.dbwindow.show()

    def quit_program(self, widget, event=None):
        if not self.__can_quit:
            return True

        gtk.main_quit()

    def on_button_optimize_clicked(self, widget):
        logger.debug(common.get_function_name())
        self.__set_image(self.image_optimize, EXECUTE)
        self.database.optimize_db()
        self.__set_image(self.image_optimize, OK)

    def on_button_check_clicked(self, widget):
        logger.debug(common.get_function_name())
        self.__set_image(self.image_check, EXECUTE)
        # Start with an integrity check
        output = self.database.check_db()
        if output[0][0] == 'ok':
            logger.info('Database integrity is ok!')
        else:
            # Errors are returned as multiple rows with a single column
            # [('error1',), ('error2',), ('error3',)]
            logger.error("Database integrity check failed!")
            for error in output:
                logger.error("  %s" %error[0])
            # Don't do remaining checks
            self.__set_image(self.image_check, ERROR)
            return

        # Check some columns so they contain the right data
        ## Check that each pigeon has his sex value set
        rows = self.database.check_empty_column(self.database.PIGEONS, 'sex')
        if len(rows) > 0:
            logger.error("Invalid empty value(s) found!")
            for row in rows:
                data = list(row)
                pindex = data[1]
                band = data[2]
                year = data[3]
                # Remove indexkey and append pindex
                data = data[1:]
                data.append(pindex)
                # Try to detect the correct sex, set a fallback first
                sex = const.YOUNG
                if self.database.has_parent(const.SIRE, band, year) == 0:
                    # No pigeon has it set as sire, try as dam
                    if self.database.has_parent(const.DAM, band, year) > 0:
                        # Found atleast once as dam
                        sex = const.DAM
                else:
                    # Found atleast once as sire
                    sex = const.SIRE
                # Set a value
                data[3] = sex
                # Update this pigeon in the database
                self.database.update_table(self.database.PIGEONS, data, 1, 1)
                logger.debug("Fixed empty sex value for '%s' with value '%s'"
                             %(pindex, sex))

        self.__set_image(self.image_check, OK)

    def on_button_delete_clicked(self, widget):
        logger.debug(common.get_function_name())
        self.__set_image(self.image_delete, EXECUTE)
        if WarningDialog(messages.MSG_REMOVE_DATABASE, self.dbwindow).run():
            try:
                self.database.close()
                os.remove(const.DATABASE)
                for img_thumb in os.listdir(const.THUMBDIR):
                    os.remove(os.path.join(const.THUMBDIR, img_thumb))
            except Exception, msg:
                logger.error("Deleting database failed: %s" % msg)
            self.__set_buttons()
            self.__set_image(self.image_delete, OK)
        else:
            self.__set_image(self.image_delete, CANCEL)

    def on_button_execute_clicked(self, widget):
        logger.debug(common.get_function_name())

        sql = self.textbuffer_sql.get_text(*self.textbuffer_sql.get_bounds())
        sql = sql.strip(" \"';")
        is_select = sql.lower().startswith('select')
        output = self.database.execute(sql, is_select)
        self.textbuffer_output.set_text(str(output))

    def on_button_clear_clicked(self, widget):
        self.textbuffer_sql.set_text("")
        self.textbuffer_output.set_text("")

    def on_textbuffer_sql_changed(self, widget):
        value = widget.get_char_count() == 0
        self.button_execute.set_sensitive(not value)

    def on_button_log_clicked(self, widget):
        logdialog.LogDialog(self.database)

    def __set_image(self, imagewidget, action):
        if action == EXECUTE:
            self.__can_quit = False
            self.dbwindow.set_sensitive(False)
        else:
            self.__can_quit = True
            self.dbwindow.set_sensitive(True)
        while gtk.events_pending():
            gtk.main_iteration()

        image, tooltip = IMAGES[action]
        imagewidget.set_from_stock(image, gtk.ICON_SIZE_BUTTON)
        imagewidget.set_tooltip_text(tooltip)
        while gtk.events_pending():
            gtk.main_iteration()

    def __set_buttons(self):
        value = os.path.exists(const.DATABASE)
        widgets = [self.button_optimize, self.button_check, self.button_delete]
        self.set_multiple_sensitive(widgets, value)

