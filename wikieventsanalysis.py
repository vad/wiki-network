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

import mwlib
from datetime import date, timedelta


def is_near_anniversary(creation, revision, range_):
    """
    >>> is_near_anniversary(date(2001, 9, 11), date(2005, 9, 19), 10)
    True
    >>> is_near_anniversary(date(2001, 1, 1), date(2005, 12, 30), 10)
    True
    >>> is_near_anniversary(date(2001, 12, 31), date(2005, 1, 1), 10)
    True
    >>> is_near_anniversary(date(2001, 12, 31), date(2005, 1, 14), 15)
    True
    >>> is_near_anniversary(date(2004, 2, 29), date(2005, 3, 7), 10)
    True
    """
    isinstance(revision, date) ##WING IDE
    isinstance(creation, date) ##WING IDE
    try:
        anniversary = date(revision.year, creation.month, creation.day)
    except ValueError, e:
        # print e, creation, revision
        anniversary = date(revision.year, creation.month, (creation.day - 1))
    delta = (revision - anniversary).days
    if abs(delta) <= range_:
        return True
    else:
        if delta > 0:
            try:
                anniversary = date(revision.year + 1, creation.month,
                                   creation.day)
            except ValueError, e:
            #    print e, creation, revision
                anniversary = date(revision.year + 1, creation.month,
                                   (creation.day - 1))
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        else:
            try:
                anniversary = date(revision.year - 1, creation.month,
                                       creation.day)
            except ValueError, e:
            #    print e, creation, revision
                anniversary = date(revision.year + 1, creation.month,
                                   (creation.day - 1))
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        return False

def get_first_revision(start_date, normal, talk):
    sum = []
    for d in (normal, talk):
        if isinstance(d,dict):
            sum += d.keys()

    if len(sum):
        return start_date + timedelta(min(sum))
    else:
        return None

class EventsProcessor:
    s_date = date(2000,1,1)
    count = 0
    counter_pages = 0
    counter_normal = {
        'normal': {'total': 0, 'anniversary': 0}
        ,'talk': {'total': 0, 'anniversary': 0}
    }
    counter__desired = {}
    desired_pages = {}
    range = None
    lang = None
    __title = None
    __desired = None
    __creation = None
    __revisions = None
    
    def __init__(self, lang, range_):
        self.lang = lang
        self.range = range_

    def set_desired(self, list_):
        for l in list_:
            # split page's name and page's creation date (if any)
            page = l.split(',')
            if len(page) > 1:
                self.desired_pages[page[0]] = date.strftime(page[1].strip(),'%Y-%m-%d')
            else:
               self.desired_pages[page[0]] = None
            # populate counter__desired dict
            self.counter__desired[page[0]] = {
                'normal': {'total': 0, 'anniversary': 0}
                ,'talk': {'total': 0, 'anniversary': 0}
            }

    def is__desired(self):
        try:
            self.desired_pages[self.__title]
        except KeyError:
            return False
        else:
            return True

    def retrieve_data(self):
        import os, sys
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
        sys.path.append('django_wikinetwork')
        from django_wikinetwork.wikinetwork.models import WikiEvent

        return WikiEvent.objects.filter(lang=self.lang)

    def print_out(self):
        print 'PAGES:', self.counter_pages, 'REVS:', self.count
        print 'DESIRED'
        for d,v in self.counter__desired.iteritems():
            print d,'\n',v
        print 'NORMAL'
        print self.counter_normal

    def process(self):
        for r in self.retrieve_data():
            self.__title = r.title
            self.__revisions = {
                    'normal': r.normal
                    ,'talk': r.talk
                }
            self.__desired = self.is__desired()
            self.process_page()

    def process_page(self):
            # creation date
            if self.__desired and self.desired_pages[self.__title]:
                self.__creation = self.desired_pages[self.__title]
            else:
                self.__creation = get_first_revision(self.s_date, self.__revisions['normal'], self.__revisions['talk'])

            if not self.__creation:
                print "CREATION NONE:", self.__title
        
            # Iter among normal and talk pages
            for type_, value in self.__revisions.iteritems():

                if not value or type(value) is not dict:
                    continue

                for d, v in value.iteritems():
                    revision = self.s_date + timedelta(d)
                    if (revision - self.__creation).days < 180:
                       continue
                    page_counter = self.counter__desired[self.__title][type_] if self.__desired else self.counter_normal[type_]
                    if is_near_anniversary(self.__creation, revision, self.range):
                        page_counter['anniversary'] += v
                    page_counter['total'] += v
                    self.count += v

            self.counter_pages += 1
            if not self.counter_pages % 5000:
                print 'PAGES:', self.counter_pages, 'REVS:', self.count
                print 'DESIRED'
                for page, counter in self.counter__desired.iteritems():
                    print page
                    print counter
                print 'NORMAL'
                print self.counter_normal

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    p.add_option('-l', '--lang', action="store", dest="lang",help="wikipedia language", default="en")
    p.add_option('-r', '--range', action="store", dest="range_",help="number of days around anniversary date", default=10, type="int")
    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")

    desired_pages_fn = files[0]

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    desired_pages = [l for l in [l.strip() for l in lines] if l and not l[0] == '#']

    processor = EventsProcessor(lang=opts.lang, range_=opts.range_)
    processor.set_desired(desired_pages)
    processor.process()
    processor.print_out()

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
