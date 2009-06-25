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
import sys
import zipfile
from os.path import isdir, join, normpath, split

import Const


def make_backup(folder):
    if not isdir(folder):
        return

    infolder = Const.PREFDIR
    outfile = join(folder, 'PigeonPlannerBackup.zip')

    try:
        zipper = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        makezip(infolder, zipper)
        zipper.close()
    except RuntimeError:
        if os.path.exists(outfile):
            os.unlink(outfile)
        zipper = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_STORED)
        makezip(infolder, zipper)
        zipper.close()

def makezip(path, zipper):
    path = os.path.normpath(path)

    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            if not filename.endswith('.lock'):
                try:
                    zipper.write(os.path.join(dirpath, filename),            
                    os.path.join(dirpath[len(path):], filename)) 
                except Exception, e:
                    print "    Error adding %s: %s" % (filename, e)

def restore_backup(infile):
    if not infile.endswith('PigeonPlannerBackup.zip'):
        return

    outfol = Const.PREFDIR

    zipper = zipfile.ZipFile(infile, 'r')
    unzip(outfol, zipper)
    zipper.close()

def unzip(path, zipper):
    if not isdir(path):
        os.makedirs(path)    

    for each in zipper.namelist():
        if not each.endswith('/'): 
            root, name = split(each)
            directory = normpath(join(path, root))
            if not isdir(directory):
                os.makedirs(directory)
            file(join(directory, name), 'wb').write(zipper.read(each))


