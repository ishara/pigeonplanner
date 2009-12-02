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
    def __init__(self, theme, arrows, toolbar, statusbar, update, language, runs, backup, interval, location, last, name, colour, sex, loft, strain):
        self.theme = theme
        self.arrows = arrows
        self.toolbar = toolbar
        self.statusbar = statusbar
        self.update = update
        self.language = language
        self.runs = runs
        self.backup = backup
        self.interval = interval
        self.location = location
        self.last = last
        self.colname = name
        self.colcolour = colour
        self.colsex = sex
        self.colloft = loft
        self.colstrain = strain


class GetOptions:
    def __init__(self):
        self.conf = configuration.ConfigurationParser()

        self.optionList = []

        p = ParsedOptions(self.conf.getint('Options', 'theme'),
                          self.conf.getboolean('Options', 'arrows'),
                          self.conf.getboolean('Options', 'toolbar'),
                          self.conf.getboolean('Options', 'statusbar'),
                          self.conf.getboolean('Options', 'update'),
                          self.conf.get('Options', 'language'),
                          self.conf.getint('Options', 'runs'),
                          self.conf.getboolean('Backup', 'backup'),
                          self.conf.getint('Backup', 'interval'),
                          self.conf.get('Backup', 'location'),
                          self.conf.getfloat('Backup', 'last'),
                          self.conf.getboolean('Columns', 'name'),
                          self.conf.getboolean('Columns', 'colour'),
                          self.conf.getboolean('Columns', 'sex'),
                          self.conf.getboolean('Columns', 'loft'),
                          self.conf.getboolean('Columns', 'strain'))

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

