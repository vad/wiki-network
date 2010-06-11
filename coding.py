#!/usr/bin/env python
#coding=utf-8

import csv, re

import sonetgraph as sg

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
    ,'Dec': ['disenbre', 'dis', 'dicembre', 'dic', 'december', 'dec', 'diç', 'di\xc3\xa7']
}


def print_csv(d, filename, header = None):

    print "Writing filename %s" % (filename,)

    try:
        with open(filename, 'w') as f:
            wr = csv.writer(f)

            if header is not None:
                wr.writerow(header)
            for k, v in d.iteritems():
                ls = []
                if header is not None:
                    for h in header:
                        ls.append(v[h])
                    wr.writerow(ls)
                else:
                    wr.writerow(v.values())
    except IOError, e:
        print e

    print "File %s saved" % (filename,)


def iter_csv(filename, _hasHeader = False):
    from csv import reader
    fieldNames = None

    print 'Reading from %s' % (filename,)

    try:
        cf = open(filename, 'rb')
    except IOError, e:
        print e

    try:
        lines = reader(cf)
    except IOError, e:
        print e[0], e[1]

    if _hasHeader:
        fieldNames = lines.next()
        
    for row in lines:
        d = {}
        for i, f in enumerate(row):
            if fieldNames:
                d[fieldNames[i]] = f
            else:
                d[i] = f
        yield d
    
    cf.close()

def enrich(v):
    import urllib as ul

    if v['template: welcome 1=yes; 0=no']:
        v.update({
            'wiki content (0=no / 1=yes)': 0
            ,'wiki rules (0=no / 1=yes)': 1
            ,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5=not wiki but personal, 6=not wiki and not personal': 3
            ,'Welcome message 1=yes; 0=no': 1
            ,'Thanks 1=yes; 0=no': 0
            ,'template: warning/vandalism/test 1=yes; 0=no': 0
            ,'Information msg (0=no / 1=yes)': 0
            ,'Redirect (0=no / 1=yes)': 0
        })
    elif v['Information msg (0=no / 1=yes)']:
        v.update({
            'template: welcome 1=yes; 0=no': 0
            #,'wiki content (0=no / 1=yes)': 0
            #,'wiki rules (0=no / 1=yes)': 0
            #,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5=not wiki but personal, 6=not wiki and not personal': 0
            #,'Welcome message 1=yes; 0=no': 0
            #,'Thanks 1=yes; 0=no': 0
            #,'template: warning/vandalism/test 1=yes; 0=no': 0
            #,'Redirect (0=no / 1=yes)': 0
        })
    elif v['Redirect (0=no / 1=yes)']:
        v.update({
            'wiki content (0=no / 1=yes)': 0
            ,'wiki rules (0=no / 1=yes)': 0
            ,'Intention: 1=Request info, 2=ask authorization, 3=coordination, 4=warnings, 5=not wiki but personal, 6=not wiki and not personal': 0
            ,'Welcome message 1=yes; 0=no': 0
            ,'Thanks 1=yes; 0=no': 0
            ,'template: warning/vandalism/test 1=yes; 0=no': 0
            ,'Information msg (0=no / 1=yes)': 0
            ,'template: welcome 1=yes; 0=no': 0
        })

    om = v['original message']
    
    try:
        # Writer's role
        u = ul.unquote(re.search(r'((?<=Utente[/:])|(?<=Discussion_utente[/:]))([^&]*)',v['Writer'], re.IGNORECASE).group().replace('_', ' '))
        wrt_role = user_roles[u]
    except (KeyError, AttributeError), e:
        print e, v['Writer']
        wrt_role = None

    try:
        # UTP owner's role
        u_role = user_roles[ul.unquote(v['Owner']).replace('_', ' ')]

    except KeyError, e:
        print e
        u_role = None

    v.update({
        'date of message': getdatetime(om)
        ,'# of words': len(om.split())
        ,'# of characters': len(om)
        ,'# of characters without whitespace': len(om.replace(' ',''))
        ,'Owner\'s role': u_role
        ,'Writer\'s role': wrt_role
    })

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
        return time.strftime(f,time.gmtime(time.mktime(time.strptime(d[0]+getmonth(d[1])+d[2], s))))
    except:
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

    return list[int(raw_input('Choose the correct date by typing the corresponding number: ')) - 1]


def main():
    from optparse import OptionParser

    global user_roles

    p = OptionParser(usage="usage: %prog [options] src_file dest_file pickle")
    opts, args = p.parse_args()

    if not args:
        p.error("files needed!")

    src = args[0] # source file name
    dest = args[1] # dest file name
    pickle = args[2] # pickle file name
    g = sg.load(pickle) #pickle loading
    
    # Saving users' roles in a dictionary with "username, role" as "key, value"
    user_roles = dict([e for e in g.getUserClass('username', ('anonymous', 'bot', 'bureaucrat', 'sysop'))])

    # copy inside a dictionary and enrich!
    r = {}
    for i, v in enumerate(iter_csv(src, True)):
        r[i] = enrich(v)

    print_csv(r, dest, r[0].keys())

    return r


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    d = main()
