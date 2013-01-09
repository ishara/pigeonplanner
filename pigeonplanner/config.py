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
import json
import copy
import time
import logging
logger = logging.getLogger(__name__)

import const


class Config(object):
    def __init__(self):
        self.default = {}
        self.settings = {}
        self.reset()

    def reset(self, key=None):
        if key is None:
            section = None
            setting = None
        elif "." in key:
            section, setting = key.split(".", 1)
        else: # key is not None and doesn't have a "."
            section = key
            setting = None
        # Now, do the reset on the right parts:
        if section is None:
            self.settings = {}
            for section in self.default:
                self.settings[section] = {}
                for setting in self.default[section]:
                    self.settings[section][setting] = \
                        copy.deepcopy(self.default[section][setting])
        elif setting is None:
            self.settings[section] = {}
            for setting in self.default[section]:
                self.settings[section][setting] = \
                    copy.deepcopy(self.default[section][setting])
        else:
            self.settings[section][setting] = \
                copy.deepcopy(self.default[section][setting])

    def load(self):
        if os.path.exists(const.CONFIGFILE):
            with open(const.CONFIGFILE) as cfg:
                try:
                    self.settings = json.load(cfg)
                except ValueError:
                    # Config is still in old format
                    logger.debug('Convert old config file to new format')
                    import ConfigParser
                    parser = ConfigParser.RawConfigParser()
                    # Reset the file pointer
                    cfg.seek(0)
                    parser.readfp(cfg)
                    cfg_transform = [
                            ('options.check-for-updates',
                                parser.getboolean, 'Options', 'update'),
                            ('options.language',
                                parser.get, 'Options', 'language'),
                            ('interface.arrows',
                                parser.getboolean, 'Options', 'arrows'),
                            ('interface.stats',
                                parser.getboolean, 'Options', 'stats'),
                            ('interface.theme',
                                parser.getint, 'Options', 'theme'),
                            ('interface.toolbar',
                                parser.getboolean, 'Options', 'toolbar'),
                            ('interface.statusbar',
                                parser.getboolean, 'Options', 'statusbar'),
                            ('interface.window-x',
                                parser.getint, 'Window', 'window_x'),
                            ('interface.window-y',
                                parser.getint, 'Window', 'window_y'),
                            ('interface.window-w',
                                parser.getint, 'Window', 'window_w'),
                            ('interface.window-h',
                                parser.getint, 'Window', 'window_h'),
                            ('backup.automatic-backup',
                                parser.getboolean, 'Backup', 'backup'),
                            ('backup.interval',
                                parser.getint, 'Backup', 'interval'),
                            ('backup.location',
                                parser.get, 'Backup', 'location'),
                            ('backup.last',
                                parser.getfloat, 'Backup', 'last'),
                            ('columns.pigeon-name',
                                parser.getboolean, 'Columns', 'name'),
                            ('columns.pigeon-colour',
                                parser.getboolean, 'Columns', 'colour'),
                            ('columns.pigeon-sex',
                                parser.getboolean, 'Columns', 'sex'),
                            ('columns.pigeon-strain',
                                parser.getboolean, 'Columns', 'strain'),
                            ('columns.pigeon-status',
                                parser.getboolean, 'Columns', 'status'),
                            ('columns.pigeon-loft',
                                parser.getboolean, 'Columns', 'loft'),
                            ('columns.result-coef',
                                parser.getboolean, 'Columns', 'coef'),
                            ('columns.result-sector',
                                parser.getboolean, 'Columns', 'sector'),
                            ('columns.result-category',
                                parser.getboolean, 'Columns', 'category'),
                            ('columns.result-type',
                                parser.getboolean, 'Columns', 'type'),
                            ('columns.result-weather',
                                parser.getboolean, 'Columns', 'weather'),
                            ('columns.result-wind',
                                parser.getboolean, 'Columns', 'wind'),
                            ('columns.result-comment',
                                parser.getboolean, 'Columns', 'comment'),
                            ('printing.general-paper',
                                parser.getint, 'Printing', 'paper'),
                            ('printing.pedigree-layout',
                                parser.getint, 'Printing', 'layout'),
                            ('printing.pedigree-name',
                                parser.getboolean, 'Printing', 'pigName'),
                            ('printing.pedigree-colour',
                                parser.getboolean, 'Printing', 'pigColour'),
                            ('printing.pedigree-sex',
                                parser.getboolean, 'Printing', 'pigSex'),
                            ('printing.pedigree-extra',
                                parser.getboolean, 'Printing', 'pigExtra'),
                            ('printing.result-colnames',
                                parser.getboolean, 'Printing', 'resColumnNames'),
                            ('printing.result-date',
                                parser.getboolean, 'Printing', 'resDate'),
                            ('printing.user-name',
                                parser.getboolean, 'Printing', 'perName'),
                            ('printing.user-address',
                                parser.getboolean, 'Printing', 'perAddress'),
                            ('printing.user-phone',
                                parser.getboolean, 'Printing', 'perPhone'),
                            ('printing.user-email',
                                parser.getboolean, 'Printing', 'perEmail'),
                        ]
                    for new, method, old_section, old_option in cfg_transform:
                        try:
                            old = method(old_section, old_option)
                        except:
                            logger.debug('Skipping option %s.%s' %
                                                    (old_section, old_option))
                            continue
                        self.set(new, old)

    def save(self, default=False):
        if not os.path.exists(const.CONFIGFILE):
            if not os.path.exists(const.PREFDIR):
                os.makedirs(const.PREFDIR, 0755)

        with open(const.CONFIGFILE, 'w') as cfg:
            settings = self.settings if not default else self.default
            json.dump(settings, cfg, indent=4)

    def get(self, key):
        section, setting = key.split(".", 1)
        return self.settings[section][setting]

    def set(self, key, value):
        section, setting = key.split(".", 1)
        if (setting in self.settings[section] and 
            self.settings[section][setting] == value):
            # Do nothing if existed and is the same
            pass
        else:
            # Set the value:
            self.settings[section][setting] = value

    def register(self, key, default):
        section, setting = key.split(".", 1)
        if section not in self.settings:
            self.settings[section] = {}
        if section not in self.default:
            self.default[section] = {}
        # Add the default value to settings, if not exist:
        if setting not in self.settings[section]:
            self.settings[section][setting] = default
        # Set the default, regardless:
        self.default[section][setting] = copy.deepcopy(default)


