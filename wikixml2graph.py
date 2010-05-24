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
import os
import sys
from time import time
import re

## LXML
from lxml import etree

## PROJECT LIBS
from edgecache import EdgeCache
import mwlib
import lib

count = 0
search = None
searchEn = None
lang = None
old_user = None
ecache = None
g = None
lang_user, lang_user_talk = None, None
en_user, en_user_talk = u"User", u"User talk"
tag = {}


def process_page(elem, ecache):
    user = None
    global count
    for child in elem:
        if child.tag == tag['title'] and child.text:
            a_title = child.text.split('/')[0].split(':')

            if len(a_title) > 1 and a_title[0] in (en_user_talk, lang_user_talk):
                user = a_title[1]
            else:
                return
        elif child.tag == tag['revision']:
            for rc in child:
                if rc.tag != tag['text']:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                try:
                    talks = mwlib.getCollaborators(rc.text, search, searchEn)
                    ecache.add(user, talks)
                    count += 1
                    if not count % 500:
                        print count
                except:
                    print "Warning: exception with user %s" % (user.encode('utf-8'),)


def fast_iter(context, func, ecache):
    for event, elem in context:
        func(elem, ecache)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context


def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")

    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    global lang
    global search, searchEn, lang_user, lang_user_talk
    global g, ecache, tag
    
    lang, date = mwlib.explode_dump_filename(xml)

    ecache = EdgeCache()

    src = BZ2File(xml)
    
    tag = mwlib.getTags(src)

    lang_user, lang_user_talk = mwlib.getTranslations(src)
    
    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    search = unicode(lang_user)
    searchEn = unicode(en_user)
    
    _fast = True
    if _fast:
        src.close()
        src = lib.BZ2FileExt(xml)
    
    fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
              process_page, ecache)

    ecache.flush()
    g = ecache.get_network()

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%swiki-%s.pickle" % (lang, date), format="pickle")
    #g.write("%swiki-%s.graphml" % (lang, date), format="graphml")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
