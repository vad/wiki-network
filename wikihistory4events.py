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

#from lxml import etree
import xml.etree.cElementTree as etree

from datetime import datetime
import sys

## PROJECT LIBS
import mwlib
from lib import SevenZipFileExt


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

class HistoryEventsPageProcessor(mwlib.PageProcessor):
    counter_pages = 0
    ## count only revisions 'days' before or after the anniversary
    days = 10
    ## desired pages
    desired_pages = []
    # language of the wikipedia, max length is 3 char
    lang = 'vec'
    talkns = 'Discussion'
    ## initial date, used for comparison and substraction
    s_date = date(2000,1,1)
    __counter = {
        'normal': {}
        ,'talk': {}
    }
    __title = None
    __type = None
    __creation = None
    ## Whether the page should be skipped or not, according to its Namespace
    __skip = None
    
    def saveInDjangoModel(self):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
        sys.path.append('django_wikinetwork')
        from django_wikinetwork.wikinetwork.models import WikiEvent

        data = {}
        data['title'] = self.__title
        data['lang'] = self.lang

        results = WikiEvent.objects.filter(**data)
        if not len(results):
            data['creation'] = self.__creation
            data_model = WikiEvent(**data)
        else:
            data_model = results[0]

        data_model.__setattr__(self.__type, self.__counter[self.__type])
        data_model.save()

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
            if a_title[0] == self.talkns:
                self.__type = 'talk'
                self.__title = a_title[1]
            else:
                self.__skip = True
                return

        self.__skip = False
        self.__creation = None
        self.counter_pages += 1

        self.__desired = self.isDesired(title)

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

        if self.__creation is None:
            if month == 2 and day == 29:
                self.__creation = date(year, 2, 28)
        else:
            self.__creation = revision_time

        days = (revision_time - self.s_date).days
        self.__counter[self.__type][days] = self.__counter[self.__type].get(days, 0) + 1

        self.count += 1
        if not self.count % 50000:
            print 'PAGES:', self.counter_pages, 'REVS:', self.count
        #del child

    def process_page(self, elem):
        self.saveInDjangoModel()

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")

    xml = files[0]
    desired_pages_fn = files[1]

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    desired_pages = [l for l in [l.strip() for l in lines] if l and not l[0] == '#']

    lang, date_, type_ = mwlib.explode_dump_filename(xml)

    src = SevenZipFileExt(xml, 51)

    tag = mwlib.getTags(src)

    src.close()
    src = SevenZipFileExt(xml)

    processor = HistoryEventsPageProcessor(tag=tag, lang=lang)
    processor.setDesired(desired_pages)

    print "BEGIN PARSING"
    mwlib.fast_iter_filter(etree.iterparse(src), {
        tag['title']: processor.process_title,
        tag['revision']: processor.process_revision,
        tag['page']: processor.process_page
    })


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
