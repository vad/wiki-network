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

from __future__ import division
from datetime import date, timedelta
from sonet.mediawiki import is_archive
from sqlalchemy import select, func
from base64 import b64decode
from zlib import decompress
from wbin import deserialize

from sonet.models import get_events_table
from sonet.lib import yyyymmdd_to_datetime


def page_iter(lang = 'en', paginate=10000000, desired=None):
    events, conn = get_events_table()

    count_query = select([func.count(events.c.id)],
               events.c.lang == lang)
    s = select([events.c.title, events.c.data, events.c.talk],
                events.c.lang == lang).order_by(
        events.c.title, events.c.talk).limit(paginate)

    ## searching only desired pages
    if desired:
        s = s.where(events.c.title.in_(desired))
        count_query = count_query.where(events.c.title.in_(desired))

    count = conn.execute(count_query).fetchall()[0][0]

    for offset in xrange(0, count, paginate):
        rs = conn.execute(s.offset(offset))
        for row in rs:
            yield (row[0],
                   deserialize(decompress(b64decode(row[1]))),
                   row[2])

            
def get_days_since(start_date, end_date, anniversary_date=None, range_=10):
    """
    Returns the number of days passed between two dates. If the considered date
    is an anniversary, count the number of days in the range around the 
    anniversary for each year

    >>> get_days_since(date(2001, 9, 11), date(2005, 9, 19), None, 10)
    1470
    >>> get_days_since(date(2010, 9, 11), date(2005, 9, 19), None, 10)
    0
    >>> get_days_since(date(2005, 9, 16), date(2005, 9, 19), None, 10)
    4
    >>> get_days_since(date(2001,9,11),date(2010,7,29),date(2001,9,11),10)
    179
    >>> get_days_since(date(2001,9,22),date(2010,7,29),date(2001,9,11),10)
    168
    >>> get_days_since(date(2001,12,30),date(2002,1,1),date(2001,12,30),50)
    3
    >>> get_days_since(date(2001,1,1),date(2001,12,31),date(2001,6,15),20)
    41
    >>> get_days_since(date(2001,1,1),date(2003,1,1),date(2001,6,15),5)
    22
    >>> get_days_since(date(2006,1,7),date(2006,7,7),date(2005,7,7),10)
    11
    >>> get_days_since(date(2010,2,4),date(2010,7,29),date(1952,8,4),10)
    5
    """
    if start_date > end_date:
        return 0
    if not anniversary_date:
        return (end_date - start_date).days + 1
    
    counter = 0
    for year in range(start_date.year, end_date.year + 1):
        try:
            ad = date(year, anniversary_date.month,anniversary_date.day)
        except ValueError:
            ad = date(year, anniversary_date.month,anniversary_date.day - 1)
            
        ## TODO: introduce dateutil.rrule.between ?
        counter += sum(1 for d in (ad + timedelta(i) 
                        for i in range(-range_,range_+1)) 
                        if (d >= start_date and d <= end_date))
        
    return counter

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
    >>> is_near_anniversary(date(2001, 12, 25), date(2005, 1, 1), 5)
    False
    >>> is_near_anniversary(date(2001, 12, 25), date(2001, 12, 25), 0)
    True
    >>> is_near_anniversary(date(2001, 12, 25), date(2001, 12, 24), 0)
    False
    """
    #year = creation.day if isleap(revision.year) else creation.day

    try:
        anniversary = date(revision.year, creation.month, creation.day)
    except ValueError:
        # print e, creation, revision
        anniversary = date(revision.year, creation.month, (creation.day - 1))
    delta = (revision - anniversary).days
    if abs(delta) <= range_:
        return True
    elif delta > 0:
        try:
            anniversary = date(revision.year + 1, creation.month,
                               creation.day)
        except ValueError:
            anniversary = date(revision.year + 1, creation.month,
                               (creation.day - 1))
        delta = (revision - anniversary).days
        return (abs(delta) <= range_)
    else:
        try:
            anniversary = date(revision.year - 1, creation.month,
                                   creation.day)
        except ValueError:
            anniversary = date(revision.year - 1, creation.month,
                               (creation.day - 1))
        delta = (revision - anniversary).days
        return (abs(delta) <= range_)

def get_first_revision(start_date, data):
    """
    >>> get_first_revision(date(2000,1,1), 2)
    >>> get_first_revision(date(2000,1,1), {51: 'a', 20: 'b', 10: 'c', 123: 'd'})
    datetime.date(2000, 1, 11)
    """
    try:
        return start_date + timedelta(min(data))
    except TypeError:
        return

class EventsProcessor:
    count = 0
    count_desired = []
    count_not_desired = {'normal': 0, 'talk': 0}
    count_pages = 0
    counter_desired = {}
    counter_normal = {
        'normal': {'total': 0, 'anniversary': 0}
        ,'talk': {'total': 0, 'anniversary': 0}
    }
    creation_accumulator = {}
    desired_only = False ## search desired pages only
    desired_pages = {}
    dump_date = None
    initial_date = date(2000,1,1)
    lang = None
    range_ = None
    skipped_days = None
    __anniversary_date = None
    __creation = None
    __data = None
    __desired = None
    __title = None
    __type = None

    def __init__(self, lang, range_, skip, dump_date, desired):
        self.lang = lang
        self.range_ = range_
        self.skipped_days = skip
        self.dump_date = dump_date
        self.desired_only = desired

    def set_desired(self, list_):
        for l in list_:
            # split page's name and page's creation date (if any)
            page = l.split(',')
            if len(page) > 1:
                s = page[1].strip()
                self.desired_pages[page[0]] = \
                    date(int(s[:4]),int(s[5:7]),int(s[8:10]))
            else:
                self.desired_pages[page[0]] = None
            # populate counter_desired dict
            self.counter_desired[page[0]] = {
                'normal': {'total': 0, 'anniversary': 0}
                ,'talk': {'total': 0, 'anniversary': 0}
            }

    def is_desired(self):
        return (self.__title in self.desired_pages)

    def get_average(self, value, anniversary):
        
        s_date = self.__creation + timedelta(self.skipped_days)
        a_date = self.__anniversary_date if anniversary else None
        
        days = get_days_since(start_date=s_date, end_date=self.dump_date,
                              anniversary_date=a_date, range_=self.range_)
        try:
            return value / days
        except ZeroDivisionError:
            return 0

    def process(self):
        desired = self.desired_pages.keys() if self.desired_only else None
        for title, data, talk in page_iter(lang=self.lang, desired=desired):
            ## check whether the page is an archive or not
            ## if so, skip it!
            if is_archive(title):
                continue
            self.__title = title
            self.__data = data
            self.__desired = self.is_desired()
            self.__type = 'normal' if not talk else 'talk'
            if self.__desired and self.__title not in self.count_desired:
                #print "PROCESSING DESIRED PAGE:", self.__title
                self.count_desired.append(self.__title)
            self.process_page()

        for type_ in ('normal', 'talk'):
            for t in ('anniversary', 'total'):
                try:
                    self.counter_normal[type_][t] /= \
                        self.count_not_desired[type_]
                except ZeroDivisionError:
                    continue

    def process_page(self):
        title = self.__title

        ## creation date
        if self.__type == 'normal' or title not in self.creation_accumulator:
            self.__creation = get_first_revision(self.initial_date,
                                                 self.__data)
            ## clear accumulator, previous stored data are not more needed
            ## since pages are ordered by title and talk (hence, if a page has talk
            ## page, then the talk page follows the article page)
            self.creation_accumulator = {title: self.__creation}
        else:
            self.__creation = self.creation_accumulator[title]

        if self.__desired:
            if self.desired_pages[title] is not None:
                self.__anniversary_date = self.desired_pages[title]
            else:
                self.__anniversary_date = self.__creation
                self.desired_pages[title] = self.__anniversary_date
        else:
            self.__anniversary_date = self.__creation

        ## if the page has been created less than one year ago, skip
        ## TODO: 365 - range??
        if (self.dump_date - self.__creation).days < 365:
            return

        anniversary = 0
        total = 0

        for d, v in self.__data.iteritems():
            revision = self.initial_date + timedelta(d)
            if (revision - self.__creation).days < self.skipped_days:
                continue
            if is_near_anniversary(self.__anniversary_date, revision,
                                   self.range_):
                anniversary += v
            total += v
        self.count += total

        page_counter = self.counter_desired[title][self.__type] if \
                     self.__desired else self.counter_normal[self.__type]
        page_counter['anniversary'] += self.get_average(anniversary, True)
        page_counter['total'] += self.get_average(total, False)
        if not self.__desired:
            self.count_not_desired[self.__type] += 1

        self.count_pages += 1
        if not self.count_pages % 50000:
            print 'PAGES:', self.count_pages, 'REVS:', self.count, \
                  'DESIRED:', len(self.count_desired)

    def print_out(self):
        accumulator = {
            'normal': {'total': [], 'anniversary': []}
            ,'talk': {'total': [], 'anniversary': []}
        }
        from numpy import average
        print 'PAGES:', self.count_pages, 'REVS:', self.count
        print 'DESIRED'
        for d, value in self.counter_desired.iteritems():
            print '%s - http://%s.wikipedia.org/wiki/%s - Anniversary: %s' % (
                d, self.lang,d.replace(' ','_'), self.desired_pages[d])
            for k in ['normal','talk']:
                v = value[k]
                accumulator[k]['total'].append(v['total'])
                accumulator[k]['anniversary'].append(v['anniversary'])
                output_line = \
                        "  %10s \t Total=%2.15f \t Anniversary=%2.15f \t " \
                        % (k, v['total'], v['anniversary'])
                try:
                    output_line += "Anniversary/Total=%2.15f " % (
                        v['anniversary'] / v['total'])
                except ZeroDivisionError:
                    output_line += "Anniversary/Total=%2.15f" % (0.)
                output_line += " \t Anniv-total=%2.15f" % (
                    v['anniversary'] - v['total'])
                print output_line
            print
        print 'AVERAGE DESIRED:'
        for k in ['normal','talk']:
            print '%10s' % (k),
            for t in ['total', 'anniversary']:
                l = accumulator[k][t]
                print '\t %s %2.15f' % (t, average(l),),
        print
        print 'NORMAL'
        for k in ['normal','talk']:
            print '%10s' % (k),
            for t in ['total', 'anniversary']:
                print '\t %s %2.15f' % (t, self.counter_normal[k][t],),


def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file dump-date")
    p.add_option('-l', '--lang', action="store", dest="lang",
                 help="wikipedia language", default="en")
    p.add_option('-r', '--range', action="store", dest="range_",
                 help="number of days before and after anniversary date",
                 default=10, type="int")
    p.add_option('-s', '--skip', action="store", dest="skip",
                 help="number of days to be skipped", default=180, type="int")
    p.add_option('-d', '--desired-only', action="store_true", dest='desired',
                 default=False, help='analysis only of desired pages')
    p.add_option('-S', '--silent', action="store_false", dest='verbose',
                 default=True, help='do not print output')

    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")

    desired_pages_fn = files[0]
    dumpdate = files[1]

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    ## parsing and extracting desired pages from file
    desired_pages = [l.decode('latin-1').replace('_',' ') for l in [
        l.strip() for l in lines] if l and not l[0] == '#']

    ## creating dump date object
    dump = yyyymmdd_to_datetime(dumpdate).date()

    ## creating processor
    processor = EventsProcessor(lang=opts.lang, range_=opts.range_,
                                skip=opts.skip, dump_date=dump,
                                desired=opts.desired)

    ## set desired pages
    processor.set_desired(desired_pages)
    ## main process
    processor.process()
    if opts.verbose:
        ## print stats and final output
        processor.print_out()

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', '/tmp/itprof.morail')
    main()
    #import timeit
    #print timeit.timeit("main.is_near_anniversary(date(2001, 9, 11), date(2005, 9, 19), 10)",
    #              "import __main__ as main;from datetime import date")
