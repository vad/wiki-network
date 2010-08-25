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
import sys

from django.utils.encoding import smart_str

from sonet.models import get_events_table
from sonet import lib


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
    
    print >>sys.stderr, 'PAGES:', count

    for offset in xrange(0, count, paginate):
        rs = conn.execute(s.offset(offset))
        for row in rs:
            yield (row[0],
                   deserialize(decompress(b64decode(row[1]))),
                   row[2])

            
def get_days_since(start_date, end_date, anniversary_date, td_list):
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
        counter += len([1 for d in (ad + td 
                        for td in td_list) 
                        if (d >= start_date and d <= end_date)])
        
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
    count_desired = []
    count_pages = 0
    count_revisions = 0
    creation_accumulator = {}
    desired_only = False ## search desired pages only
    desired_pages = {}
    dump_date = None
    initial_date = date(2000,1,1)
    lang = None
    keys_ = ['article','type_of_page','desired','total_edits',
            'anniversary_edits','n_of_anniversaries',
            'anniversary_edits/total_edits','non_anniversary_edits/total_edits',
            'event_date','first_edit_date','first_edit_date-event_date_in_days']
    last_page = None
    output_file = None
    pages = []
    range_ = None
    sevenzip_process = None
    skipped_days = None
    td_list = None
    threshold = None
    __event_date = None
    __first_edit_date = None
    __data = None
    __desired = None
    __n_of_anniversaries = None
    __title = None
    __type = None

    def __init__(self, **kwargs):
        
        from subprocess import Popen, PIPE        
        
        self.lang = kwargs['lang']
        self.range_ = kwargs['range_']
        self.skipped_days = kwargs['skip']
        self.dump_date = kwargs['dump_date']
        self.desired_only = kwargs['desired']
        self.output_file = kwargs['output_file']
                
        # timedelta list, used in get_days_since
        self.td_list = [timedelta(i) for i in
                        range(-self.range_,self.range_+1)]
        
                
        self.sevenzip_process = Popen(['7z', 'a', '-si', self.output_file + '.7z'],
                              stdin=PIPE, stderr=None)
        
        sys.stdout = self.sevenzip_process.stdin
        print ">".join(self.keys_)

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

    def is_desired(self):
        return (self.__title in self.desired_pages)

    def get_start_date(self):
        
        sd = timedelta(self.skipped_days)
        
        if self.__first_edit_date == self.__event_date:
            s_date = self.__event_date + sd
            
        elif self.__event_date + sd > self.__first_edit_date:
            s_date = self.__event_date + sd
            
        else:
            s_date = self.__first_edit_date
        
        return s_date

    def get_days_since(self):
        s_date = self.get_start_date()
        return get_days_since(start_date=s_date, end_date=self.dump_date,
                                  anniversary_date=self.__event_date, 
                                  td_list=self.td_list)
    
    def get_n_anniversaries(self):
        n = 0
        s_date = self.get_start_date()
        
        for y in range(s_date.year + 1, self.dump_date.year + 1):
            try: 
                d = date(y, self.__event_date.month, self.__event_date.day)
            except ValueError: 
                d = date(y, self.__event_date.month, self.__event_date.day - 1)
    
            if (d >= s_date and d <= self.dump_date):
                n += 1
        
        return n

    def process(self, threshold=1.):
        from random import random
                
        desired = self.desired_pages.keys() if self.desired_only else None
        
        for title, data, talk in page_iter(lang=self.lang, desired=desired):
            ## check whether the page is an archive or not
            ## if it is a link, skip it!
            if is_archive(title):
                continue
            
            ## page's attributes
            self.__title = title
            self.__data = data
            self.__desired = self.is_desired()
            self.__type_of_page = talk ## 0 = article, 1 = talk
            if self.__desired and self.__title not in self.count_desired:
                print >> sys.stderr, "PROCESSING DESIRED PAGE:", self.__title
                self.count_desired.append(self.__title)
                
            if not self.__desired and self.threshold < 1.:
                if threshold == 0. or random() > threshold:
                    self.__skip = True
                else:
                    self.__skip = False
            else:
                self.__skip = False
                
            ## process page
            if not self.__skip: 
                self.process_page()
        
        self.flush()

    def process_page(self):
        
        ## page's (and last page as well) attributes
        title = self.__title
        type_ = 'talk' if self.__type_of_page else 'normal'
        if self.last_page:
            lp_title = self.last_page['article']
            lp_type = 'normal' if self.last_page['type_of_page'] else 'talk'
            lp_edits = self.last_page['total_edits']
        else:
            lp_title = None 
            lp_type = None
            lp_edits = None       

        ## creation date
        self.__first_edit_date = get_first_revision(self.initial_date,
                                                 self.__data)
            
        ## remove pages without talk
        try:
            if type_ == lp_type:
                self.last_page = None
        except IndexError:
            pass

        if self.__desired:
            if self.desired_pages[title] is not None:
                self.__event_date = self.desired_pages[title]
            else:
                self.__event_date = self.__first_edit_date
        else:
            self.__event_date = self.__first_edit_date
            
        ## if the page has been created less than one year ago, skip
        ## TODO: 365 - range??
        if (self.dump_date - self.__first_edit_date).days < 365:
            ## if it is a talk, remove the article page as well
            if type_ == 'talk':
                try:
                    self.last_page = None
                except IndexError:
                    pass
            return

        anniversary = 0
        total = 0
        in_skipped = 0

        for d, v in self.__data.iteritems():
            revision = self.initial_date + timedelta(d)
            if (revision - self.__event_date).days < self.skipped_days:
                in_skipped += v
                continue
            if is_near_anniversary(self.__event_date, revision, self.range_):
                anniversary += v
            total += v
        
        try:
            ann_total_edits = anniversary / total
            not_ann_total_edits = (total - anniversary) / total
        except ZeroDivisionError:
            ann_total_edits = 0.
            not_ann_total_edits = 0.
                    
        dict_ = {
            'article': self.__title,
            'type_of_page': int(not self.__type_of_page),
            'desired': int(self.__desired),
            'total_edits': total,
            'anniversary_edits': anniversary,
            'n_of_anniversaries': self.get_n_anniversaries(),
            'anniversary_edits/total_edits': ann_total_edits,
            'non_anniversary_edits/total_edits': not_ann_total_edits,
            'event_date': self.__event_date,
            'first_edit_date': self.__first_edit_date,
            'first_edit_date-event_date_in_days': (self.__first_edit_date - 
                                                   self.__event_date).days
        }

        if self.last_page and (title == lp_title):
            self.pages.append(self.last_page)
            self.pages.append(dict_)
            self.count_pages += 2
            self.count_revisions += (total + lp_edits)
            self.last_page = None
            if not self.count_pages % 50000:
                self.flush()
        else:
            self.last_page = dict_
        

    def flush(self):
        
        print >> sys.stderr, 'PAGES:', self.count_pages, 'REVS:', \
              self.count_revisions, 'DESIRED:', len(self.count_desired)
        
        for page in self.pages:
            try:
                print '%s>%d>%d>%d>%d>%d>%2.16f>%2.16f>%s>%s>%d' % \
                      (smart_str(page['article']),page['type_of_page'],
                      page['desired'],page['total_edits'],
                      page['anniversary_edits'],page['n_of_anniversaries'],
                      page['anniversary_edits/total_edits'],
                      page['non_anniversary_edits/total_edits'],
                      page['event_date'],page['first_edit_date'],
                      page['first_edit_date-event_date_in_days'])
            except UnicodeEncodeError, e:
                print >> sys.stderr, e, page['article']
                continue
            del page
            
        self.pages = []
        return

    
