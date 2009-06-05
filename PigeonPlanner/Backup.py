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
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        makezip(infolder, zip, True)
        zip.close()
    except RuntimeError:
        if os.path.exists(outfile):
            os.unlink(outfile)
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_STORED)
        makezip(infolder, zip, True)
        zip.close()
#        print "    Unable to compress zip file contents."

def makezip(path, zip, keep):
    path = os.path.normpath(path)

    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            if not file.endswith('.lock'):
#                print "Adding %s..." % os.path.join(path, dirpath, file)
                try:
                    if keep:
                        zip.write(os.path.join(dirpath, file),
                        os.path.join(os.path.basename(path), os.path.join(dirpath, file)[len(path)+len(os.sep):]))
                    else:
                        zip.write(os.path.join(dirpath, file),            
                        os.path.join(dirpath[len(path):], file)) 

                except Exception, e:
                    print "    Error adding %s: %s" % (file, e)

def restore_backup(infile):
    if not infile.endswith('PigeonPlannerBackup.zip'):
        return

    outfol = Const.HOMEDIR

    zip = zipfile.ZipFile(infile, 'r')
    unzip(outfol, zip)
    zip.close()

def unzip(path, zip):
    if not isdir(path):
        os.makedirs(path)    

    for each in zip.namelist():
        if not each.endswith('/'): 
            root, name = split(each)
            directory = normpath(join(path, root))
            if not isdir(directory):
                os.makedirs(directory)
            file(join(directory, name), 'wb').write(zip.read(each))


