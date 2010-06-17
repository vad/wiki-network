#!/usr/bin/env python
#coding=utf-8

import re
import urllib as ul
import sonetgraph as sg

from utils import iter_csv, print_csv

# Global vars
user_roles = None

vec_cal = {
    'Jan': ['xenaro', 'xen', 'gen', 'gennaio', 'jan', 'january']
    ,'Feb': ['febraro', 'feb', 'febbraio', 'february']
    ,'Mar': ['marso', 'mar', 'marzo', 'march', 'marzso']
    ,'Apr': ['avril', 'avr', 'aprile', 'apr', 'april', 'aprili']
    ,'May': ['majo', 'maj', 'maggio', 'mag', 'may']
    ,'Jun': ['giugno', 'giu', 'june', 'jun']
    ,'Jul': ['lujo', 'luj', 'luglio', 'lug', 'july', 'jul']
    ,'Aug': ['agosto', 'ago', 'august', 'aug']
    ,'Sep': ['setenbre', 'set', 'settembre', 'september', 'sep']
    ,'Oct': ['otobre', 'ottobre', 'oto', 'ott', 'october', 'oct']
    ,'Nov': ['novenbre', 'novembre', 'nov', 'november']
    ,'Dec': ['disenbre', 'dis', 'dicembre', 'dic', 'december', 'dec', 'diç', ul.unquote('diç')]
}

languages = {'it':'Italian','en':'English','de':'German','vec':'Venetian','es':'Spanish','eo':'Esperanto','fr':'French','fur':'Friulano','pt':'Portuguese','ro':'Romanian','la':'Latin','grc':'Ancient Greek','el':'Greek'}

header_list = ["Coder (Vad=1,  Marco = 2)","Owner","Owner's role","Writer","Clean writer","Writer's role","Signature yes=1, no=0","Signature findable by script 1=yes; 0=no","wiki content (0=no / 1=yes)","wiki rules (0=no / 1=yes)","Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5= personal, 6=other","Welcome message 1=yes; 0=no","Thanks 1=yes; 0=no","template: warning/vandalism/test 1=yes; 0=no","template: welcome 1=yes; 0=no","Information msg (0=no / 1=yes)","Redirect (0=no / 1=yes)","datetime","year","month","day","time","# of words","# of characters","# of characters without whitespace","Variazioni del “thanks”","Comments (language issues, signature missing or other)","original message"] + languages.values()


def enrich(v):

    global language

    if v['template: welcome 1=yes; 0=no'] == '1':
        v.update({
            'wiki content (0=no / 1=yes)': 0
            ,'wiki rules (0=no / 1=yes)': 1
            ,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5= personal, 6=other': 3
            ,'Welcome message 1=yes; 0=no': 1
            ,'Thanks 1=yes; 0=no': 0
            ,'template: warning/vandalism/test 1=yes; 0=no': 0
            ,'Information msg (0=no / 1=yes)': 0
            ,'Redirect (0=no / 1=yes)': 0
        })
    elif v['Information msg (0=no / 1=yes)'] == '1':
        v.update({
            'template: welcome 1=yes; 0=no': -999999
            ,'wiki content (0=no / 1=yes)': -999999
            ,'wiki rules (0=no / 1=yes)': -999999
            ,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5= personal, 6=other': -999999
            ,'Welcome message 1=yes; 0=no': -999999
            ,'Thanks 1=yes; 0=no': -999999
            ,'template: warning/vandalism/test 1=yes; 0=no': -999999
            ,'Redirect (0=no / 1=yes)': -999999
        })
    elif v['Redirect (0=no / 1=yes)'] == '1':
        v.update({
            'wiki content (0=no / 1=yes)': -999999
            ,'wiki rules (0=no / 1=yes)': -999999
            ,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5= personal, 6=other': -999999
            ,'Welcome message 1=yes; 0=no': -999999
            ,'Thanks 1=yes; 0=no': -999999
            ,'template: warning/vandalism/test 1=yes; 0=no': -999999
            ,'Information msg (0=no / 1=yes)': -999999
            ,'template: welcome 1=yes; 0=no': -999999
            ,'Signature yes=1, no=0': -99999
            ,'Signature findable by script 1=yes; 0=no': -99999
        })
    else:
        v.update({
            'Information msg (0=no / 1=yes)': 0
            ,'Redirect (0=no / 1=yes)': 0
        })

    om = v['original message']
    cm = v['Comments (language issues, signature missing or other)']

    try:
        lang = re.search('lang:((\w+[/,]?)*)', cm, re.IGNORECASE).groups()[0].split(',')
        for l in lang:
            if l not in languages and l != '':
                print "Why don\'t you consider me? I am a language too!", l
    except:
        lang = ['vec']

    for l,d in languages.iteritems():
        v[d] = int(l in lang)
    
    try:
        # Writer's role
        us = re.search(r'((?<=Utente[/:])|(?<=Discussion_utente[/:]))([^&]*)',v['Writer'], re.IGNORECASE)

        if us is not None:
            user = us.group()
        else:
            user = v['Writer']

        wrt_role = user_roles[ul.unquote(user.replace('_', ' '))]

    except (KeyError, AttributeError), e:
        if not v['Writer'] or v['Writer'] == '':
            user = 'NONE'
        else:
            user = v['Writer']
        wrt_role = 'NONE'

    try:
        # UTP owner's role
        u_role = user_roles[ul.unquote(v['Owner']).replace('_', ' ')]

    except KeyError, e:
        print e
        u_role = 'NONE'

    if not v['Owner'] or v['Owner'] == '':
        v['Owner']  = 'NONE'
    if not v['Writer'] or v['Writer'] == '':
        v['Writer']  = 'NONE'

    v.update({
        '# of words': len(om.split())
        ,'# of characters': len(om)
        ,'# of characters without whitespace': len(om.replace(' ',''))
        ,'Owner\'s role': u_role
        ,'Writer\'s role': wrt_role
        ,'Clean writer': user
        })

    dt = getdatetime(om)
    
    if dt is not None:
        v.update(dt)

    return v


