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


def retrieve_pages(**kwargs):
    import os, sys
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
    sys.path.append('django_wikinetwork')
    from django_wikinetwork.wikinetwork.models import WikiEvent
    from django.core.paginator import Paginator

    return Paginator(WikiEvent.objects.filter(**kwargs).order_by('title','talk'), 50000)
    
def get_days_since(s_date, end_date, range_=10, skipped_days=180, is_anniversary=False):
    """
    Returns the number of days passed between two dates minus the number of days to be skipped (if any).
    If the considered date is an anniversary, count the number of days in the range around the anniversary
    for each year

    >>> get_days_since(date(2001, 9, 11), date(2005, 9, 19), 10, 180, False)
    1289
    >>> get_days_since(date(2001, 1, 1), date(2005, 12, 30), 10, 180, True)
    86
    >>> get_days_since(date(2001, 12, 31), date(2005, 1, 1), 10, 0, False)
    1097
    >>> get_days_since(date(2005, 7, 7), date(2010, 7, 2), 10, 180, True)
    89
    >>> get_days_since(date(2005, 7, 7), date(2010, 7, 15), 10, 180, True)
    103
    >>> get_days_since(date(2005, 7, 7), date(2006, 7, 7), 10, 180, True)
    11
    >>> get_days_since(date(2005, 8, 4), date(2010, 7, 29), 10, 180, True)
    90
    """
    if not is_anniversary:
        return (end_date - s_date).days - skipped_days

    ## counter for days
    days = 0
    for i in range(s_date.year+1,end_date.year+2):
        try:
            ad = date(i, s_date.month, s_date.day)
        except ValueError, e:
            # print e, creation, revision
            ad = date(i, s_date.month, (s_date.day-1))
        if (ad - s_date).days < skipped_days:
            continue
        if (ad - timedelta(range_)) > end_date:
            break
        ## difference in days between the checked date - which is ad - and the creation
        ## of the page
        delta = (end_date - ad).days
        ## if delta is greater than two times the considered range, then the range doubled
        ## elsewhere, if delta is postive means that the dump date is still greater then the anniversary
        ## date in the considered year - i -, hence add the range plus the difference in days.
        ## last case, dump date felt in the range for the considered date, but less than that date. Hence
        ## add the difference between range and delta 
        if delta > (range_ * 2):
            days += (range_ * 2) + 1
        elif not delta:
            days += range_ + 1
        elif delta > 0:
            days += range_ + 1 + delta
        else:
            days += abs(delta)
    
    return days

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
    isinstance(revision, date) ##WING IDE
    isinstance(creation, date) ##WING IDE
    try:
        anniversary = date(revision.year, creation.month, creation.day)
    except ValueError:
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
            except ValueError:
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
            except ValueError:
            #    print e, creation, revision
                anniversary = date(revision.year + 1, creation.month,
                                   (creation.day - 1))
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        return False

def get_first_revision(start_date, data):
    """
    >>> get_first_revision(date(2000,1,1), 2)
    >>> get_first_revision(date(2000,1,1), {51: 'a', 20: 'b', 10: 'c', 123: 'd'})
    datetime.date(2000, 1, 11)
    """
    try:
        return start_date + timedelta(min(data))
    except:
        return None

