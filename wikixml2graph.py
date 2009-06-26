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
import trustletlib
import os
import igraph as ig

## etree
from lxml import etree

#the right translation for "Discussion User" in the language in key
i18n = trustletlib.load('language_parameters', os.path.join( os.environ['HOME'], 'shared_datasets', 'WikiNetwork', 'languageparameters.c2' ), fault=False ) 

tag_prefix = u'{http://www.mediawiki.org/xml/export-0.3/}'

page_tag = tag_prefix + u'page'
title_tag = tag_prefix + u'title'
revision_tag = tag_prefix + u'revision'
text_tag = tag_prefix + u'text'
count = 0
g = ig.Graph(n=0, directed=True)
g.vs['login'] = []
g.es['weight'] = []

def count_discussion(text):
    return trustletlib.getCollaborators(text, i18n, lang)

def addTalks(user, speakers):
    def check_or_add(login):
        if login not in g.vs['login']:
            g.add_vertices(1)
            g.vs[len(g.vs)-1]['login'] = login
    try:
        print "Add a talk to %s" % (user.encode('utf-8'),)
    except UnicodeError:
        print "Add a talk to someone with a strange name"
        
    user = user.encode('utf-8')
    
    check_or_add(user)
    e_to = g.vs['login'].index(user)
    for speaker,weight in speakers:
        speaker = speaker.encode('utf-8')
        check_or_add(speaker)
        e_from = g.vs['login'].index(speaker)
        try:
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] += weight
        except ig.core.InternalError:
            g.add_edges((e_from, e_to))
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] = weight

def process_page(elem):
    for child in elem:
        if child.tag == title_tag and child.text:
            a_title = child.text.split('/')[0].split(':')
            if len(a_title) > 1 and a_title[0] == i18n[lang][0]:
                user = a_title[1]
            else:
                return
        elif child.tag == revision_tag:
            for rc in child:
                if rc.tag == text_tag:
                    assert user, "User still not defined"
                    if rc.text:
                        talks = count_discussion(rc.text)
                        if talks:
                            addTalks(user, talks)
                        global count
                        count += 1
                        print count
                    user = None


def fast_iter(context, func):
    for event, elem in context:
        func(elem)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context


if __name__ == "__main__":
    import re
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    
    opts, files = p.parse_args()
    
    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    s = os.path.split(xml)[1]
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})-',s)
    date = '-'.join([res.group(x) for x in xrange(1,4)])

    src = BZ2File(xml)

    fast_iter(etree.iterparse(src, tag=page_tag), process_page)

    g.write("out.graphmlz", format="graphmlz")

#cc = ''
#for event, elem in etree.iterparse(src, tag=page_tag):
#    if event == 'end' and elem.tag == page_tag:
#        process_page(elem)
#        #a_title = 
#        #if elem.findtext(title_tag) 
#        cc = elem
#        elem.clear()

