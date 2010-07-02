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

    
def fast_iter(context, func):
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

def isHardRedirect(rawWikiText):
    """
    >>> isHardRedirect("   #REDIRECT [[User:me]]")
    True
    >>> isHardRedirect("[[User:me]]")
    False
    """
    rex = r'[\n ]*#REDIRECT[\n ]*\[\[[^]]*\]\]'
    return re.match(rex, rawWikiText) is not None
    

re_cache = {}
def getCollaborators(rawWikiText, search):
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

    """
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
        un = capfirst(unicode(u.group(2)).replace('_', ' '))
        weights[un] = weights.get(un, 0) + 1

    return weights


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
            keys = re.findall(r'<namespace key="(\d+)">([^<]*)</namespace>',
                              line)
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


def explode_dump_filename(fn):
    """
    >>> explode_dump_filename( \
            "/tmp/itwiki-20100218-pages-meta-current.xml.bz2")
    ('it', '20100218')
    """
    from os.path import split
    
    s = split(fn)[1] #filename with extension
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})-', s)
    date = ''.join([res.group(x) for x in range(1, 4)])
    return (lang, date)
    

def capfirst(s):
    """
    Given a string, it returns the same string with the first letter capitlized

    >>> capfirst("test")
    'Test'
    """
    return s[0].upper() + s[1:]


if __name__ == "__main__":
    getCollaborators('d [[User:you|mee:-)e/e]] d [[User:me]][[utente:me]]', \
        ('utente', 'user'))