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
import sys
from random import random

## PROJECT LIBS
from sonet.mediawiki import HistoryPageProcessor, explode_dump_filename, \
     getTranslations, getTags
from sonet import lib


class HistoryEventsPageProcessor(HistoryPageProcessor):
    def save_in_django_model(self):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(PROJECT_ROOT+'/django_wikinetwork')
        from django_wikinetwork.wikinetwork.models import WikiEvent

        data = {
            'title': self._title,
            'lang': self.lang
        }

        results = WikiEvent.objects.filter(**data)
        if not len(results):
            we = WikiEvent(**data)
        else:
            we = results[0]

        we.desired = self._desired
        we.__setattr__(self._type, self._counter[self._type])
        we.save()
        self.counter_pages += 1

    def process_revision(self, elem):
        if self._skip: return

        tag = self.tag

        for el in elem:
            if el.tag == tag['timestamp']:
                timestamp = el.text
                break
        year = int(timestamp[:4])
        month = int(timestamp[5:7])
        day = int(timestamp[8:10])
        revision_time = date(year, month, day)

        days = (revision_time - self.s_date).days
        self._counter[self._type][days] = \
            self._counter[self._type].get(days, 0) + 1

        self.count += 1
        if not self.count % 50000:
            print 'PAGES:', self.counter_pages, 'REVS:', self.count

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file desired_list acceptance_ratio")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")

    xml = files[0]
    desired_pages_fn = files[1]
    threshold = float(files[2])

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    desired_pages = [l.decode('latin-1') for l in [l.strip() for l in lines]
                     if l and not l[0] == '#']

    lang, _, _ = explode_dump_filename(xml)

    deflate, _lineno = lib.find_open_for_this_file(xml)

    if _lineno:
        src = deflate(xml, 51)
    else:
        src = deflate(xml)

    translation = getTranslations(src)
    tag = getTags(src, tags='page,title,revision,'+ \
                  'minor,timestamp,redirect')

    src.close()
    src = deflate(xml)

    processor = HistoryEventsPageProcessor(tag=tag, lang=lang)
    processor.talkns = translation['Talk']
    processor.threshold = threshold
    processor.set_desired(desired_pages)

    print "BEGIN PARSING"
    processor.start(src)


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
