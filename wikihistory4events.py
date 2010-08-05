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
from sonet.mediawiki import PageProcessor, explode_dump_filename, \
     getTranslations, getTags
from sonet import lib


class HistoryEventsPageProcessor(PageProcessor):
    counter_pages = 0
    ## count only revisions 'days' before or after the anniversary
    days = 10
    ## desired pages
    desired_pages = {}
    ## initial date, used for comparison and substraction
    s_date = date(2000, 1, 1)
    __counter = None
    __title = None
    __type = None
    ## Whether the page should be skipped or not, according to its Namespace
    __skip = False
    threshold = 1.
    talkns = None
    __desired = False

    def save_in_django_model(self):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(PROJECT_ROOT+'/django_wikinetwork')
        from django_wikinetwork.wikinetwork.models import WikiEvent

        data = {
            'title': self.__title,
            'lang': self.lang
        }

        results = WikiEvent.objects.filter(**data)
        if not len(results):
            we = WikiEvent(**data)
        else:
            we = results[0]

        we.desired = self.__desired
        we.__setattr__(self.__type, self.__counter[self.__type])
        we.save()
        self.counter_pages += 1

    def set_desired(self, l):
        self.desired_pages = dict(
            [(page, 1) for page in l]
        )

    def is_desired(self, title):
        return self.desired_pages.has_key(title)

    def process_title(self, elem):
        title = elem.text
        a_title = title.split(':')
        if len(a_title) == 1:
            self.__type = 'normal'
            self.__title = a_title[0]
        else:
            if a_title[0] == self.talkns:
                self.__type = 'talk'
                self.__title = a_title[1]
            else:
                self.__skip = True
                return

        self.__desired = self.is_desired(self.__title)
        if not self.__desired or self.threshold < 1.:
            if self.threshold == 0. or random() > self.threshold:
                self.__skip = True
                return

        self.__counter = {
            'normal': {}
            ,'talk': {}
        }

    def process_revision(self, elem):
        if self.__skip: return

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
        self.__counter[self.__type][days] = \
            self.__counter[self.__type].get(days, 0) + 1

        self.count += 1
        if not self.count % 50000:
            print 'PAGES:', self.counter_pages, 'REVS:', self.count

    def process_page(self, _):
        if not self.__skip:
            self.save_in_django_model()
        self.__skip = False

    def process_redirect(self, _):
        self.__skip = True

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