def create_option_parser():
    from optparse import OptionParser, OptionGroup
    from sonet.lib import SonetOption

    op = OptionParser('%prog [options] file dump-date output-file ratio', 
                      option_class=SonetOption)
    
    op.add_option('-l', '--lang', action="store", dest="lang",
                 help="Wikipedia language (en, it, vec, ...)", default="en")
    op.add_option('-r', '--range', action="store", dest="range_",
                 help="number of days before and after anniversary date",
                 default=10, type="int")
    op.add_option('-s', '--skip', action="store", dest="skip",
                 help="number of days to be skipped", default=180, type="int")
    op.add_option('-d', '--desired-only', action="store_true", dest='desired',
                 default=False, help='analysis only of desired pages')
    
    return op

def main():

    p = create_option_parser()
    opts, files = p.parse_args()

    if len(files) < 4:
        p.error("Bad number of arguments!")

    desired_pages_fn = files[0]
    dumpdate = files[1]
    out_file = files[2]
    threshold = float(files[3])

    with open(desired_pages_fn) as f:
        lines = f.readlines()

    ## parsing and extracting desired pages from file
    desired_pages = [l.decode('latin-1').replace('_',' ') for l in [
        l.strip() for l in lines] if l and not l[0] == '#']

    ## creating dump date object
    dump = lib.yyyymmdd_to_datetime(dumpdate).date()
    
    ## creating processor
    processor = EventsProcessor(lang=opts.lang, range_=opts.range_,
                                skip=opts.skip, dump_date=dump,
                                desired=opts.desired, output_file=files[2])

    ## set desired pages
    processor.set_desired(desired_pages)
    ## main process
    processor.process(threshold=threshold)

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', '/tmp/itprof.morail')
    main()
    #import timeit
    #print timeit.timeit("main.is_near_anniversary(date(2001, 9, 11), date(2005, 9, 19), 10)",
    #              "import __main__ as main;from datetime import date")
