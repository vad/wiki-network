#Copyright Paolo Massa paolo@gnuband.org
#GPLv3.0 licence - Free Software
# the script
# - gets statistics in json format from different wikipedias
# 
import urllib2,simplejson

def get_stats_wikipedia(wiki_id):
    '''Return a list of tuples with (attribute,value). wiki_id is the id of the wiki such as en or it or simple'''
    wikipedia_base_url = ".wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"
    url = "http://"+wiki_id+wikipedia_base_url

    print "Get stats for ",wiki_id," at ",url

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'PhaulyWikipediaStatisticsCollecter/0.1')]
    page = opener.open( url ).read()
    
    #print page
    stats = simplejson.loads(page)['query']['statistics']

    return stats

def get_all_stats(list_wiki_ids):
    stats = {}
    for wiki_id in list_wiki_ids:
        stats[wiki_id] = get_stats_wikipedia(wiki_id)
    return stats

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
        'he',
        'no',
        'ru',
        'sv',
    ]
    stats = get_all_stats(list_wiki_ids)
    print stats
