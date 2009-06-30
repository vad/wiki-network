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
#g = ig.Graph(n=0, directed=True)
#g.vs['login'] = []
#g.es['weight'] = []
usernames = {}
search = None
searchEn = None
lang = None
edges = []
old_user = None
elist = None

class EdgeList:
    edges = [] # a list of tuples: [('sender', 'recipient', 20), ...]
    temp_edges = {} # a dict of dicts : {'recipient': {'sender1': 20, 'sender2': 2}}

    def cumulate_edge(self, user, talks):
        if not self.temp_edges.has_key(user):
            self.temp_edges[user] = talks
            return
    
        d = self.temp_edges[user]
        for speaker, msgs in talks.iteritems():
            d[speaker] = d.get(speaker, 0) + msgs


    def flush_cumulate(self):
        for recipient, talk in self.temp_edges.iteritems():
            for sender, msgs in talk.iteritems():
                self.edges.append((sender, recipient, msgs))

        self.temp_edges.clear()


    def get_network(self):
        nodes = set(e[0] for e in self.edges).union(set(e[1] for e in self.edges))

        g = ig.Graph(n = 0, directed=True)
        g.es['weight'] = []
        
        g.add_vertices(len(nodes))
        
        dnodes = {}
        i = 0
        for node in nodes:
            dnodes[node] = i
            i += 1

        g.vs['username'] = list(node.encode('utf-8') for node in nodes)
        del nodes
        
        clean_edges = ((dnodes[e[0]], dnodes[e[1]]) for e in self.edges)
        g.add_edges(clean_edges)
        
        for e_from, e_to, weight in self.edges:
            eid = g.get_eid(dnodes[e_from], dnodes[e_to], directed=True)
            g.es[eid]['weight'] = weight

        return g


def process_page(elem, elist):
    user = None
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
                    #assert user, "User still not defined"
                    if rc.text and user:
                        #try:
                        #if True:
                        talks = trustletlib.getCollaborators(rc.text, search, searchEn)
                        if talks:
                            elist.cumulate_edge(user, talks)
                            #addTalks(elist, user, talks)
                        global count
                        count += 1
                        if not count%500:
                            print count
                        if count > 10000:
                            sys.exit(2)
                        #except:
                        #    print "Warning: exception with user %s" % (user,)


def fast_iter(context, func, elist):
    for event, elem in context:
        func(elem, elist)
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

    elist = EdgeList()

    src = BZ2File(xml)

    fast_iter(etree.iterparse(src, tag=page_tag), process_page, elist)

    elist.flush_cumulate()
    g = elist.get_network()

    #g.vs['login'] = (None,)*len(g.vs)
    #for username, idx in usernames.iteritems():
    #    g.vs[idx]['login'] = username.encode('utf-8')

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%s_out.graphmlz" % (lang,), format="graphmlz")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
