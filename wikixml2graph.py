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

from bz2 import BZ2File

## LXML
from lxml import etree

## PROJECT LIBS
from edgecache import EdgeCache
import mwlib
import lib

class PageProcessor(object):
    count = 0
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
                a_title = child.text.split('/')[0].split(':')
    
                if len(a_title) > 1 and a_title[0] in self.user_talk_names:
                    user = a_title[1]
                else:
                    return
            elif child.tag == tag['revision']:
                for rc in child:
                    if rc.tag != tag['text']:
                        continue
    
                    assert user, "User still not defined"
                    if not (rc.text and user):
                        continue
                    
                    if (mwlib.isHardRedirect(rc.text) or
                       mwlib.isSoftRedirect(rc.text)):
                        continue
                    
                    #try:
                    #talks = mwlib.getCollaborators(rc.text, self.search)
                    talks = mwlib.getCollaborators(rc.text, ('User', 'Utente'),
                                                   lang="vec")
                    #except:
                    #    print "Warning: exception with user %s" % (
                    #        user.encode('utf-8'),)
                        
                    self.ecache.add(mwlib.capfirst(user.replace('_', ' ')),
                                    talks)
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

    src = BZ2File(xml)
    
    tag = mwlib.getTags(src)

    lang_user, lang_user_talk = mwlib.getTranslations(src)
    
    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    lang_user = unicode(lang_user)
    en_user = unicode(en_user)
    
    _fast = True
    if _fast:
        src.close()
        src = lib.SevenZipFileExt(xml)
    
    processor = PageProcessor(ecache=ecache, tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
                    processor.process)

    #import cPickle as pickle
    
    #with open('/hardmnt/sakamoto0/sra/setti/datasets/'+
    #          'wikipedia/itwiki-20100218-ec.pickle', 'wb') as f:
    #    pickle.dump(ecache.temp_edges, f)
        
    ecache.flush()
    g = ecache.get_network()

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%swiki-%s.pickle" % (lang, date), format="pickle")
    


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
