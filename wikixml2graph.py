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
import igraph as ig
from time import time

## etree
from lxml import etree

tag_prefix = u'{http://www.mediawiki.org/xml/export-0.3/}'

page_tag = tag_prefix + u'page'
title_tag = tag_prefix + u'title'
revision_tag = tag_prefix + u'revision'
text_tag = tag_prefix + u'text'

count = 0
search = None
searchEn = None
lang = None
old_user = None
ecache = None
g = None
lang_user, lang_user_talk = None, None
en_user, en_user_talk = u"User", u"User talk"

class EdgeCache:
    edges = []      # a list of tuples: [(sender_id, recipient_id, 20), ...]
    temp_edges = {} # a dict of dicts : {'recipient': {'sender1': 20, 'sender2': 2}}
    nodes = {}      # a dict of {'username': vertex_id}

    def cumulate_edge(self, user, talks):
        if not self.temp_edges.has_key(user):
            self.temp_edges[user] = talks
            return

        d = self.temp_edges[user]
        for speaker, msgs in talks.iteritems():
            d[speaker] = d.get(speaker, 0) + msgs


    def flush_cumulate(self):
        """
        This function assumes that all edges directed to the same node are present.

        For example you can call cumulate_edge twice with the same user, but in
        the meanwhile you can't call flush_cumulate()
        """

        for recipient, talk in self.temp_edges.iteritems():
            # find node with username recipient in self nodes
            # If not present add it; we give him the id rec_id
            rec_id = self.nodes.setdefault(recipient, len(self.nodes))

            for sender, msgs in talk.iteritems():
                send_id = self.nodes.setdefault(sender, len(self.nodes))
                self.edges.append((send_id, rec_id, msgs))

        self.temp_edges.clear()


    def get_network(self):
        """
        Get the resulting network and clean cached data
        """

        g = ig.Graph(n = 0, directed=True)
        g.es['weight'] = []
        g.vs['username'] = []

        g.add_vertices(len(self.nodes))

        for username, id in self.nodes.iteritems():
            g.vs[id]['username'] = username.encode('utf-8')
        self.nodes.clear()

        clean_edges = ((e[0], e[1]) for e in self.edges)
        g.add_edges(clean_edges)
        del clean_edges

        for e_from, e_to, weight in self.edges:
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] = weight
        self.edges = []

        return g


def process_page(elem, ecache):
    user = None
    global count
    for child in elem:
        if child.tag == title_tag and child.text:
            a_title = child.text.split('/')[0].split(':')

            if len(a_title) > 1 and a_title[0] in (en_user_talk, lang_user_talk):
                user = a_title[1]
            else:
                return
        elif child.tag == revision_tag:
            for rc in child:
                if rc.tag != text_tag:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                try:
                    talks = mwlib.getCollaborators(rc.text, search, searchEn)
                    ecache.cumulate_edge(user, talks)
                    count += 1
                    if not count % 500:
                        print count
                    #if count > 10000:
                    #    sys.exit(2)
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
    import re
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")

    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    global lang
    global search, searchEn, lang_user, lang_user_talk
    global g, ecache
    s = os.path.split(xml)[1] #filename with extension
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})-',s)
    date = ''.join([res.group(x) for x in xrange(1,4)])

    ecache = EdgeCache()

    src = BZ2File(xml)

    counter = 0
    for line in src:
        keys = re.findall(r'<namespace key="(\d+)">([^<]*)</namespace>', line)
        for key, ns in keys:
            if key == '2':
                lang_user = unicode(ns, 'utf-8')
            elif key == '3':
                lang_user_talk = unicode(ns, 'utf-8')

        counter += 1
        if counter > 50:
            break

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    src.seek(0)
    search = unicode(lang_user)
    searchEn = unicode(en_user)

    fast_iter(etree.iterparse(src, tag=page_tag), process_page, ecache)

    ecache.flush_cumulate()
    g = ecache.get_network()

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    #g.write("%swiki-%s.pickle" % (lang, date), format="pickle")
    g.write("%swiki-%s.graphml" % (lang, date), format="graphml")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
