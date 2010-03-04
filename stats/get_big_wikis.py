#!/usr/bin/env python

def big_wikis():
    from csv import reader
    from urllib import urlopen
    
    f = urlopen('http://s23.org/wikistats/largest_csv.php?sort=good_desc,total_desc&th=10000&lines=500')
    r = reader(f)
    keys = r.next()
    keys = [e.strip() for e in keys]
    
    for l in r:
        yield dict(zip(keys, l))

def main():
    import os, sys
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_wikinetwork.settings'
    from django_wikinetwork.wikinetwork.models import BigWikiStat
    
    for wiki in big_wikis():
        # there can't be an id field in a Django model (it's the pk)
        if not wiki:
            continue
        
        wiki["_id"] = wiki["id"]
        del wiki["id"]
        if not wiki["activeusers"]:
            wiki["activeusers"] = 0

        bws = BigWikiStat(**wiki)
        
        bws.save()

if __name__ == "__main__":
    main()
    
    
