#!/usr/bin/env python
#coding=utf-8

from edgecache import *
from lib import iter_csv, print_csv, ensure_dir
from sonet.mediawiki import normalize_pagename
import re
import sonetgraph as sg
import urllib as ul


#Global vars
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']
verbose = False


def getedges(_list, _selfedge=True, _year=None, wiki='', user_ns='', clean=False):
    """
    Prepare a dictionary of owner and writers, to be used to populate
    the network.

    Example: user A wrote 3 messages to user B,
    user C wrote 1 message to user B, user A wrote
    4 message to user C

    Returns:
    {
        'B': {
            'A': 3
            ,'C': 1
        }
        ,'C': {
            'A':4
        }
    }
    """
    d = {}

    for l in _list:
        writer = l['Writer']
        owner = l['Owner']
        year = l['year']
        signature = (l['Signature findable by script 1=yes; 0=no'] == '1')
        redirect = (l['Redirect (0=no / 1=yes)'] == '1')
        info_box = (l['Information msg (0=no / 1=yes)'] == '1')
        welcome_tpl = (l['template: welcome 1=yes; 0=no'] == '1')

        if _year and _year != year:
            continue
        if not _selfedge and writer == owner:
            continue

        # Add owner
        o = normalize_pagename(owner.decode('utf-8'))
        if o not in d:
            d[o] = {}

        if writer is None or writer == '' or writer == 'NONE':
            continue

        try:
            us = re.search(r'^%s.*(?<=%s[/:])([^&]*)' % (wiki, user_ns,), writer, re.IGNORECASE)
            if us is not None:
                user = us.groups()[0]
            else:
                if verbose:
                    print 'User %s not find' % (writer,)
                continue
        except (KeyError, AttributeError), e:
            print e
            continue

        w = normalize_pagename(ul.unquote(user).decode('utf-8'))

        if w not in d:
            d[w] = {}

        if info_box or redirect:
            continue

        if clean and not welcome_tpl:
            continue

        # Aggiungo l'edge oppure aumento il peso di uno esistente
        d[o][w] = (d[o]).get(w,0) + 1

    for k, v in d.iteritems():
        yield k, v


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter
    from os import path

    global verbose

    op = OptionParser(usage="usage: %prog [options] file")
    op.add_option('-c', '--clean', action="store_true", dest="clean",help="Skip message with signature not findable by script", default=False)
    op.add_option('-v', '--verbose', action="store_true", dest="verbose",help="Verbose output", default=False)
    op.add_option('-w', '--wiki', dest="wiki",help="wiki url", default='')
    op.add_option('-u', '--userns', dest="user_ns",help="User namespace, default \'Utente\'", default='Utente')
    op.add_option('-f', '--filename', dest="filename",help="Filename", default='network')

    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")

    verbose = opts.verbose

    f = args[0]
    dest = path.dirname(f) + '/'

    ec = EdgeCache()

    for writer,owner in getedges(_list=iter_csv(f, True), wiki=opts.wiki, user_ns=opts.user_ns, clean=opts.clean):
        ec.add(writer, owner)

    ec.flush()

    g = sg.Graph(ec.get_network())

    if verbose:
        print '\nCreating files'
    g.g.write_graphml(dest+opts.filename+'.graphml')
    g.g.write_pickle(dest+opts.filename+'.pickle')

    return g


if __name__ == "__main__":
    g = main()
