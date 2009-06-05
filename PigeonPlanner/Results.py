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
import os.path
import cPickle as pickle

import Const


def create_new_db(db):
    if db == 'result':
        dataFile = open(Const.RESULTFILE, 'w')
    elif db == 'data':
        dataFile = open(Const.DATAFILE, 'w')

    pickle.dump({}, dataFile)

    dataFile.close()

def read_all_results():
    resultFile = open(Const.RESULTFILE, 'r')

    results = pickle.load(resultFile)

    resultFile.close()

    return results

def read_result(ring):
    results = []
    dics = read_all_results()

    try:
        results = dics[ring]
    except TypeError: #XXX
        pass
    except KeyError:
#        print "No results for this pigeon"
        pass

    return results

def add_result(ring, new_results):
    results = read_all_results()

    resultFile = open(Const.RESULTFILE, 'w')

    if not results.has_key(ring):
        results[ring] = []

    results[ring].append(new_results)

    pickle.dump(results, resultFile)

    resultFile.close()

def remove_result(ring, date, point, place, out):
    results = read_all_results()

    resultFile = open(Const.RESULTFILE, 'w')

    dics = results[ring]

    try:
        for index, value in enumerate(dics):
            if value['date'] == date and value['point'] == point and value['place'] == place and value['out'] == out:
                del dics[index]
    except:
        print "Error deleting result"

    pickle.dump(results, resultFile)

    resultFile.close()

def read_all_data():
    dataFile = open(Const.DATAFILE, 'r')

    data = pickle.load(dataFile)

    dataFile.close()

    return data

def read_data(datatype):
    items = []

    dics = read_all_data()

    try:
        items = dics[datatype]
    except TypeError: #XXX
        pass
    except KeyError:
#        print "No %s items yet" %datatype
        pass

    return items

def add_data(datatype, item):
    '''

    @param datatype: 'colour', 'racepoint', 'strain', 'loft' or 'sector'
    @param item: The item to add
    '''

    data = read_all_data()

    dataFile = open(Const.DATAFILE, 'w')

    if not data.has_key(datatype):
        data[datatype] = []

    data[datatype].append(item)

    pickle.dump(data, dataFile)

    dataFile.close()


# Create PP folder when not present
if not os.path.exists(Const.PREFDIR):
    os.makedirs(Const.PREFDIR, 0755)

# Create db when not present
if not os.path.exists(Const.RESULTFILE):
    create_new_db('result')

if not os.path.exists(Const.DATAFILE):
    create_new_db('data')


