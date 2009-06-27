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
import os, sys
import igraph as ig
from time import time

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
#g.vs['login'] = []
g.es['weight'] = []
usernames = {}
search = None
searchEn = None
lang = None

def addTalks(g, user, speakers):
    #start = time()
    def check_or_add(g, login):
        try:
            return usernames[login]
        except KeyError:
            g.add_vertices(1)
            idx = len(g.vs)-1
            usernames[login] = idx
            return idx
    
    #try:
    #    print "Add a talk to %s" % (user,)
    #except UnicodeError:
    #    print "Add a talk to someone with a strange name"
        
    e_to = check_or_add(g, user)
    for speaker,weight in speakers:
        e_from = check_or_add(g, speaker)
        try:
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] += weight
        except ig.core.InternalError:
            g.add_edges((e_from, e_to))
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] = weight
    #print "%.4f" % (time()-start,)

def process_page(elem, g):
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
                        #try:
                        if True:
                            talks = trustletlib.getCollaborators(rc.text, search, searchEn)
                            if talks:
                                addTalks(g, user, talks)
                            global count
                            count += 1
                            print count
                        #except:
                        #    print "Warning: exception with user %s" % (user,)
                    user = None


def fast_iter(context, func, g):
    for event, elem in context:
        func(elem, g)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context


def main():
    import re
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    
    opts, files = p.parse_args()
    
    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]
    print xml

    global lang
    global search, searchEn
    s = os.path.split(xml)[1]
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})-',s)
    date = '-'.join([res.group(x) for x in xrange(1,4)])
    search = unicode(i18n[lang][1])
    searchEn = unicode(i18n['en'][1])

    src = BZ2File(xml)

    fast_iter(etree.iterparse(src, tag=page_tag), process_page, g)

    g.vs['login'] = (None,)*len(g.vs)
    for username, idx in usernames.iteritems():
        g.vs[idx]['login'] = username.encode('utf-8')

    print "Len:", len(g.vs)

    g.write("out.graphmlz", format="graphmlz")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
