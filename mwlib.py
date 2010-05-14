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
from socket import inet_ntoa, inet_aton, error
from urllib import urlopen
try:
    import json
except ImportError:
    import simplejson as json

    
def fast_iter_queue(context, func, q):
    for event, elem in context:
        func(elem, q)
        elem.clear()
        #while elem.getprevious() is not None:
        #    del elem.getparent()[0]
    del context

    
def fast_iter(context, func):
    for event, elem in context:
        func(elem)
        elem.clear()
        #while elem.getprevious() is not None:
        #    del elem.getparent()[0]
    del context
    
def isip(s):
    """
    >>> isip("192.168.1.1")
    True
    >>> isip("not-an-ip")
    False
    """
    try:
        return inet_ntoa(inet_aton(s)) == s
    except error:
        return False


def getCollaborators( rawWikiText, search, searchEn ):
    """
    Search for regular expression containing [[User:username|anchor text]] and count
    a new message from username to the owner of the page. It also works on localized
    versions of the wikipedia, for example in the Italian Wikipedia it searches for
    [[Utente:username|anchor text]]

    We choose to get [[User:username|anchor text]] and not the User_discussion:username
    link for the following reason: signatures can be personalized.
    
    We rely on policies for signatures in the different Wikipedias.
    In English Wikipedia, see http://en.wikipedia.org/wiki/Wikipedia:Signatures#Links
    "Signatures must include at least one internal link to your user page, user talk
    page, or contributions page; this allows other editors easy access to your talk
    page and contributions log. The lack of such a link is widely viewed as
    obstructive." In Italian wikipedia, see
    http://it.wikipedia.org/wiki/Aiuto:Personalizzare_la_firma#Personalizzare_la_firma
    "La firma deve sempre contenere un wikilink alla pagina utente e/o alla propria
    pagina di discussione."
    
    >>> getCollaborators('d [[User:you|mee:-)ee]] d [[User:me]][[Utente:me]]', 'Utente', 'User')
    {'me': 2, 'you': 1}
    >>> getCollaborators('[[User:you', 'Utente', 'User')
    {}

    """
    rex = r'\[\[(%s|%s)\:([^]\|/]*)[^]/]*\]\]' % (search, searchEn)
    matches = re.finditer(rex, rawWikiText)

    weights = {}
    for u in matches:
        un = u.group(2)
        weights[un] = weights.get(un, 0) + 1

    return weights


def getTemplates(rawWikiText):
    rex = '\{\{(\{?[^\}\|\{]*)'
    matches = re.finditer(rex, rawWikiText)
    
    weights = {}
    for tm in matches:
        t = tm.group(1)
        weights[t] = weights.get(t, 0) + 1

    return weights


#def getWords(rawWikiText):
#    import nltk

def addGroupAttribute(g, lang, group='bot'):
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
            return

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

    return


def addBlockedAttribute(g, lang):
    g.vs['blocked'] = [None,]*len(g.vs)
    url = base_url = 'http://%s.wikipedia.org/w/api.php?action=query&list=blocks&bklimit=500&format=json' % ( lang, )

    start = None
    while True:
        if start:
            url = '%s&bkstart=%s' % (base_url, start)
        print "BLOCKED USERS: url = %s" % url
        furl = urlopen(url)
        res = json.load(furl)

        if not res.has_key('query') or not res['query']['blocks']:
            print 'No blocked users'
            return

        bk_list = []
        for block in res['query']['blocks']:
            if not block.has_key('user'):
                continue
            print block['user'].encode('utf-8')
            try:
                bk_list.append(block['user'].encode('utf-8'))
            except IndexError:
                pass

        bk_vs = g.vs.select(username_in=bk_list)
        bk_vs['blocked'] = (True,)*len(bk_vs)

        if res.has_key('query-continue'):
            start = res['query-continue']['blocks']['bkstart']
        else:
            break

    return


def getTags(src):
    # find namespace (eg: http://www.mediawiki.org/xml/export-0.3/)
    try:
        root = src.readline()
        ns = unicode(re.findall(r'xmlns="([^"]*)', root)[0])
        
        tag_prefix = u'{%s}' % ns
    
        tag = {}
        for t in 'page,title,revision,text'.split(','):
            tag[t] = tag_prefix + unicode(t)
    finally:
        src.seek(0)
    
    return tag


def getTranslations(src):
    try:
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
    finally:
        src.seek(0)
        
    return (lang_user, lang_user_talk)
