#!/usr/bin/env python
#coding=utf-8

from edgecache import *
from lib import iter_csv, print_csv, ensure_dir
from mwlib import capfirst
import re
import sonetgraph as sg
import urllib as ul


#Global vars
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']


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
        redirect = (l['Redirect (0=no / 1=yes)'] == '1')
        info_box = (l['Information msg (0=no / 1=yes)'] == '1')
        signature = (l['Signature findable by script 1=yes; 0=no'] == '1')

        if _year and _year != year:
            continue
        if not _selfedge and writer == owner:
            continue

        # Add owner
        o = capfirst(owner.decode('utf-8').replace('_', ' '))
        if o not in d:
            d[o] = {}

        if info_box or redirect:
            continue
        
        if clean and not signature:
            continue

        if writer is None or writer == '' or writer == 'NONE':
            continue

        try:
            us = re.search(r'^%s.*(?<=%s[/:])([^&]*)' % (wiki, user_ns,), writer, re.IGNORECASE)
            if us is not None:
                user = us.groups()[0]
            else:
                print 'User %s not find' % (writer,)
                continue
        except (KeyError, AttributeError), e:
            print e
            continue

        w = capfirst(ul.unquote(user).decode('utf-8').replace('_', ' '))
        d[o][w] = (d[o]).get(w,0) + 1

    for k, v in d.iteritems():
        yield k, v


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter
    from os import path

    _sfx = '' 

    op = OptionParser(usage="usage: %prog [options] file")
    op.add_option('-c', '--clean', action="store_true", dest="clean",help="Skip message with signature not findable by script", default=False)
    op.add_option('-w', '--wiki', dest="wiki",help="wiki url", default='')
    op.add_option('-u', '--userns', dest="user_ns",help="User namespace, default \'Utente\'", default='Utente')
    
    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")
    if opts.clean:
        _sfx = "_clean"
    
    _file = args[0]

    _dir = path.dirname(_file)
    dest = _dir + "/"
    ec = EdgeCache()

    for writer,owner in getedges(_list=iter_csv(_file, True), wiki=opts.wiki, user_ns=opts.user_ns, clean=opts.clean):
        ec.add(writer, owner)

    ec.flush()

    g = sg.Graph(ec.get_network())

    g.g.write_graphml(dest+'coding_network'+_sfx+'.graphml')
    g.g.write_pickle(dest+'coding_network'+_sfx+'.pickle')

    return g


if __name__ == "__main__":
    g = main()
