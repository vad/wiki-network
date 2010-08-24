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
import sys
from socket import inet_ntoa, inet_aton, error
from urllib import urlopen
from collections import namedtuple

from pageprocessor import PageProcessor, HistoryPageProcessor

try:
    import json
except ImportError:
    import simplejson as json


def fast_iter(context, func):
    """
    Use this function with etree.iterparse().

    See http://www.ibm.com/developerworks/xml/library/x-hiperfparse/ for doc.
    """
    for _, elem in context:
        func(elem)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
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


def isSoftRedirect(rawWikiText):
    r"""
    Find if the page starts with a soft redirect template

    >>> isSoftRedirect("{{softredirect|User:bot}}")
    True
    >>> isSoftRedirect("\n\n{{\nsoftredirect \n |  :en:User talk:bot}}")
    True
    >>> isSoftRedirect("{{ softredirect}}")
    False
    >>> isSoftRedirect("some text {{softredirect|:en:User talk:bot}}")
    False
    """
    rex = r'^[\n ]*{{[\n ]*softredirect[\n ]*\|[^}\n]*\}\}'
    return re.match(rex, rawWikiText) is not None

def is_archive(pagetitle):
    """
    Test whether a page is an archive or not
    (i.e. it contains a '/' in its title

    >>> is_archive('7_July_2005_London_bombings')
    False
    >>> is_archive('7_July_2005_London_bombings/Archive_2')
    True
    >>> is_archive('7_July_2005_London_bombings\/Archive_2')
    True
    >>> is_archive('7_July_2005_London_bombings/Archive_2/Some/thing/else')
    True
    """
    return bool(pagetitle.count('/'))

def isHardRedirect(rawWikiText):
    """
    >>> isHardRedirect("   #REDIRECT [[User:me]]")
    True
    >>> isHardRedirect("[[User:me]]")
    False
    """
    rex = r'[\n ]*#REDIRECT[\n ]*\[\[[^]]*\]\]'
    return re.match(rex, rawWikiText) is not None

## re_cache is a mutable, so it keeps state through function calls
def getCollaborators(rawWikiText, search, lang=None, re_cache = {}):
    """
    Search for regular expression containing [[User:username|anchor text]] and
    count a new message from username to the owner of the page. It also works
    on localized versions of the wikipedia, for example in the Italian
    Wikipedia it searches for
    [[Utente:username|anchor text]]

    We choose to get [[User:username|anchor text]] and not the
    User_discussion:username link for the following reason: signatures can be
    personalized.

    We rely on policies for signatures in the different Wikipedias.
    In English Wikipedia, see
    http://en.wikipedia.org/wiki/Wikipedia:Signatures#Links "Signatures must
    include at least one internal link to your user page, user talk page, or
    contributions page; this allows other editors easy access to your talk
    page and contributions log. The lack of such a link is widely viewed as
    obstructive." In Italian wikipedia, see
    http://it.wikipedia.org/wiki/Aiuto:Personalizzare_la_firma#Personalizzare_la_firma
    "La firma deve sempre contenere un wikilink alla pagina utente e/o alla
    propria pagina di discussione."

    >>> getCollaborators( \
            'd [[User:you|mee:-)e/e]] d [[User:me]][[utente:me]]', \
                         ('Utente', 'User'))
    {u'Me': 2, u'You': 1}
    >>> getCollaborators('[[User:you', ('Utente', 'User'))
    {}
    >>> getCollaborators('[[Utente:me/archive|archive]]', ('Utente', 'User'))
    {}
    >>> getCollaborators('[[:vec:Utente:me|or you]]', ('Utente', 'User'), \
            'vec')
    {u'Me': 1}

    """
    if lang:
        search += tuple([":%s:%s" % (lang, s) for s in search])
    rex = r'\[\[(%s):([^/]*?)[|\]][^\]]*\]' % ('|'.join(search),)
    try:
        matches = re_cache[rex].finditer(rawWikiText)
    except KeyError:
        re_cache[rex] = re.compile(rex, re.IGNORECASE)
        matches = re_cache[rex].finditer(rawWikiText)

    weights = dict()
    for u in matches:
        ##TODO: fare un test per controllare che questo continui a funzionare
        ##      (nomi utenti strani da correggere con capfirst e replace)
        u2 = u.group(2)
        if not u2:
            print >>sys.stderr, 'getCollaborators: empty username found'
            continue
        un = capfirst(unicode(u2).replace('_', ' '))
        weights[un] = weights.get(un, 0) + 1

    return weights


