#!/usr/bin/env python
#coding=utf-8

from edgecache import *
from lib import iter_csv, print_csv, ensure_dir
from mwlib import capfirst
import re
import sonetgraph as sg
import urllib as ul


#Global vars
user_roles = None
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']


def getedges(_list, _selfedge=True, _year=None, wiki=''):
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
        info_msg = (l['Information msg (0=no / 1=yes)'] == '1')
        signature = (l['Signature findable by script 1=yes; 0=no'] == '1')

        if info_msg or redirect or not signature:
            continue

        if _year and _year != year:
            continue
        if not _selfedge and writer == owner:
            continue

        # Add owner
        o = capfirst(ul.unquote(owner).decode('utf-8').replace('_', ' '))
        if o not in d:
            d[o] = {}

        if writer is None or writer == '' or writer == 'NONE':
            continue

        try:
            us = re.search(r'^%s.*(?<=Utente[/:])([^&]*)' % wiki, writer, re.IGNORECASE)
            #us = re.search(r'((?<=Utente[/:])|(?<=Discussion_utente[/:]))([^&]*)', writer, re.IGNORECASE)
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


def getuserrole(user):
    try:
        return user_roles[user]
    except KeyError, e:
        print 'No role for user: %s' % (user,)
        return None


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter
    from os import path

    global user_roles

    op = OptionParser(usage="usage: %prog [options] file pickle")

    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")
    
    _file = args[0]
    _pickle = args[1] # pickle file name
    
    urg = sg.load(_pickle) # pickle loading
    
    # Saving users' roles in a dictionary with "username, role" as "key, value"
    user_roles = dict([e for e in urg.getUserClass('username', ('anonymous', 'bot', 'bureaucrat', 'sysop'))])

    _dir = path.dirname(_file)
    dest = _dir + "/"
    ec = EdgeCache()

    for writer,owner in getedges(_list=iter_csv(_file, True), wiki='http://vec.wikipedia.org'):
        ec.add(writer, owner)

    ec.flush()

    g = sg.Graph(ec.get_network())
    # Adding 'role' attribute to each vertex in the graph
    g.g.vs.set_attribute_values('role', map(lambda x: getuserrole(x), g.g.vs['username']))
    # 
    g.g.write_graphml(dest+'vec_only.graphml')
    g.g.write_pickle(dest+'vec_only.pickle')
    #g.g.write_pajek(dest_net+'network'+suff+'.net')
    
    # complete coding
    ec = EdgeCache()

    for writer,owner in getedges(_list=iter_csv(_file, True)):
        ec.add(writer, owner)

    ec.flush()

    g = sg.Graph(ec.get_network())
    # Adding 'role' attribute to each vertex in the graph
    g.g.vs.set_attribute_values('role', map(lambda x: getuserrole(x), g.g.vs['username']))
    # 
    g.g.write_graphml(dest+'coding.graphml')
    g.g.write_pickle(dest+'coding.pickle')
    #g.g.write_pajek(dest_net+'network'+suff+'.net')
    return g


if __name__ == "__main__":
    g = main()
