#!/usr/bin/env python


#Copyright Paolo Massa paolo@gnuband.org
#GPLv3.0 licence - Free Software
# the script
# - gets statistics in json format from different wikipedias
# 


import urllib2
try:
    import json
except ImportError:
    import simplejson as json

def get_stats_wikipedia(wiki_id):
    '''Return a list of tuples with (attribute,value). wiki_id is the id of the wiki such as en or it or simple'''
    wikipedia_base_url = ".wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"
    url = "http://"+wiki_id+wikipedia_base_url

    print "Get stats for ",wiki_id," at ",url

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'PhaulyWikipediaStatisticsCollecter/0.1')]
    page = opener.open( url ).read()
    
    stats = json.loads(page)['query']['statistics']

    return stats

def get_all_stats(list_wiki_ids):
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
    from django_wikinetwork.wikinetwork.models import WikiStat
    
    for wiki_id in list_wiki_ids:
        stats = get_stats_wikipedia(wiki_id)
        
        # convert unicode keywords to string
        stats = dict(zip(map(str, stats.keys()), stats.values()))
        stats['lang'] = wiki_id
        print stats
        
        ws = WikiStat(**stats)
        ws.save()


if __name__ == "__main__":
    list_wiki_ids = [
        'en',
        'de',
        'fr',
        'it',
        'nl',
        'es',
        'pt',
        'ca',
        'eo',
        'commons',
        'simple',
        'la',
        'sq',
        'pms',
        'scn',
        'nap',
        'vec',
        'lmo',
        'co',
        'ia',
        'rm',
        'fur',
        'sco',
        'lij',
        'sc',
        'eml',
        'zh',
        'ja',
        'pl',
    ]
    get_all_stats(list_wiki_ids)
