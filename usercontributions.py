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

import os
import sys
import re
try:
    import re2
    re2_compile_with_fallback = re2.compile
except ImportError:
    logging.warn("pyre2 not available. It's gonna be a long job")
    re2_compile_with_fallback = re.compile
import time
#import guppy
from array import array
from datetime import datetime
import logging

## PROJECT LIBS
import sonet.mediawiki as mwlib
from sonet.lib import find_open_for_this_file
from sonet.timr import Timr
from multiprocessing import Process, Pipe

## DATABASE
from sonet.models import get_contributions_table
from base64 import b64encode
from zlib import compress
from wbin import serialize

ATTR_LEN = None

class UserContrib(object):
    __slots__ = ['comments_length', 'namespace_count', 'data']

    def __init__(self):
        ##self.namespace_count = np.zeros((attr_len,), dtype=np.int)
        ## TODO: class wide attribute
        ## data = [comments_count, minor, welcome, npov,
        ##         please, thanks, revert, first_time, last_time, normal_edits]

        ## 4 bytes per item on 64bit pc
        ## array of unsigned int, len = 10
        self.data = array('I', (0,)*10)

        ## this can be very large, in this way it uses python bigints.
        ## KEEP THIS OUT OF self.data!!
        self.comments_length = 0

        ## we don't define namespace_count here but in inc_namespace() to save
        ## memory

    @property
    def normal_count(self):
        return self.data[9]

    def inc_normal(self):
        self.data[9] += 1

    def inc_namespace(self, idx):
        if not hasattr(self, 'namespace_count'):
            ##TODO: maybe attr_len contains unneeded namespace? like key=0
            self.namespace_count = array('I', (0,)*ATTR_LEN)
        self.namespace_count[idx] += 1

    @property
    def first_time(self):
        return datetime.fromtimestamp(self.data[7])

    @property
    def last_time(self):
        return datetime.fromtimestamp(self.data[8])

    def time(self, time_):
        epoch = int(time.mktime(time_.timetuple()))
        if self.data[7] == 0 or self.data[7] > epoch:
            self.data[7] = epoch
        if self.data[8] == 0 or self.data[8] < epoch:
            self.data[8] = epoch

    @property
    def comment_length(self):
        try:
            return 1.*self.comments_length/self.data[0]
        except ZeroDivisionError:
            return 0.

    @comment_length.setter
    def comment_length(self, length):
        self.comments_length += length
        self.data[0] += 1

    @property
    def comment_count(self):
        return self.data[0]

    @property
    def minor(self):
        return self.data[1]

    def inc_minor(self):
        self.data[1] += 1

    @property
    def welcome(self):
        return self.data[2]

    def inc_welcome(self):
        self.data[2] += 1

    @property
    def npov(self):
        return self.data[3]

    def inc_npov(self):
        self.data[3] += 1

    @property
    def please(self):
        return self.data[4]

    def inc_please(self):
        self.data[4] += 1

    @property
    def thanks(self):
        return self.data[5]

    def inc_thanks(self):
        self.data[5] += 1

    @property
    def revert(self):
        return self.data[6]

    def inc_revert(self):
        self.data[6] += 1


