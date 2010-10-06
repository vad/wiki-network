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
import sys, csv
from os import path

from django.utils.encoding import smart_str

from sonet.models import get_events_table
from sonet import lib

## GLOBAL VARS
initial_date = date(2000,1,1)


def page_iter(lang = 'en', paginate=10000000, desired=None):
    events, conn = get_events_table()

    count_query = select([func.count(events.c.id)],
               events.c.lang == lang)
    s = select([events.c.title, events.c.data, events.c.talk,
                events.c.total_editors,events.c.bot_editors,
                events.c.anonymous_editors],
                events.c.lang == lang).order_by(
        events.c.title, events.c.talk).limit(paginate)

    ## searching only desired pages
    if desired:
        s = s.where(events.c.title.in_(desired))
        count_query = count_query.where(events.c.title.in_(desired))

    count = conn.execute(count_query).fetchall()[0][0]
    
    print 'PAGES:', count

    for offset in xrange(0, count, paginate):
        rs = conn.execute(s.offset(offset))
        for row in rs:
            yield (row[0],
                   deserialize(decompress(b64decode(row[1]))),
                   row[2],row[3],row[4],row[5])

            
def get_days_since(start_date, end_date, anniversary_date, td_list):
    """
    Returns the number of days passed between two dates. If the considered date
    is an anniversary, count the number of days in the range around the 
    anniversary for each year

    >>> td = [timedelta(i) for i in range(-10,11)]
    >>> get_days_since(date(2001, 9, 11), date(2005, 9, 19), None, td)
    1470
    >>> get_days_since(date(2010, 9, 11), date(2005, 9, 19), None, td)
    0
    >>> get_days_since(date(2005, 9, 16), date(2005, 9, 19), None, td)
    4
    >>> get_days_since(date(2001,9,11),date(2010,7,29),date(2001,9,11),td)
    179
    >>> get_days_since(date(2001,9,22),date(2010,7,29),date(2001,9,11),td)
    168
    >>> get_days_since(date(2006,1,7),date(2006,7,7),date(2005,7,7),td)
    11
    >>> get_days_since(date(2010,2,4),date(2010,7,29),date(1952,8,4),td)
    5
    >>> td = [timedelta(i) for i in range(-50,51)]
    >>> get_days_since(date(2001,12,30),date(2002,1,1),date(2001,12,30),td)
    3
    >>> td = [timedelta(i) for i in range(-20,21)]
    >>> get_days_since(date(2001,1,1),date(2001,12,31),date(2001,6,15),td)
    41
    >>> td = [timedelta(i) for i in range(-5,6)]
    >>> get_days_since(date(2001,1,1),date(2003,1,1),date(2001,6,15),td)
    22
    >>> get_days_since(date(2001,9,22),date(2010,7,29),date(2001,9,11),None)
    8
    >>> get_days_since(date(2004,2,29),date(2010,7,29),date(2000,2,29),None)
    7
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
        if td_list:
            counter += len([1 for d in (ad + td 
                        for td in td_list) 
                        if (d >= start_date and d <= end_date)])
        else:
            counter += int(ad >= start_date and ad <= end_date)
        
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
    
def print_data_file(fn, dict_, s_date, e_date):
    """
    Given a filename and a dictionary of day => revisions
    it creates a csv file
    """
    s_days = (s_date - initial_date).days
    e_days = (e_date - initial_date).days
    
    with open(fn, 'w') as f:
        wrt = csv.writer(f)
        wrt.writerow(['date','total_edits','bot_edits','anon_edits'])
        for d in range(s_days, e_days + 1):
            try:
                t = dict_[d]
                wrt.writerow([(initial_date+timedelta(d)).strftime('%Y-%m-%d'),
                        t[0],t[1],t[2]])
            except KeyError:
                wrt.writerow([(initial_date+timedelta(d)).strftime('%Y-%m-%d'),
                        0,0,0])

class EventsProcessor:
    count_desired = []
    count_pages = 0
    count_revisions = 0
    creation_accumulator = {}
    csv_writer = None
    desired_only = False ## search desired pages only
    desired_pages = {}
    dump_date = None
    groups = None
    lang = None
    keys_ = ['article','type_of_page','desired','total_edits',
             'unique_editors','anniversary_edits','n_of_anniversaries',
             'anniversary_days','anniversary_edits/total_edits',
             'non_anniversary_edits/total_edits','event_date',
             'first_edit_date','first_edit_date-event_date_in_days']
    output_dir = None
    pages = []
    range_ = None
    skipped_days = None
    td_list = None
    threshold = None
    __event_date = None
    __first_edit_date = None
    __data = None
    __desired = None
    __id = None
    __n_of_anniversaries = None
    __title = None
    __type = None
    __unique_editors = 0

    def __init__(self, **kwargs):
        
        from subprocess import Popen, PIPE        
        
        self.lang = kwargs['lang']
        self.range_ = kwargs['range_']
        self.skipped_days = kwargs['skip']
        self.dump_date = kwargs['dump_date']
        self.desired_only = kwargs['desired']
        self.groups = kwargs['groups']
                
        # timedelta list, used in get_days_since
        self.td_list = [timedelta(i) for i in
                        range(-self.range_,self.range_+1)]
        
        if not lib.find_executable('7z'):
            raise Exception, 'Cannot find 7zip executable (7z)'
        
        fn = kwargs['output_file'] + '.bz2'
        
        if path.isfile(fn):
            raise Exception, 'Delete file ' + fn + ' before proceeding'
        
        zip_process = Popen(['7z', 'a', '-tbzip2', '-mx=9', fn, '-si'],
                            stdin=PIPE, stderr=None)
                
        self.csv_writer = csv.DictWriter(zip_process.stdin, 
                                   fieldnames = self.keys_, delimiter=',', 
                                   quotechar='"', quoting=csv.QUOTE_ALL)
        
        self.csv_writer.writeheader()
        
        ## Outup directory for data files (only for desired pages)
        self.output_dir = fn[0:fn.rfind('/')] + '/%s_data_files/' % self.lang
        ## check if the directory exists. if not create it
        lib.ensure_dir(self.output_dir)
                        
    def set_desired(self, fn):
        ## save desired pages list
        for r in csv.reader(open(fn, 'rb')):
            page = r[0].decode('latin-1').replace('_',' ')
            if page[0] == '#': continue
            
            try:
                self.desired_pages[page] = \
                    date(int(r[1][:4]),int(r[1][5:7]),int(r[1][8:10]))
            except:
                self.desired_pages[page] = None

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
        s_date = self.get_start_date()
        return get_days_since(start_date=s_date, end_date=self.dump_date,
                                  anniversary_date=self.__event_date, 
                                  td_list=None)

    def process(self, threshold=1.):
        from random import random
                       
        des = self.desired_pages.keys() if self.desired_only else None
        
        for title,data,talk,te,be,ae in page_iter(lang=self.lang,desired=des):
            ## check whether the page is an archive or not
            ## if it is a link, skip it!
            if is_archive(title):
                continue
            
            ## editors who are neither bots nor anonymous
            oe = te - be - ae
            
            ## page's attributes
            self.__title = title
            self.__data = data
            self.__desired = self.is_desired()
            self.__type_of_page = talk ## 0 = article, 1 = talk
            ## unique editors
            self.__unique_editors = (
                (oe if 'total' not in self.groups else 0) +
                (be if 'bots' not in self.groups else 0) +
                (ae if 'anonymous' not in self.groups else 0)
            )
            
            if self.__desired and self.__title not in self.count_desired:
                print "PROCESSING DESIRED PAGE:", self.__title
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
        """
        process a page counting all the revisions made and
        calculating some statistics as number of days since
        creation, edits in anniversary's range, etc.
        """
        
        ## page's (and last page as well) attributes
        title = self.__title
        talk = self.__type_of_page
        groups = self.groups
        
        ## creation date
        self.__first_edit_date = get_first_revision(initial_date,
                                                 self.__data)
        if self.__desired:
            if self.desired_pages[title] is not None:
                self.__event_date = self.desired_pages[title]
            else:
                self.__event_date = self.__first_edit_date
        else:
            self.__event_date = self.__first_edit_date
           
        ## if it is a desired page then print out data 
        ## about its daily revisions
        if self.__desired:
            fn = self.output_dir + '%s%s.csv' % ('Talk:' if talk else '',title,)
            print_data_file(fn, self.__data, self.__first_edit_date,
                            self.dump_date)
            
        ## if the page has been created less than one year ago, skip
        ## TODO: 365 - range??
        if (self.dump_date - self.__first_edit_date).days < 365:
            return

        anniversary = 0
        total = 0
        in_skipped = 0

        for d, t in self.__data.iteritems():
            tot_edits, bot_edits, anon_edits = t
            other_edits = tot_edits - bot_edits - anon_edits
            revision = initial_date + timedelta(d)
            if (revision - self.__event_date).days < self.skipped_days:
                in_skipped += tot_edits
                continue
            if is_near_anniversary(self.__event_date, revision, self.range_):
                ## edits made in anniversary's range
                anniversary += (
                    (other_edits if 'total' not in groups else 0) +
                    (bot_edits if 'bots' not in groups else 0) +    
                    (anon_edits if 'anonymous' not in groups else 0)
                )
            ## total edits
            total += (
                (other_edits if 'total' not in groups else 0) +
                (bot_edits if 'bots' not in groups else 0) + 
                (anon_edits if 'anonymous' not in groups else 0)
            )
                
        try:
            ann_total_edits = anniversary / total
            not_ann_total_edits = (total - anniversary) / total
        except ZeroDivisionError:
            ann_total_edits = 0.
            not_ann_total_edits = 0.
                    
        dict_ = {
            'article': smart_str(self.__title),
            'type_of_page': int(not talk),
            'desired': int(self.__desired),
            'total_edits': total,
            'unique_editors': self.__unique_editors,
            'anniversary_edits': anniversary,
            'n_of_anniversaries': self.get_n_anniversaries(),
            'anniversary_days': self.get_days_since(),
            'anniversary_edits/total_edits': ann_total_edits,
            'non_anniversary_edits/total_edits': not_ann_total_edits,
            'event_date': self.__event_date,
            'first_edit_date': self.__first_edit_date,
            'first_edit_date-event_date_in_days': (self.__first_edit_date - 
                                                   self.__event_date).days
        }

        self.pages.append(dict_)
        self.count_pages += 1
        self.count_revisions += total

        if not self.count_pages % 50000:
            self.flush()       

    def flush(self):
        
        print 'PAGES:', self.count_pages, 'REVS:', self.count_revisions,
        'DESIRED:', len(self.count_desired)
        
        self.csv_writer.writerows(self.pages)
                   
        self.pages = []
        return

    
def create_option_parser():
    from optparse import OptionParser, OptionGroup
    from sonet.lib import SonetOption

    op = OptionParser('%prog [options] file dump-date output-file', 
                      option_class=SonetOption)
    
    op.add_option('-l', '--lang', action="store", dest="lang",
                 help="Wikipedia language (en, it, vec, ...)", default="en")
    op.add_option('-r', '--range', action="store", dest="range_",
                 help="number of days before and after anniversary date",
                 default=10, type="int")
    op.add_option('-s', '--skipped-days', action="store", dest="skip",
                 help="number of days to be skipped", default=180, type="int")
    op.add_option('-d', '--desired-only', action="store_true", dest='desired',
                 default=False, help='analysis only of desired pages')
    op.add_option('-g','--groups',action="store",dest='groups',default='', 
                 help='comma separated list of not-to-be-analyzed groups \
                 (total|bots|anonymous)')
    op.add_option('-R', '--ratio', action="store", dest="ratio",
                 help="percentage of pages to be analyzed",
                 default=1., type="float")
    
    return op

def main():

    p = create_option_parser()
    opts, files = p.parse_args()

    try:
        desired_pages_fn = files[0]
        dumpdate = files[1]
        out_file = files[2]
    except IndexError:
        p.error("Bad number of arguments! Try with --help option")

    ## creating dump date object
    dump = lib.yyyymmdd_to_datetime(dumpdate).date()
    
    ## list of not-to-be-analyzed groups
    groups = [g for g in opts.groups.split(',') if g]
    
    ## creating processor
    processor = EventsProcessor(lang=opts.lang, range_=opts.range_, 
                                skip=opts.skip, dump_date=dump, groups=groups, 
                                desired=opts.desired, output_file=files[2])

    ## set desired pages
    processor.set_desired(desired_pages_fn)
    ## main process
    processor.process(threshold=opts.ratio)

if __name__ == "__main__":
    main()