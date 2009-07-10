# -*- coding: utf-8 -*-
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

import re

def getCollaborators( rawWikiText, search, searchEn ):
    rex = '\[\[(%s|%s)\:([^]\|/]*)[^]]*\]\]' % (search, searchEn)
    matches = re.finditer(rex, rawWikiText)

    weights = {}
    for u in matches:
        un = u.group(2)
        weights[un] = weights.get(un, 0) + 1

    return weights


def addGroupAttribute(g, lang, group='bot'):
    try:
        import json
    except ImportError:
        import simplejson as json
    from urllib import urlopen
    url = 'http://%s.wikipedia.org/w/api.php?action=query&list=allusers&augroup=%s&aulimit=500&format=json' % ( lang, group)

    start = None
    while True:
        if start:
            url += '&aufrom=%s' % (start,)
        furl = urlopen(url)
        res = json.load(furl)

        if not res.has_key('query') or not res['query']['allusers']:
            print 'Group %s has errors or has no users' % group
            g.vs[group] = [None,]*len(g.vs)
            return g

        for user in res['query']['allusers']:
            print user['name'].encode('utf-8')
            try:
                g.vs.select(username=user['name'].encode('utf-8'))[0][group] = True
            except IndexError:
                pass
        
        if res.has_key('query-continue'):
            start = res['query-continue']['allusers']['aufrom']
        else:
            break

    return g