class ContribDict(dict):
    def __init__(self, namespaces):
        global ATTR_LEN
        super(ContribDict, self).__init__()
        self._namespaces = namespaces
        ATTR_LEN = len(namespaces)
        self._d_namespaces = dict([(name.decode('utf-8'), idx) for idx, (_,
            name) in enumerate(namespaces)])
        self._re_welcome = re2_compile_with_fallback(r'well?come', flags=re.I)
        self._re_npov = re2_compile_with_fallback(r'[ n]pov', flags=re.I)
        self._re_please = re2_compile_with_fallback(r'pl(s|z|ease)',
                                                    flags=re.I)
        self._re_thanks = re2_compile_with_fallback(r'th(ank|anx|x)',
                                                    flags=re.I)
        self._re_revert = re2_compile_with_fallback(r'(revert| rev )',
                                                    flags=re.I)

        contributions, self.connection = get_contributions_table()
        self.insert = contributions.insert()

    #----------------------------------------------------------------------
    def append(self, user, page_title, timestamp, comment, minor):
        try:
            contrib = self[user]
        except KeyError:
            contrib = UserContrib()
            self[user] = contrib

        ## Namespace
        a_title = page_title.split(':')
        if len(a_title) == 1:
            contrib.inc_normal()
        else:
            try:
                contrib.inc_namespace(self._d_namespaces[a_title[0]])
            except KeyError:
                contrib.inc_normal()

        year = int(timestamp[:4])
        month = int(timestamp[5:7])
        day = int(timestamp[8:10])
        hour = int(timestamp[11:13])
        minutes = int(timestamp[14:16])
        seconds = int(timestamp[17:19])

        timestamp = datetime(year, month, day, hour, minutes, seconds)
        ## Time
        contrib.time(timestamp)

        ## Minor
        if minor:
            contrib.inc_minor()

        ## Comment
        if not comment: return
        contrib.comment_length = len(comment)
        if self._re_welcome.search(comment) is not None:
            contrib.inc_welcome()
        if self._re_npov.search(comment) is not None:
            contrib.inc_npov()
        if self._re_please.search(comment) is not None:
            contrib.inc_please()
        if self._re_thanks.search(comment) is not None:
            contrib.inc_thanks()
        if self._re_revert.search(comment) is not None:
            contrib.inc_revert()

    #----------------------------------------------------------------------
    def save(self, lang):
        """
        Save the accumulated data into DB
        """
        from itertools import islice

        iterator = self.iteritems()
        step = 100000
        for _ in xrange(0, len(self), step):
            data = [{'username': user,
                     'lang': lang,
                     'normal_edits': d.normal_count,
                     'namespace_edits': b64encode(
                         compress(serialize(d.namespace_count.tolist())))
                             if hasattr(d, 'namespace_count') else None,
                     'first_edit': d.first_time,
                     'last_edit': d.last_time,
                     'comments_count': d.comment_count,
                     'comments_avg': d.comment_length,
                     'minor': d.minor,
                     'welcome': d.welcome,
                     'npov': d.npov,
                     'please': d.please,
                     'thanks': d.thanks,
                     'revert': d.revert
                     }
                    for user, d in islice(iterator, step)]
            self.connection.execute(self.insert, data)


def use_contrib_dict(receiver, namespaces, lang):
    cd = ContribDict(namespaces)

    while 1:
        rev = receiver.recv()

        try:
            cd.append(*rev)
        except TypeError:
            cd.save(lang)
            return

