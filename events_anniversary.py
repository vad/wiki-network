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

from datetime import date

## PROJECT LIBS
from sonet.mediawiki import HistoryPageProcessor, explode_dump_filename, \
     get_translations, get_tags, getUsersGroup
from sonet import lib
from sonet.timr import Timr

from sonet.models import get_events_table
from base64 import b64encode
from zlib import compress
from wbin import serialize

class HistoryEventsPageProcessor(HistoryPageProcessor):
    queue = None
    connection = None
    insert = None
    bots = []

    def __init__(self, **kwargs):
        super(HistoryEventsPageProcessor, self).__init__(**kwargs)
        self.queue = []

        events, self.connection = get_events_table()
        self.insert = events.insert()

    def flush(self):
        data = [{'title': page['title'],
                 'lang': self.lang,
                 'talk': (page['type'] == 'talk'),
                 'data': b64encode(compress(serialize(page['counter']))),
                 'desired': page['desired'],
                 'total_editors': page['total_editors'],
                 'bot_editors': page['bot_editors'],
                 'anonymous_editors': page['anon_editors']
                 } for page in self.queue]
        self.connection.execute(self.insert, data)
        self.queue = []

    def save(self):
        data = {
            'title': self._title,
            'type': self._type,
            'desired': self._desired,
            'counter': self._counter,
            'total_editors': self.get_number_of_editors(),
            'bot_editors': self.get_number_of_editors('bot'),
            'anon_editors': self.get_number_of_editors('anonymous')
        }

        self.queue.append(data)
        self.counter_pages += 1

    def set_bots(self):
        self.bots = frozenset(getUsersGroup(lang=self.lang, edits_only=True))

    def process_timestamp(self, elem):
        if self._skip: return

        timestamp = elem.text
        year = int(timestamp[:4])
        month = int(timestamp[5:7])
        day = int(timestamp[8:10])
        revision_time = date(year, month, day)

        self._date = (revision_time - self.s_date).days
        ## default value for self._date is a list where
        ## first element is for total revisions, the second
        ## for revisions made by bot and the last one for
        ## anonymous' revisions
        t = self._counter.get(self._date, [0,0,0])
        t[0] += 1 ## increment total revisions
        self._counter[self._date] = t

        del revision_time, t
        self.count += 1
        if not self.count % 500000:
            self.flush()
            print 'PAGES:', self.counter_pages, 'REVS:', self.count

    def process_username(self, elem):
        try:
            u = elem.text.encode('utf-8')
            ## whether user is a bot or not
            role = 'bot' if u in self.bots else None

            if not u in self._editors:
                self._editors[u] = role

            if role: ## in case of a bot's contribution increment bot's edits
                self._counter[self._date][1] += 1
        except AttributeError:
            pass

    def process_ip(self, elem):
        if not elem.text in self._editors:
            self._editors[elem.text] = 'anonymous'
        ## Contributor is anonymous, thus increments anonymous' contribution
        self._counter[self._date][2] += 1


def main():
    import optparse
    import csv

    p = optparse.OptionParser(
        usage="usage: %prog [options] file desired_list acceptance_ratio")
    p.add_option('-v', action="store_true", dest="verbose", default=False,
                 help="Verbose output (like timings)")
    opts, files = p.parse_args()
    if opts.verbose:
        import sys, logging
        logging.basicConfig(stream=sys.stderr,
                            level=logging.DEBUG)

    if len(files) != 3:
        p.error("Wrong parameters")

    xml = files[0]
    desired_pages_fn = files[1]
    threshold = float(files[2])

    lang, _, _ = explode_dump_filename(xml)
    deflate, _lineno = lib.find_open_for_this_file(xml)

    with open(desired_pages_fn, 'rb') as f:
        desired_pages = [l[0].decode('latin-1') for l in csv.reader(f)
                                        if l and not l[0][0] == '#']

    if _lineno:
        src = deflate(xml, 51)
    else:
        src = deflate(xml)

    translation = get_translations(src)
    tag = get_tags(src, tags='page,title,revision,'+ \
                  'minor,timestamp,redirect,ip,username')

    src.close()
    src = deflate(xml)

    processor = HistoryEventsPageProcessor(tag=tag, lang=lang)
    processor.talkns = translation['Talk']
    processor.threshold = threshold
    processor.set_desired(desired_pages)
    with Timr('Retrieving bots'):
        processor.set_bots()
    print "BEGIN PARSING"
    with Timr('Parsing'):
        processor.start(src)
    processor.flush()


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
