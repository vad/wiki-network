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
import os, sys
import re
from time import time

## etree
from lxml import etree

from sonet import mediawiki as mwlib

count = 0
lang = None
old_user = None
g = None
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"
templates = {}


def merge_templates(big, small):
    for k, v in small.iteritems():
        big.setdefault(k, 0) #set big[k] if not already defined
        big[k] += v


def process_page(elem):
    user = None
    global count, templates

    for child in elem:
        if child.tag == tag['title'] and child.text:
            a_title = child.text.split('/')[0].split(':')

            if len(a_title) > 1 and a_title[0] in (en_user, lang_user):
            #if len(a_title) > 1 and a_title[0] == en_user:
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
                    page_templates = mwlib.getTemplates(rc.text)
                    merge_templates(templates, page_templates)
                    count += 1

                    if not count % 500:
                        print >> sys.stderr, count
                except:
                    print "Warning: exception with user %s" % (user.encode('utf-8'),)
                    raise


def main():
    import optparse
    from operator import itemgetter

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml_filename = files[0]

    global lang_user_talk, lang_user, tag

    src = BZ2File(xml_filename)

    tag = mwlib.getTags(src)

    lang_user, lang_user_talk = mwlib.getTranslations(src)

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], huge_tree=True),
                    process_page)

    for k, v in sorted(templates.items(), key=itemgetter(1), reverse=True):
        print v, k.encode('utf-8')


if __name__ == "__main__":
    main()