class EventsProcessor:
    accumulator = {
        'anniversary': {}
        ,'creation': {}
    }
    count = 0
    count_not_desired = {'normal': 0, 'talk': 0}
    count_pages = 0
    counter_desired = {}
    counter_normal = {
        'normal': {'total': 0, 'anniversary': 0}
        ,'talk': {'total': 0, 'anniversary': 0}
    }
    creation_accumulator = {}
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
    
    def __init__(self, lang, range_, skip, dump_date):
        self.lang = lang
        self.range_ = range_
        self.skipped_days = skip
        self.dump_date = dump_date

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
        try:
            self.desired_pages[self.__title]
        except KeyError:
            return False
        else:
            return True
    
    def print_out(self):
        print 'PAGES:', self.count_pages, 'REVS:', self.count
        print 'DESIRED'
        for d,value in self.counter_desired.iteritems():
            print '%s - http://%s.wikipedia.org/wiki/%s - Anniversary: %s' % (d, self.lang,d.replace(' ','_'), self.desired_pages[d])
            for k in ['normal','talk']:
                v = value[k]
                output_line = "  %10s \t Total=%2.15f \t Anniversary=%2.15f \t " % (k,v['total'],v['anniversary'])
                try:
                    output_line += "Anniversary/Total=%2.15f " % (v['anniversary']/v['total'])
                except ZeroDivisionError:
                    output_line += "Anniversary/Total=0"
                output_line += " \t Anniv-total=%2.15f" % (v['anniversary']-v['total'])
                print output_line
            print
        print 'NORMAL'
        print self.counter_normal

    def get_average(self, value, anniversary):
        ## Check if the days passed since the considered date have already
        ## been computed. If so, avoid calculating them once again
        try:
            days = self.accumulator['anniversary'][self.__anniversary_date] if anniversary \
                 else self.accumulator['creation'][self.__creation]
        except KeyError:
            accumulator = self.accumulator['anniversary'] if anniversary else self.accumulator['creation']
            date_ = date(self.__creation.year,self.__anniversary_date.month,self.__anniversary_date.day) \
                  if anniversary else self.__creation
            days = get_days_since(s_date=date_, end_date=self.dump_date, range_=self.range_, 
                                  skipped_days=self.skipped_days, is_anniversary=anniversary)
            accumulator[date_] = days

        try:
            return value / days
        except ZeroDivisionError:
            return value
        
    def get_data(self):
        from django.core.paginator import EmptyPage, InvalidPage
        pages = retrieve_pages(lang=self.lang)
        print "TOTAL:", pages.count,
        print "PAGES:", pages.num_pages
        page = pages.page(1)
        while True:
            for e in page.object_list:
                yield e
            try:
                page = pages.page(page.next_page_number())
            except (EmptyPage, InvalidPage):
                return

    def process(self):
        for r in self.get_data():
            self.__title = r.title
            self.__data = r.data
            self.__desired = self.is_desired()
            self.__type = 'normal' if not r.talk else 'talk'
            if self.__desired:
                print "PROCESSING DESIRED PAGE:", self.__title, self.__type
            self.process_page()
            
        for type_ in ['normal', 'talk']:
            for t in ['anniversary', 'total']:
                try:
                    self.counter_normal[type_][t] /= self.count_not_desired[type_]
                except ZeroDivisionError:
                    continue

    def process_page(self):
            # creation date
            if self.__type == 'normal' or self.__title not in self.creation_accumulator:
                self.__creation = get_first_revision(self.initial_date, self.__data)
                self.creation_accumulator.clear()
                self.creation_accumulator[self.__title] = self.__creation
                
            else:
                self.__creation = self.creation_accumulator[self.__title]
            
            # anniversary_date, if set 
            self.__anniversary_date = self.desired_pages[self.__title] if (self.__desired and self.desired_pages[self.__title]) else self.__creation
            if (self.__desired and not self.desired_pages[self.__title]):
                self.desired_pages[self.__title] = self.__anniversary_date
            
            ## if the page has been created less than one year ago, skip
            if (self.dump_date - self.__creation).days < 365:
                return
            
            if not isinstance(self.__data, dict):
                return

            accumulator = {'anniversary': 0, 'total': 0}

            for d, v in self.__data.iteritems():
                revision = self.initial_date + timedelta(d)
                if (revision - self.__creation).days < self.skipped_days:
                    continue
                if is_near_anniversary(self.__anniversary_date, revision, self.range_):
                    accumulator['anniversary'] += v
                accumulator['total'] += v
                self.count += v

            page_counter = self.counter_desired[self.__title][self.__type] if self.__desired else self.counter_normal[self.__type]
            for t in ['anniversary','total']:
                page_counter[t] += self.get_average(accumulator[t], (t=='anniversary'))
            if not self.__desired:
                self.count_not_desired[self.__type] += 1

            self.count_pages += 1
            if not self.count_pages % 50000:
                print 'PAGES:', self.count_pages, 'REVS:', self.count
                                
                
def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file dump-date")
    p.add_option('-l', '--lang', action="store", dest="lang",help="wikipedia language", default="en")
    p.add_option('-r', '--range', action="store", dest="range_",help="number of days before and after anniversary date", default=10, type="int")
    p.add_option('-s', '--skip', action="store", dest="skip",help="number of days to be skipped", default=180, type="int")
    
    opts, files = p.parse_args()
    
    if not files:
        p.error("Give me a file, please ;-)")

    desired_pages_fn = files[0]
    dumpdate = files[1]

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    ## parsing and extracting desired pages from file
    desired_pages = [l.decode('latin-1') for l in [l.strip() for l in lines] if l and not l[0] == '#']
    ## creating dump date object
    dump = date(int(dumpdate[:4]),int(dumpdate[4:6]),int(dumpdate[6:8]))
    
    ## creating processor
    processor = EventsProcessor(lang=opts.lang, range_=opts.range_, skip=opts.skip, dump_date=dump)
    ## set desired pages
    processor.set_desired(desired_pages)
    ## main process
    processor.process()
    ## print stats and final output
    processor.print_out()

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
