#!/usr/bin/env python

##########################################################################
#                                                                        #
#  This program is free software; you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation; version 2 of the License.               #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
##########################################################################

from sonet.models import get_contributions_table
from sqlalchemy import select, func

import logging
import time
from base64 import b64decode
from zlib import decompress
from wbin import deserialize

from django.utils.encoding import smart_str

import sonet.mediawiki as mwlib
from sonet.lib import find_open_for_this_file

def user_iter(lang = 'en', paginate=10000000):
    contrib, conn = get_contributions_table()

    count_query = select([func.count(contrib.c.id)],
               contrib.c.lang == lang)
    s = select([contrib],
                contrib.c.lang == lang).order_by(
                    contrib.c.id).limit(paginate)

    count = conn.execute(count_query).fetchall()[0][0]

    #print >>sys.stderr, 'PAGES:', count

    for offset in xrange(0, count, paginate):
        rs = conn.execute(s.offset(offset))
        for row in rs:
            ## row is a RowProxy object: supports dict and list methods
            ## convert it to dict to use with csv.DictWriter
            v = dict(row)
            del v['id']
            del v['lang']
            v['namespace_edits'] = deserialize(decompress(b64decode(
                v['namespace_edits']
            ))) if v['namespace_edits'] is not None else None
            yield v

def prepare_data(namespaces):
    for user in user_iter():
        if user['namespace_edits'] is None:
            user['namespace_edits'] = [0,]*len(namespaces)
        for i, namespace_edit in enumerate(user['namespace_edits']):
            user[namespaces[i]] = namespace_edit
        del user['namespace_edits']

        ## smart_str to manage unicode
        user['username'] = smart_str(user['username'])

        ## converts datetime objects to timestamps (seconds elapsed since
        ## 1970-01-01)
        user['first_edit'] = int(time.mktime(user['first_edit'].timetuple()))
        user['last_edit'] = int(time.mktime(user['last_edit'].timetuple()))

        yield user

def get_xml_file():
    from optparse import OptionParser
    op = OptionParser("%prog dump.xml.gz output_file.bz2",
        description="Export User contribution data from database into csv")
    _, args = op.parse_args()
    if len(args) != 2:
        op.error('Missing xml dump file or output file')
    return args[0], args[1]

def main():
    from bz2 import BZ2File
    from csv import DictWriter

    logging.basicConfig(#filename="usercontributions_export.log",
                        stream=sys.stderr,
                        level=logging.DEBUG)
    logging.info('---------------------START---------------------')

    xml, out = get_xml_file()

    deflate, _lineno = find_open_for_this_file(xml)

    if _lineno:
        src = deflate(xml, 51)
    else:
        src = deflate(xml)

    namespaces = [v for _,v in mwlib.get_namespaces(src)]

    fout = BZ2File(out, 'w')

    fields = ['username', 'normal_edits', 'comments_count', 'comments_avg',
              'minor', 'revert', 'npov', 'welcome', 'please', 'thanks',
              'first_edit', 'last_edit']
    fields[2:2] = namespaces
    dw = DictWriter(fout, fields)
    dw.writeheader()

    ## to get only the first 1000 users:
    #from itertools import islice
    #data_iterator = islice(prepare_data(namespaces), 1000)
    data_iterator = prepare_data(namespaces)

    count = 0
    for user in data_iterator:
        dw.writerow(user)

        count += 1
        if not count % 5000:
            logging.info(count)

if __name__ == "__main__":
    main()