#Copyright Paolo Massa paolo@gnuband.org
#GPLv3.0 licence - Free Software
# the script
# - gets statistics HTML pages from different wikipedias such as http://en.wikipedia.org/wiki/Special:Statistics , http://it.wikipedia.org/wiki/Special:Statistics , ...
# - parses the HTML page in order to extract the raw data
# 
# The alternative is to get data from the API but there is less information and in the meantime I started having fine with the small tech challenges I found along the way ;)
#  see http://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics
# 
import urllib2
from BeautifulSoup import BeautifulSoup          # For processing HTML
import locale
locale.setlocale(locale.LC_ALL,"")


def get_stats_wikipedia(wiki_id):
    '''Return a list of tuples with (attribute,value). wiki_id is the id of the wiki such as en or it or simple'''
    #if a locale for string syntax is not specified for a certain wiki, we use the deafult one (en_US)
    default_locale_for_wiki_id = "en_US"
    locale_for_wiki_id = {
        "it":"ro_RO", # the separator for it_IT is "" but in it.wikipedia.org they use "." so I need to specify it by hand in locale_for_wiki_id
        "es":"ro_RO",
        "nl":"ro_RO",
        "ca":"ro_RO",
    } 
    if wiki_id in locale_for_wiki_id:
        locale.setlocale(locale.LC_NUMERIC, locale_for_wiki_id[wiki_id])
    else:
        locale.setlocale(locale.LC_NUMERIC, default_locale_for_wiki_id)

    mw_statistics = {
        'name': 'mw-statistics', 
        'attributes': ['articles','pages','files','edits','edits-average','jobqueue','users','users-active']
    }
    statistics_group = {
        'name': 'statistics-group', 
        'attributes': ['bot','sysop','bureaucrat','checkuser',
            'steward','import','transwiki', # it seems it does not found these classes because in the HTML page they are in pair with another CSS class and I didn't find in one sec a way to have BeautifulSoup to work with these <tr class="statistics-group-steward statistics-group-zero"> ... but anyway if the class is not found the following check simply gets these numbers as N/A
            'uploader','ipblock-exempt','oversight','founder','rollbacker','accountcreator','autoreviewer','abusefilter']
    }
    wikipedia_base_url = "http://%s.wikipedia.org/wiki/Special:Statistics"
    url = wikipedia_base_url % wiki_id

    print "Get stats for ",wiki_id," at ",url

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'PhaulyWikipediaStatisticsCollecter/0.1')]
    page = opener.open( url ).read()
   
    soup = BeautifulSoup(page) #parse the page HTML text
    #print "code=",soup.originalEncoding
    import codecs
   
    ret = []

    for attribute in mw_statistics['attributes']:
        value = soup.find("tr", { "class" : mw_statistics['name']+"-"+attribute })
        #print value
        value = value.contents[1].contents
        value = value[0]

        value = value.replace(u'\xa0',''); #orrible hack, in fur.wikipedia.org numbers are in this format u'3\xa0765' for the number 3765, the 'thousands_sep' is this exoteric char so we escape it here for all the wikipedia (i.e. there is no control the wikipedia is the 'fur' one because this can be a problem for more than this wikipedia
        value = value.replace(u' ','');
        value = locale.atof(str(value))
        #print "  "+mw_statistics['name']+"-"+attribute+" = "+str(value)
        ret.append((mw_statistics['name']+"-"+attribute,value))

    for attribute in statistics_group['attributes']:
        value = soup.find("tr", { "class" : statistics_group['name']+"-"+attribute })
        if value:    
            value = value.contents[1].contents
            value = value[0]
            value = value.replace(u'\xa0',''); #orrible hack, in fur.wikipedia.org numbers are in this format u'3\xa0765' for the numb    er 3765, the 'thousands_sep' is this exoteric char so we escape it here for all the wikipedia (i.e. there is no control the wikipedia is the 'fur' one because this can be a problem for more than this wikipedia
            value = value.replace(u' ','');
            value = locale.atof(str(value[0]))
        else: # the class is not found (maybe because there are 2 CSS class in the same HTML element)
            value = 0.0
        #print "  "+mw_statistics['name']+"-"+attribute+" = "+str(value)
        ret.append((statistics_group['name']+"-"+attribute,value))
    return ret

def get_all_stats(list_wiki_ids):
    stats = {}
    for wiki_id in list_wiki_ids:
        stats[wiki_id] = get_stats_wikipedia(wiki_id)
    return stats

def pretty_print(stats):
    fw = 23
    print '|| wiki_id\t || '+(' || '.join([str(attr).ljust(fw)[:fw] for (attr,val) in stats[list_wiki_ids[0]]]))+" ||"
    for wiki_id in list_wiki_ids:
        print "|| "+wiki_id+'\t || '+(' || '.join([str(val).ljust(fw)[:fw] for (attr,val) in stats[wiki_id]]))+" ||"

if __name__ == "__main__":
    candidate_locales = ['es_UY', 'fr_FR', 'fi_FI', 'es_CO', 'pt_PT', 'it_IT',
                   'et_EE', 'es_PY', 'no_NO', 'nl_NL', 'lv_LV', 'el_GR', 'be_BY', 'fr_BE',
                   'ro_RO', 'ru_UA', 'ru_RU', 'es_VE', 'ca_ES', 'se_NO', 'es_EC', 'id_ID',
                   'ka_GE', 'es_CL', 'hu_HU', 'wa_BE', 'lt_LT', 'sl_SI', 'hr_HR', 'es_AR',
                   'es_ES', 'oc_FR', 'gl_ES', 'bg_BG', 'is_IS', 'mk_MK', 'de_AT', 'pt_BR',
                   'da_DK', 'nn_NO', 'cs_CZ', 'de_LU', 'es_BO', 'sq_AL', 'sk_SK', 'fr_CH',
                   'de_DE', 'br_FR', 'nl_BE', 'sv_FI', 'pl_PL', 'fr_CA', 'fo_FO',
                   'bs_BA', 'fr_LU', 'kl_GL', 'fa_IR', 'de_BE', 'sv_SE', 'it_CH', 'uk_UA',
                   'eu_ES', 'vi_VN', 'af_ZA', 'nb_NO', 'en_DK', 'tg_TJ', 'en_US']
    #for loc in candidate_locales:
    #    locale.setlocale(locale.LC_NUMERIC, loc)
    #    print "[",locale.localeconv()['thousands_sep'],"] is the separator between thousands in numbers for [",loc,"]"
    list_wiki_ids = [
        'nl',
        'de',
        'pt',
        'ca',
        'la',
        'eml',
        'scn',
        'sco',
        'vec',
        'lij',
        'lmo',
        'co',
        'pms',
        'nap',
        'sc',
        'rm',
        'eo',
        'ia',
        'sq',
        'simple',
        'commons',
        'es',
        'fr',
        'fur',
        'it',
        'en'
    ]
    stats = get_all_stats(list_wiki_ids)
    pretty_print(stats)
