#!/usr/bin/env python


#Copyright Paolo Massa paolo@gnuband.org, Davide Setti NAME.SURNAME@gmail.com
#GPLv3.0 licence - Free Software
# the script
# - gets statistics in json format from different wikipedias
#

import urllib2
from BeautifulSoup import BeautifulSoup
try:
    import json
except ImportError:
    import simplejson as json

AGENT = "Mozilla/5.0 (X11; U; Linux i686 (x86_64); it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6"


def get_stats_wikipedia(link):
    '''
    Return a list of tuples with (attribute,value). link is the base url,
    such as http://en.wikipedia.org
    '''
    wikipedia_base_url = "/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"
    url = link+wikipedia_base_url

    print "Get stats for ", link #, " at ", url

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', AGENT)]
    page = opener.open(url).read()

    stats = json.loads(page)['query']['statistics']

    return stats


def get_all_stats(wikis):
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
    from django_wikinetwork.wikinetwork.models import WikiStat

    for link, lang, family in wikis:
        try:
            stats = get_stats_wikipedia(link)
        except Exception, e:
            #print 'Exception on ', wiki_id
            print e
            continue

        # convert unicode keywords to string
        stats = dict(zip(map(str, stats.keys()), stats.values()))
        stats['lang'] = lang
        stats['family'] = family

        ws = WikiStat(**stats)
        ws.save()


def iter_project():
    site_matrix = "http://meta.wikimedia.org/wiki/Special:SiteMatrix"

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', AGENT)]
    page = opener.open(site_matrix)
    soup = BeautifulSoup(page)

    for tr in soup.find(id="mw-sitematrix-table").findAll(
        lambda tag: tag.name == 'tr' and not tag.get('style')):
        for td in tr.findAll('td'):
            a = td.find(lambda tag: tag.name == 'a' and
                        not tag.get('class') and not tag.get('id'))
            if a:
                link = a.get('href')
                lang, _type = (link.split('/')[-1]).split('.')[:2]
                yield (link, lang, _type)


if __name__ == "__main__":
    get_all_stats(iter_project())