##TODO: add doctests
def getTemplates(rawWikiText):
    rex = '\{\{(\{?[^\}\|\{]*)'
    matches = re.finditer(rex, rawWikiText)

    weights = dict()
    for tm in matches:
        t = tm.group(1)
        weights[t] = weights.get(t, 0) + 1

    return weights


#def getWords(rawWikiText):
#    import nltk

def addGroupAttribute(g, lang, group='bot'):
    url = ('http://%s.wikipedia.org/w/api.php?action=query&list=allusers'+
           '&augroup=%s&aulimit=500&format=json') % (lang, group)

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
                g.vs.select(username=user['name'].encode('utf-8')
                            )[0][group] = True
            except IndexError:
                pass

        if res.has_key('query-continue'):
            start = res['query-continue']['allusers']['aufrom']
        else:
            break

    return


def addBlockedAttribute(g, lang):
    g.vs['blocked'] = [None,]*len(g.vs)
    url = base_url = ('http://%s.wikipedia.org/w/api.php?action=query&list='+
                      'blocks&bklimit=500&format=json') % ( lang, )

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


def getTags(src, tags='page,title,revision,text'):
    # find namespace (eg: http://www.mediawiki.org/xml/export-0.3/)
    try:
        root = src.readline()
        ns = unicode(re.findall(r'xmlns="([^"]*)', root)[0])

        tag_prefix = u'{%s}' % ns

        tag = {}
        for t in tags.split(','):
            tag[t] = tag_prefix + unicode(t)
    finally:
        src.seek(0)

    return tag


def getTranslations(src):
    try:
        counter = 0
        translation = {}

        while 1:
            line = src.readline()
            if not line: break
            keys = re.findall(
                r'<namespace key="(\d+)"[^>]*>([^<]*)</namespace>',
                line)
            for key, ns in keys:
                if key == '1':
                    translation['Talk'] = unicode(ns, 'utf-8')
                if key == '2':
                    translation['User'] = unicode(ns, 'utf-8')
                elif key == '3':
                    translation['User talk'] = unicode(ns, 'utf-8')
                elif key == '4':
                    translation['Wikipedia'] = unicode(ns, 'utf-8')

            counter += 1
            if counter > 50:
                break
    finally:
        src.seek(0)

    return translation

def getNamespaces(src):
    try:
        counter = 0
        namespaces = []

        while 1:
            line = src.readline()
            if not line: break
            keys = re.findall(r'<namespace key="(\d+)"[^>]*>([^<]*)</namespace>',
                              line)
            for key, ns in keys:
                namespaces.append((key, ns))

            counter += 1
            if counter > 40:
                break
    finally:
        src.seek(0)

    return namespaces


def explode_dump_filename(fn):
    """
    >>> explode_dump_filename( \
            "/tmp/itwiki-20100218-pages-meta-current.xml.bz2")
    ('it', '20100218', '-pages-meta-current')
    """
    from os.path import split

    s = split(fn)[1] #filename with extension
    res = re.search('(.*?)wiki[\-]*-(\d{8})([^.]*)', s)
    return (res.group(1), res.group(2), res.group(3))


def capfirst(s):
    """
    Given a string, it returns the same string with the first letter capitlized

    >>> capfirst("test")
    'Test'
    """
    return s[0].upper() + s[1:]


def count_renames(lang):
    url = base_url = ('http://%s.wikipedia.org/w/api.php?action=query&list='+\
                      'logevents&letype=renameuser&lelimit=500&leprop='+ \
                      'title|type|user|timestamp|comment|details&format=json'
                      ) % ( lang, )
    counter = 0
    start = None
    while True:
        if start:
            url = '%s&lestart=%s' % (base_url, start)
        furl = urlopen(url)
        res = json.load(furl)

        if not res.has_key('query') or not res['query']['logevents']:
            print 'No logs'
            return

        counter += len(res['query']['logevents'])

        if res.has_key('query-continue'):
            start = res['query-continue']['logevents']['lestart']
        else:
            break
        print counter

    return counter

Message = namedtuple('Message', 'time welcome')