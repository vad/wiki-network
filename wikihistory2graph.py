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

from datetime import datetime
import os

## PROJECT LIBS
from sonet.edgecache import EdgeCache
import sonet.mediawiki as mwlib
from sonet.lib import SevenZipFileExt, find_open_for_this_file

class HistoryPageProcessor(mwlib.PageProcessor):
    """
    HistoryPageProcessor extracts a graph from a meta-history or a
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
        (... more revision)
    </page>
    """
    # to limit the extraction to changes before a datetime
    time_end = None
    # to limit the extraction to changes after a datetime
    time_start = None
    _receiver = None
    _sender = None
    _skip = False
    _skip_revision = False
    _time = None ## time of this revision
    counter_deleted = 0

    def process_title(self, elem):
        if self._skip_revision: return

        title = elem.text
        a_title = title.split(':')

        if len(a_title) > 1 and a_title[0] in self.user_talk_names:
            self._receiver = a_title[1]
        else:
            self._skip = True
            return

        try:
            title.index('/')
            self.count_archive += 1
            self._skip = True
        except ValueError:
            pass

    def process_timestamp(self, elem):
        if self._skip_revision: return

        timestamp = elem.text
        year = int(timestamp[:4])
        month = int(timestamp[5:7])
        day = int(timestamp[8:10])
        hour = int(timestamp[11:13])
        minutes = int(timestamp[14:16])
        seconds = int(timestamp[17:19])
        revision_time = datetime(year, month, day, hour, minutes, seconds)
        if ((self.time_end and revision_time > self.time_end) or
            (self.time_start and revision_time < self.time_start)):
            self._skip_revision = True
        else:
            self._time = revision_time

    def process_contributor(self, contributor):
        if self._skip_revision: return

        if contributor is None:
            self._skip_revision = True

        sender_tag = contributor.find(self.tag['username'])
        if sender_tag is None:
            try:
                self._sender = contributor.find(self.tag['ip']).text
            except AttributeError:
                ## user deleted
                self._skip_revision = True
                self.counter_deleted += 1
        else:
            try:
                self._sender = mwlib.capfirst(
                    sender_tag.text.replace('_', ' ')
                )
            except AttributeError:
                ## if username is defined but empty, look for id tag
                self._sender = contributor.find(self.tag['id']).text

    def process_revision(self, elem):
        skip = self._skip_revision
        self._skip_revision = False
        if skip: return

        assert self._sender is not None, "Sender still not defined"
        assert self._receiver is not None, "Receiver still not defined"

        self.ecache.add(mwlib.capfirst(self._receiver.replace('_', ' ')),
                        {self._sender: [self._time,]}
                        )
        self._sender = None

    def process_page(self, _):
        if self._skip:
            self._skip = False
            return

        self._receiver = None

        self.count += 1
        if not self.count % 500:
            print self.count


def main():
    from optparse import OptionParser

    p = OptionParser(usage="usage: %prog [options] file")
    p.add_option('-l', '--lang', action="store", dest="lang",
                 help="wikipedia language", default="en")
    _, args = p.parse_args()

    if len(args) != 1: p.error("Give me a file, please ;-)")
    xml = args[0]
    if not os.path.exists(xml):
        p.error("Dump file does not exist (%s)" % (xml,))

    en_user, en_user_talk = u"User", u"User talk"

    lang, date_, type_ = mwlib.explode_dump_filename(xml)

    ecache = EdgeCache()
    deflate, _lineno = find_open_for_this_file(xml)

    if _lineno:
        src = deflate(xml, 51)
    else:
        src = deflate(xml)

    tag = mwlib.getTags(src,
            tags='page,title,revision,text,timestamp,contributor,username,ip')

    translations = mwlib.getTranslations(src)
    lang_user, lang_user_talk = translations['User'], translations['User talk']

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    lang_user = unicode(lang_user)
    en_user = unicode(en_user)

    src.close()
    print "BEGIN PARSING"
    src = deflate(xml)

    processor = HistoryPageProcessor(ecache=ecache, tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang)
    processor.start(src)
    print 'TOTAL UTP: ', processor.count
    print 'ARCHIVES: ', processor.count_archive
    print 'DELETED: ', processor.counter_deleted

    ecache.flush()
    g = ecache.get_network(edge_label='timestamp')

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    for e in g.es:
        e['weight'] = len(e['timestamp'])
        #e['timestamp'] = str(e['timestamp'])
    g.write("%swiki-%s%s.pickle" % (lang, date_, type_), format="pickle")
    g.write("%swiki-%s%s.graphml" % (lang, date_, type_), format="graphml")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
