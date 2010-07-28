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

from datetime import datetime

## PROJECT LIBS
from edgecache import EdgeCache
import mwlib
from lib import SevenZipFileExt
from mwlib import PageProcessor


class HistoryPageProcessor(PageProcessor):
    # to limit the extraction to changes before a datetime
    end = None
    # to limit the extraction to changes after a datetime
    start = None
    
    def process(self, elem):
        tag = self.tag
        user = None
        for child in elem:
            if child.tag == tag['title'] and child.text:
                a_title = child.text.split(':')
    
                if len(a_title) > 1 and a_title[0] in self.user_talk_names:
                    user = a_title[1]
                else:
                    return
                
                try:
                    child.text.index('/')
                    self.count_archive += 1
                    return
                except ValueError:
                    pass

            elif child.tag == tag['revision']:
                revision_time = datetime.strptime(
                    child.find(tag['timestamp']).text,
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                if self.end and revision_time > self.end:
                    continue
                if self.start and revision_time < self.start:
                    continue
                    
                ##TODO: change 'rc' variable name
                rc = child.find(tag['contributor'])
                if rc.tag != tag['contributor']:
                    continue

                assert user, "User still not defined"
                
                sender_tag = rc.find(tag['username'])
                if sender_tag is None:
                    sender_tag = rc.find(tag['ip'])
                collaborator = mwlib.capfirst(
                    sender_tag.text.replace('_', ' ')
                )
                    
                self.ecache.add(mwlib.capfirst(user.replace('_', ' ')),
                                {collaborator: [revision_time,]}
                                )
                self.count += 1
                if not self.count % 500:
                    print self.count


def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    en_user, en_user_talk = u"User", u"User talk"
    
    lang, date, type_ = mwlib.explode_dump_filename(xml)

    ecache = EdgeCache()

    src = SevenZipFileExt(xml, 51)
    
    tag = mwlib.getTags(src)

    lang_user, lang_user_talk = mwlib.getTranslations(src)
    
    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    lang_user = unicode(lang_user)
    en_user = unicode(en_user)
    
    src.close()
    src = SevenZipFileExt(xml)
        
    processor = HistoryPageProcessor(ecache=ecache, tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang)
    processor.end = datetime(2009, 12, 31)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
                    processor.process)
    print 'TOTAL UTP: ', processor.count
    print 'ARCHIVES: ', processor.count_archive

    ecache.flush()
    g = ecache.get_network(edge_label='timestamp')

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%swiki-%s%s.pickle" % (lang, date, type_), format="pickle")
    
    for e in g.es:
        e['weight'] = len(e['timestamp'])
        #e['timestamp'] = str(e['timestamp'])
    g.write("%swiki-%s%s.graphml" % (lang, date, type_), format="graphml")
    

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
