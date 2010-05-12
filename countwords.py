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
import mwlib
import os, sys
import re
from time import time

## etree
from lxml import etree

## nltk
import nltk
from nltk.corpus import stopwords

count = 0
lang = None
old_user = None
g = None
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"

## frequency distribution
fd = nltk.FreqDist()
it_stopwords = stopwords.words('italian')


def process_page(elem):
    user = None
    global count, fd, it_stopwords
    
    for child in elem:
        if child.tag == tag['title'] and child.text:
            a_title = child.text.split('/')[0].split(':')

            try:
                if a_title[0] in (en_user_talk, lang_user_talk):
                #if len(a_title) > 1 and a_title[0] == lang_user_talk:
                    user = a_title[1]
                else:
                    return
            except KeyError:
                return
        elif child.tag == tag['revision']:
            for rc in child:
                if rc.tag != tag['text']:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                try:
                    tokens = nltk.word_tokenize(nltk.clean_html(rc.text.encode('utf-8')))
                    text = nltk.Text(t for t in tokens if len(t) > 2 and t not in it_stopwords)

                    fd.update(text)
                    
                    count += 1
                    
                    if not count % 500:
                        print >>sys.stderr, count
                except:
                    print "Warning: exception with user %s" % (user.encode('utf-8'),)
                    raise


def fast_iter(context, func):
    for event, elem in context:
        func(elem)
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

    global templates
    global lang_user_talk, lang_user, tag

    src = BZ2File(xml)

    tag = mwlib.getTags(src)

    lang_user, lang_user_talk = mwlib.getTranslations(src)

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    fast_iter(etree.iterparse(src, tag=tag['page']), process_page)

    for k, v in sorted(fd.items(),cmp=lambda x,y: cmp(x[1], y[1]),reverse=True):
        print v, k


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