def getdatetime(message):
    import time

    test = re.findall('\d{2}[/:]\d{2}[/:]\d{2}, ', message)
    if len(test):
        print "Warning! this date probably has a date with seconds too: %s - skipped" % (test,)
        return None
    
    test = re.findall('\d{2}[/:]\d{2} [a-zA-Z0-9]+', message)
    if len(test):
        print "Warning! this date probably has strange format: %s - skipped" % (test,)
        return None

    dates = re.findall('(\d{2}[/:]\d{2}, )?(\d{1,2} \w+ \d{2,4})( [/(]\w+[/)])?', message)

    if not len(dates):
        return None
    
    if len(dates) > 1:
        print "\nWARNING: double date\n\n%s\n" % (message,)
        d = pickdate(dates)
        #d = dates[-1]
    else:
        d = dates[0]

    # d is a tuple containing:
    # d[0] == hours (i.e. '07:23 ,')
    # d[1] == date (i.e. '23 Oto 2007')
    # d[2] == timezone (i.e. ' (UTC)')
        
    f = "%d/%m/%Y" # Output date format
    s = '%d %b %Y' # Input date format

    if d[0] is not None and d[0] != '':
        s = '%H:%M, ' + s
        f += ' %H:%M'

    if d[2] is not None and d[2] != '':
        s += ' (%Z)'

    try:
        # returning time converted in GMT time
        t = time.gmtime(time.mktime(time.strptime(d[0]+getmonth(d[1])+d[2], s)))
        return {
            'datetime': time.strftime(f,t)
            ,'year': t.tm_year
            ,'month': t.tm_mon
            ,'day': t.tm_mday
            ,'time': '%d:%d' % (t.tm_hour,t.tm_min,)
        }
    except Exception as e:
        print e
        return None


def getmonth(s):

    if s is not None:
        m = re.findall('[a-zA-Z]+', s)[0]
        for k, l in vec_cal.iteritems():
            if m.lower() in l:
                return s.replace(m, k)
        print "Warning! date discarded: %s" % (s,)

    return None


def pickdate(list):

    i = 1
    for l in list:
        print i, l
        i += 1

    try:
        return list[int(raw_input('Choose the correct date by typing the corresponding number: ')) - 1]
    except IndexError, e:
        print e
        return None


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter

    global user_roles

    op = OptionParser(usage="usage: %prog [options] src_file dest_dir pickle")

    op.add_option('-t', '--template-free', action="store_true", dest="temp_free",help="Template & company skipped")

    opts, args = op.parse_args()

    if not args:
        op.error("files & dir needed!")

    src = args[0] # source file name
    dest_dir = args[1] # dest dir name
    pickle = args[2] # pickle file name
    g = sg.load(pickle) #pickle loading
    
    # Saving users' roles in a dictionary with "username, role" as "key, value"
    user_roles = dict([e for e in g.getUserClass('username', ('anonymous', 'bot', 'bureaucrat', 'sysop'))])

    # copy inside a dictionary and enrich!
    r = {}
    for i, v in enumerate(iter_csv(src, True)):
        if opts.temp_free:
            if v['template: welcome 1=yes; 0=no'] == '1' or v['template: warning/vandalism/test 1=yes; 0=no'] == '1' or v['Information msg (0=no / 1=yes)'] == '1' or v['Redirect (0=no / 1=yes)'] == '1':
                continue

        r[i] = enrich(v)

    if opts.temp_free:
        dest = dest_dir + '/template_free_coding/'
    else:
        dest = dest_dir + '/complete_coding/'

    print_csv(r, dest+'coding_enriched.csv', header_list)

    return r


if __name__ == "__main__":
    d = main()