class UserContributionsPageProcessor(mwlib.PageProcessor):
    """
    UserContributionsPageProcessor extracts a graph from a meta-history or a
    stub-meta-history dump.

    A state-machine-like approach is used to parse the file.

    Only tag-end events are used. (eg. in <a><b></b></a> the first event is for
    the <b> tag, then the one for <a>).

    The entry point is process_title (one per page). Then, in every page there
    are many revisions, and each one has timestamp and contributor tags.

    <page>
        <title>Title</title>
        <revision>
            <timestamp>...<timestamp>
            <contributor>...</contributor>
        </revision>
        (... more revisions ...)
    </page>
    """
    __slots__ = tuple()
    # to limit the extraction to changes before a datetime
    time_end = None
    # to limit the extraction to changes after a datetime
    time_start = None
    _re_welcome = None
    __welcome_pattern = None
    sender = None ## multiprocessing Connection object
    __namespaces = None
    count_revision = 0

    @property
    def namespaces(self):
        return self.__namespaces

    @namespaces.setter
    def namespaces(self, namespaces):
        self.__namespaces = namespaces
        self.contribution = ContribDict(namespaces)

    @property
    def welcome_pattern(self):
        return self.__welcome_pattern

    @welcome_pattern.setter
    def welcome_pattern(self, value):
        self.__welcome_pattern = value
        self._re_welcome = re.compile(value, flags=re.IGNORECASE)

    ## PAGE RELATED VARIABLES
    _skip = False
    _title = None

    ## REVISION RELATED VARIABLES
    _time = None ## time of this revision
    _comment = None
    _skip_revision = False
    _sender = None
    _minor = False

    def process_title(self, elem):
        self._title = elem.text

    def process_timestamp(self, elem):
        if self._skip_revision: return

        self._time = elem.text

    def process_contributor(self, contributor):
        if self._skip_revision: return

        if contributor is None:
            logging.warning('contributor is None')
            self._skip_revision = True

        sender_tag = contributor.find(self.tag['username'])
        if sender_tag is None:
            self._skip_revision = True
        else:
            try:
                self._sender = mwlib.normalize_pagename(sender_tag.text)
            except AttributeError:
                ## if username is defined but empty, look for id tag
                self._sender = contributor.find(self.tag['id']).text

    def process_comment(self, elem):
        if self._skip_revision or not elem.text:
            return
        self._comment = elem.text

    def process_minor(self, _):
        self._minor = True

    def process_revision(self, _):
        skip, self._skip_revision = self._skip_revision or self._skip, False
        comment, self._comment = self._comment, None
        minor, self._minor = self._minor, False
        if skip: return

        self.count_revision += 1
        assert self._sender is not None, "Sender still not defined"
        assert self._title is not None, "Page title not defined"
        assert self._time is not None, "time not defined"

        self.sender.send((self._sender, self._title, self._time,
                comment, minor))

        self._sender = None

    def process_page(self, _):
        if self._skip:
            self._skip = False
            return

        self._title = None

        self.count += 1
        if not self.count % 500:
            logging.debug("%d %d", self.count, self.count_revision)
            #with Timr('guppy'):
            #    logging.debug(guppy.hpy().heap())

    #def end(self):
    #    with Timr('save'):
    #        self.contribution.save(self.lang)


def opt_parse():
    from optparse import OptionParser
    from sonet.lib import SonetOption

    p = OptionParser(usage="usage: %prog [options] dumpfile",
                     option_class=SonetOption)
    p.add_option('-s', '--start', action="store",
        dest='start', type="yyyymmdd", metavar="YYYYMMDD", default=None,
        help="Look for revisions starting from this date")
    p.add_option('-e', '--end', action="store",
        dest='end', type="yyyymmdd", metavar="YYYYMMDD", default=None,
        help="Look for revisions until this date")
    opts, args = p.parse_args()

    ## CHECK IF OPTIONS ARE OK
    if len(args) != 1:
        p.error("Wrong number of arguments")
    if not os.path.exists(args[0]):
        p.error("Dump file does not exist (%s)" % (args[0],))
    return (opts, args)


def main():
    logging.basicConfig(#filename="usercontributions.log",
                        stream=sys.stderr,
                        level=logging.DEBUG)
    logging.info('---------------------START---------------------')

    receiver, sender = Pipe(duplex=False)

    _, args = opt_parse()
    xml = args[0]

    ## SET UP FOR PROCESSING
    lang, _, _ = mwlib.explode_dump_filename(xml)

    deflate, _lineno = find_open_for_this_file(xml)

    if _lineno:
        src = deflate(xml, 51)
    else:
        src = deflate(xml)

    tag = mwlib.get_tags(src,
        tags='page,title,revision,timestamp,contributor,username,ip'+ \
             ',comment,id,minor')

    namespaces = mwlib.get_namespaces(src)

    src.close()
    logging.info("BEGIN PARSING")
    src = deflate(xml)

    processor = UserContributionsPageProcessor(tag=tag, lang=lang)
    processor.sender = sender
    processor.namespaces = namespaces
    ##TODO: only works on it.wikipedia.org! :-)
    processor.welcome_pattern = r'Benvenut'

    p = Process(target=use_contrib_dict, args=(receiver, processor.namespaces,
                                               lang))
    p.start()

    with Timr('PROCESSING'):
        processor.start(src) ## PROCESSING

    sender.send(None)
    p.join() ## wait until save is complete


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
    #h = guppy.hpy()
    #print h.heap()
