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

import mmap

## PROJECT LIBS
from edgecache import EdgeCache
import mwlib
import lib
from lib import SevenZipFileExt

class PageProcessor(object):
    count = 0
    count_archive = 0
    ecache = None
    tag = None
    user_talk_names = None
    search = None
    lang = None
    
    def __init__(self, ecache=None, tag=None, user_talk_names=None,
                 search=None, lang=None):
        self.ecache = ecache
        self.tag = tag
        self.user_talk_names = user_talk_names
        self.search = search
        self.lang = lang
    
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
                for rc in child:
                    if rc.tag != tag['contributor']:
                        continue
    
                    assert user, "User still not defined"
                    
                    try:
                        sender_tag = rc.find(tag['username'])
                        if sender_tag is None:
                            sender_tag = rc.find(tag['ip'])
                        collaborator = mwlib.capfirst(
                            sender_tag.text.replace('_', ' ')
                        )
                    except AttributeError, e:
                        raise AttributeError, e
                        
                    self.ecache.add(mwlib.capfirst(user.replace('_', ' ')),
                                    {collaborator: 1}
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
    
    lang, date = mwlib.explode_dump_filename(xml)

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
    
    processor = PageProcessor(ecache=ecache, tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
                    processor.process)
    print 'TOTAL UTP: ', processor.count
    print 'ARCHIVES: ', processor.count_archive

    ecache.flush()
    g = ecache.get_network()

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%swikihistory-%s.graphml" % (lang, date), format="graphml")
    

if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
