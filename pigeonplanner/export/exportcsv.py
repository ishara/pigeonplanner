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


import csv
import cStringIO
import codecs

import utils


__all__ = ['ExportCSV']


# Unicode classes taken from http://docs.python.org/library/csv.html
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, dialect=dialect,
                                     quoting=csv.QUOTE_ALL, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow({k:str(v).encode("utf-8") for k,v in row.items()})
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class ExportCSV(object):
    name = 'CSV'
    extension = '.csv'
    filefilter = ('CSV', '*.csv')

    @classmethod
    def run(self, filepath, pigeons):
        with open(filepath, 'wb') as output:
            writer = UnicodeWriter(output, fieldnames=utils.COLS_PIGEON)
            writer.writerow(dict((name, name) for name in utils.COLS_PIGEON))
            for pigeon in pigeons:
                writer.writerow({'pindex': pigeon.pindex,
                                 'band': pigeon.ring,
                                 'year': pigeon.year,
                                 'sex': pigeon.sex,
                                 'visible': pigeon.show,
                                 'status': pigeon.active,
                                 'colour': pigeon.colour,
                                 'name': pigeon.name,
                                 'strain': pigeon.strain,
                                 'loft': pigeon.loft,
                                 'image': pigeon.image,
                                 'sire band': pigeon.sire,
                                 'sire year': pigeon.yearsire,
                                 'dam band': pigeon.dam,
                                 'dam year': pigeon.yeardam,
                                 'extra1': pigeon.extra1,
                                 'extra2': pigeon.extra2,
                                 'extra3': pigeon.extra3,
                                 'extra4': pigeon.extra4,
                                 'extra5': pigeon.extra5,
                                 'extra6': pigeon.extra6})

