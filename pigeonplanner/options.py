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
Interface to get and set configuration options
"""


from pigeonplanner import configuration


class GetOptions(object):
    def __init__(self):
        self.conf = configuration.ConfigurationParser()
        self._set_options()

    def update_options(self):
        self.conf.read(self.conf.prefFile)
        self._set_options()

    def _set_options(self):
        self.theme = self.conf.getint('Options', 'theme')
        self.arrows = self.conf.getboolean('Options', 'arrows')
        self.stats = self.conf.getboolean('Options', 'stats')
        self.toolbar = self.conf.getboolean('Options', 'toolbar')
        self.statusbar = self.conf.getboolean('Options', 'statusbar')
        self.update = self.conf.getboolean('Options', 'update')
        self.language = self.conf.get('Options', 'language')
        self.backup = self.conf.getboolean('Backup', 'backup')
        self.interval = self.conf.getint('Backup', 'interval')
        self.location = self.conf.get('Backup', 'location')
        self.last = self.conf.getfloat('Backup', 'last')
        self.colname = self.conf.getboolean('Columns', 'name')
        self.colcolour = self.conf.getboolean('Columns', 'colour')
        self.colsex = self.conf.getboolean('Columns', 'sex')
        self.colloft = self.conf.getboolean('Columns', 'loft')
        self.colstrain = self.conf.getboolean('Columns', 'strain')
        self.paper = self.conf.getint('Printing', 'paper')
        self.layout = self.conf.getint('Printing', 'layout')
        self.perName = self.conf.getboolean('Printing', 'perName')
        self.perAddress = self.conf.getboolean('Printing', 'perAddress')
        self.perPhone = self.conf.getboolean('Printing', 'perPhone')
        self.perEmail = self.conf.getboolean('Printing', 'perEmail')
        self.pigName = self.conf.getboolean('Printing', 'pigName')
        self.pigColour = self.conf.getboolean('Printing', 'pigColour')
        self.pigSex = self.conf.getboolean('Printing', 'pigSex')
        self.pigExtra = self.conf.getboolean('Printing', 'pigExtra')
        self.pigImage = self.conf.getboolean('Printing', 'pigImage')
        self.resCoef = self.conf.getboolean('Printing', 'resCoef')
        self.resSector = self.conf.getboolean('Printing', 'resSector')
        self.resCategory = self.conf.getboolean('Printing', 'resCategory')
        self.resType = self.conf.getboolean('Printing', 'resType')
        self.resWeather = self.conf.getboolean('Printing', 'resWeather')
        self.resWind = self.conf.getboolean('Printing', 'resWind')
        self.resComment = self.conf.getboolean('Printing', 'resComment')
        self.resColumnNames = self.conf.getboolean('Printing', 'resColumnNames')
        self.resDate = self.conf.getboolean('Printing', 'resDate')

    def write_default(self):
        """
        Write the default configuration file
        """

        self.conf.generateDefaultFile()
        self.conf.copyNew(default=True)
        self.update_options()

    def write_options(self, dic):
        """
        Write the options to the configuration file

        @param dic: a dictionary of options ({section : {key : value}}) 
        """

        self.conf.generateNewFile(dic)
        self.conf.copyNew(new=True)
        self.update_options()

    def set_option(self, section, option, value):
        """
        Set a single option to the configuration file

        @param section: The section of the option
        @param option: The option to change
        @param value: The value for the option
        """

        self.conf.set_option(section, option, value)
        self.update_options()

