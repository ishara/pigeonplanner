# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# File taken and modified from Gtkvd

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
Provides classes for our configuration
"""

import os
import time
import ConfigParser
import logging
logger = logging.getLogger(__name__)

from pigeonplanner import const


class Configuration(object):
    def __init__(self):
        """
        Initialisation.
        """

        self.sections = []
        self.__defineConfiguration()

    def __defineConfiguration(self):
        """
        Adds all the wanted sections and options.
        """

        self.__addSection('Options')
        self.__addOption('Options', 'theme', 2)
        self.__addOption('Options', 'arrows', 'False')
        self.__addOption('Options', 'stats', 'False')
        self.__addOption('Options', 'toolbar', 'True')
        self.__addOption('Options', 'statusbar', 'True')
        self.__addOption('Options', 'update', 'True')
        self.__addOption('Options', 'language', 'def')
        self.__addSection('Window')
        self.__addOption('Window', 'window_x', 0)
        self.__addOption('Window', 'window_y', 0)
        self.__addOption('Window', 'window_w', 1)
        self.__addOption('Window', 'window_h', 720)
        self.__addSection('Backup')
        self.__addOption('Backup', 'backup', 'True')
        self.__addOption('Backup', 'interval', 30)
        self.__addOption('Backup', 'location', const.HOMEDIR)
        self.__addOption('Backup', 'last', time.time())
        self.__addSection('Columns')
        self.__addOption('Columns', 'name', 'True')
        self.__addOption('Columns', 'colour', 'False')
        self.__addOption('Columns', 'sex', 'False')
        self.__addOption('Columns', 'strain', 'False')
        self.__addOption('Columns', 'loft', 'False')
        self.__addSection('Printing')
        self.__addOption('Printing', 'paper', 0)
        self.__addOption('Printing', 'layout', 0)
        self.__addOption('Printing', 'perName', 'True')
        self.__addOption('Printing', 'perAddress', 'True')
        self.__addOption('Printing', 'perPhone', 'True')
        self.__addOption('Printing', 'perEmail', 'False')
        self.__addOption('Printing', 'pigName', 'True')
        self.__addOption('Printing', 'pigColour', 'True')
        self.__addOption('Printing', 'pigSex', 'True')
        self.__addOption('Printing', 'pigExtra', 'True')
        self.__addOption('Printing', 'pigImage', 'False')
        self.__addOption('Printing', 'resCoef', 'True')
        self.__addOption('Printing', 'resSector', 'True')
        self.__addOption('Printing', 'resCategory', 'True')
        self.__addOption('Printing', 'resType', 'True')
        self.__addOption('Printing', 'resWeather', 'True')
        self.__addOption('Printing', 'resWind', 'True')
        self.__addOption('Printing', 'resComment', 'True')
        self.__addOption('Printing', 'resColumnNames', 'True')
        self.__addOption('Printing', 'resDate', 'True')

    def __addSection(self, name):
        """
        Add a section.

        @param name The name of the section.
        """

        section = Section(name)
        self.sections.append(section)

    def __addOption(self, section, name, default):
        """
        Add an option.

        @param section The name of the section the option belongs to.
        @param name The name of the option, this is the 'key'
        """

        option = Option(name, default)
        section = self.findSection(section)
        section.addOption(option)

    def findSection(self, name):
        """
        Returns the section object for the section with the given name.
        """

        for section in self.sections:
            if section.name == name:
                return section

    def getConfiguration(self):
        """
        Returns a list of Sections, each containing its Options.
        """

        return self.sections

class ConfigurationParser(ConfigParser.ConfigParser):
    def __init__(self):
        """
        Initialises the variables, copies new (default) configuration file
        if it does not exist and reads the configuration file.
        """

        ConfigParser.ConfigParser.__init__(self)

        self.prefFile = os.path.join(const.PREFDIR, 'pigeonplanner.cfg')

        configuration = Configuration()
        self.sections = configuration.getConfiguration()

        self.generateDefaultFile()
        self.copyNew()
        self.read(self.prefFile)

    def generateDefaultFile(self):
        """
        Creates the default configurationfile string based on the known
        Section's and Option's.
        """

        self.defaultFile = "#Pigeon Planner configuration file"
        for section in self.sections:
            self.defaultFile += "\n\n"
            self.defaultFile += "[%s]" % section.name
            for option in section.options:
                self.defaultFile += "\n%s = %s" % (option.name,
                                                   option.defaultValue)

    def generateNewFile(self, valueDic):
        """
        Creates a new configuration file based on the given dic.
        """

        self.newFile = "#Pigeon Planner configuration file"
        for section, values in valueDic.items():
            self.newFile += "\n\n"
            self.newFile += "[%s]" % section
            for option, value in valueDic[section].items():
                self.newFile += "\n%s = %s" % (option, value)

    def copyNew(self, new=False, default=False):
        """
        Copies a default configuration file if it does not exist yet.

        @param new: Should we write a new file?
        @param default: Should we write a default file?
        """

        fileToWrite = None

        if new:
            fileToWrite = self.newFile
        else:
            if not os.path.exists(self.prefFile) or default:
                if not os.path.exists(const.PREFDIR):
                    os.makedirs(const.PREFDIR, 0755)
                fileToWrite = self.defaultFile

        if fileToWrite:
            file = open(self.prefFile, 'w')
            file.write(fileToWrite)
            file.close()

    def set_option(self, section, option, value):
        """
        Set a single option to the configuration file

        @param section: The section of the option
        @param option: The option to change
        @param value: The value for the option
        """

        ConfigParser.ConfigParser.set(self, section, option, value)

        file = open(self.prefFile, 'w')
        ConfigParser.ConfigParser.write(self, file)
        file.close()

    def get(self, section, option):
        """
        Overrides the 'get' method from the standard ConfigParser.ConfigParser.
        This one is safer as it uses a default value in case of errors.
        
        @param section The section of the configuration file.
        @param option The option you want the value of.
        @return The value of the option, or the default value in case of error.
        """

        default=None
        for sectionItem in self.sections:
            if sectionItem.name == section:
                for optionItem in sectionItem.options:
                    if optionItem.name == option:
                        default = optionItem.defaultValue

        el = {'option': option,
              'section': section,
              'default': default}

        try:
            value = ConfigParser.ConfigParser.get(self, section, option)
            if value == "":
                raise OptionEmptyError
            return value
        except ConfigParser.NoOptionError:
            logger.warning("The '%(option)s' option is not set in the "
                           "'%(section)s' section of the configuration file, "
                           "using the default '%(default)s'." % el)
            return default
        except OptionEmptyError:
            logger.warning("The value of the '%(option)s' option in the "
                           "'%(section)s' section of the configuration file "
                           "is empty, using the default '%(default)s'." % el)
            return default
        except ConfigParser.NoSectionError:
            logger.warning("There is no section '%(section)s' in the "
                           "configuration file; an error occured parsing its "
                           "option '%(option)s', using the default "
                           "'%(default)s'." % el)

            preffile = open(self.prefFile, 'a')
            preffile.write("\n\n[%s]" %section)
            preffile.close()
            self.read(self.prefFile)

            return default
        except:
            logger.error("There went something wrong parsing the '%(option)s' "
                         "option in the '%(section)s' section of the "
                         "configuration file, using the default "
                         "'%(default)s'." % el)
            return default

class OptionEmptyError(Exception):
    """
    An exception to raise if the value of an option is equal to "".
    """
    def __init__(self):
        Exception.__init__(self)

class Section(object):
    def __init__(self, name, options=None):
        """
        Initialisation.

        @param name The name of the section.
        """

        self.name = name
        self.options = options

    def addOption(self, option):
        """
        Adds the Option to this Section.
        """

        if not self.options:
            self.options = []
        self.options.append(option)

class Option(object):
    def __init__(self, name, defaultValue):
        """
        Initialisation.

        @param name The name of the option.
        @param defaultValue The default value of the option.
        """

        self.name = name
        self.defaultValue = defaultValue