default_config = [
                ('options.check-for-updates', True),
                ('options.language', 'def'),
                ##('options.format-coef', '%(place)s / %(out)s * 100'),
                ##('options.format-date', '%Y-%m-%d'),

                ('interface.arrows', False),
                ('interface.stats', False),
                ('interface.theme', 1),
                ('interface.toolbar', True),
                ('interface.statusbar', True),
                ('interface.window-x', 0),
                ('interface.window-y', 0),
                ('interface.window-w', 1),
                ('interface.window-h', 680),

                ('backup.automatic-backup', True),
                ('backup.interval', 30),
                ('backup.location', const.HOMEDIR),
                ('backup.last', time.time()),

                ('columns.pigeon-name', True),
                ('columns.pigeon-colour', False),
                ('columns.pigeon-sex', False),
                ('columns.pigeon-strain', False),
                ('columns.pigeon-status', False),
                ('columns.pigeon-loft', False),
                ('columns.result-coef', True),
                ('columns.result-sector', True),
                ('columns.result-category', True),
                ('columns.result-type', True),
                ('columns.result-weather', True),
                ('columns.result-wind', True),
                ('columns.result-comment', True),

                ('printing.general-paper', 0),
                ('printing.pedigree-layout', 0),
                ('printing.pedigree-box-colour', False),
                ('printing.pedigree-name', True),
                ('printing.pedigree-colour', True),
                ('printing.pedigree-sex', True),
                ('printing.pedigree-extra', True),
                ('printing.pedigree-image', False),
                ('printing.pigeon-colnames', True),
                ('printing.pigeon-sex', True),
                ('printing.result-colnames', True),
                ('printing.result-date', False),
                ('printing.user-name', True),
                ('printing.user-address', True),
                ('printing.user-phone', True),
                ('printing.user-email', False),
        ]

CONFIG = Config()
get = CONFIG.get
set = CONFIG.set
register = CONFIG.register
save = CONFIG.save
load = CONFIG.load

for option, value in default_config:
    register(option, value)

load()