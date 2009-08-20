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


import configuration


class ParsedOptions:
    def __init__(self, theme, column, columntype, columnposition, arrows, toolbar, statusbar, update):
        self.theme = theme
        self.column = column
        self.columntype = columntype
        self.columnposition = columnposition
        self.arrows = arrows
        self.toolbar = toolbar
        self.statusbar = statusbar
        self.update = update


class GetOptions:
    def __init__(self):
        self.conf = configuration.ConfigurationParser()

        self.optionList = []

        p = ParsedOptions(self.conf.getint('Options', 'theme'),
                          self.conf.getboolean('Options', 'column'),
                          self.conf.get('Options', 'columntype'),
                          self.conf.getint('Options', 'columnposition'),
                          self.conf.getboolean('Options', 'arrows'),
                          self.conf.getboolean('Options', 'toolbar'),
                          self.conf.getboolean('Options', 'statusbar'),
                          self.conf.getboolean('Options', 'update'))

        self.optionList = p

    def write_default(self):
        '''
        Write the default configuration file
        '''

        self.conf.generateDefaultFile()
        self.conf.copyNew(default=True)

    def write_options(self, dic):
        '''
        Write the options to the configuration file

        @param dic: a dictionary of options ({section : {key : value}}) 
        '''

        self.conf.generateNewFile(dic)
        self.conf.copyNew(new=True)

    def set_option(self, section, option, value):
        '''
        Set a single option to the configuration file

        @param section: The section of the option
        @param option: The option to change
        @param value: The value for the option
        '''

        self.conf.set_option(section, option, value)
