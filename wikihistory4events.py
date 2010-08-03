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

## LXML
from lxml import etree
#import xml.etree.cElementTree as etree

from datetime import date
import sys
import re
import cPickle as pickle
import psycopg2
import wbin

## PROJECT LIBS
import mwlib
#import cmwlib
from lib import SevenZipFileExt
from mwlib import PageProcessor


## TODO: move into the analysis script
def isNearAnniversary(creation, revision, range_):
    """
    >>> isNearAnniversary(date(2001, 9, 11), date(2005, 9, 19), 10)
    True
    >>> isNearAnniversary(date(2001, 1, 1), date(2005, 12, 30), 10)
    True
    >>> isNearAnniversary(date(2001, 12, 31), date(2005, 1, 1), 10)
    True
    """
    isinstance(revision, date) ##WING IDE
    isinstance(creation, date) ##WING IDE
    anniversary = date(revision.year, creation.month, creation.day)
    delta = (revision - anniversary).days
    if abs(delta) <= range_:
        return True
    else:
        if delta > 0:
            anniversary = date(revision.year + 1, creation.month,
                                   creation.day)
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        else:
            anniversary = date(revision.year - 1, creation.month,
                                   creation.day)
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        return False

class HistoryEventsPageProcessor(PageProcessor):
    ## count only revisions 'days' before or after the anniversary
    days = 10
    ## initial date, used for comparison and substraction
    s_date = date(2000,1,1)
    ## counter for desired pages
    ## total revisions vs revisions near the anniversary
    #counter_desired = None
    #counter_normal = {
    #    'talk': {'total': 0, 'anniversary': 0},
    #    'normal': {'total': 0, 'anniversary': 0}
    #}
    desired_pages = []
    counter_pages = 0
    writer = None
    __counter = {
        'normal': {}
        ,'talk': {}
        ,'title': None
    }
    __title = None
    __type = None
    __creation = None
    ## Whether the page should be skipped or not, according to its Namespace
    __skip = None

    def __init__(self, tag=None, lang=None, writer=None):
        PageProcessor.__init__(self, tag=tag, lang=lang)
        if writer:
            self.writer = writer

    def setDesired(self, l):
        self.counter_desired = {}
        for page in l:
            self.desired_pages.append(page)

    def isDesired(self, title):
        return (title in self.desired_pages)
        
    def process_title(self, elem):
        title = elem.text
        a_title = title.split(':')
        if len(a_title) == 1:
            self.__type = 'normal'
            self.__title = a_title[0]
        else:
            if a_title[0] == 'Talk':
                self.__type = 'talk'
                self.__title = a_title[1]
            else:
                self.__skip = True
                return

        self.__counter['title'] = self.__title
        self.__skip = False
        self.__creation = None
        self.counter_pages += 1

        if self.isDesired(title):
            self.__desired = True
        else:
            self.__desired = False

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
        self.__counter[self.__type][days] = self.__counter[self.__type].get(days, 0) + 1

        self.count += 1
        if not self.count % 50000:
            print 'PAGES:', self.counter_pages, 'REVS:', self.count
        #del child

    def process_page(self, elem):
        ## PICKLE
        #self.writer.write(pickle.dumps(self.__counter))
        ## WBIN
        #self.writer.write(wbin.serialize(self.__counter))
        ## DB
        try:
            
            self.writer.execute("""SELECT set_%s(\'%s\', %%(bytea)s)""" % (self.__type, self.__title), {'bytea': psycopg2.Binary(pickle.dumps(self.__counter))})
        except Exception, e:
            print e


def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]
    desired_pages_fn = files[1]
    out_filename = files[2]

    with open(desired_pages_fn) as f:
        lines = f.readlines()
    desired_pages = [l for l in [l.strip() for l in lines] if l and not l[0] == '#']

    lang, date_, type_ = mwlib.explode_dump_filename(xml)

    src = SevenZipFileExt(xml, 51)

    tag = mwlib.getTags(src)

    src.close()
    src = SevenZipFileExt(xml)

    conn = psycopg2.connect("host=sakamoto dbname=research_wiki user=psqladm password=admpsql port=5432")
    writer = conn.cursor()

    processor = HistoryEventsPageProcessor(tag=tag, lang=lang, writer=writer)
    processor.setDesired(desired_pages)

    print "BEGIN PARSING"
    #mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
    #                processor.process)
    mwlib.fast_iter_filter(etree.iterparse(src), {
        tag['title']: processor.process_title,
        tag['revision']: processor.process_revision,
        tag['page']: processor.process_page
    })


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
