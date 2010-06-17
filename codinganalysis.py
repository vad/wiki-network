#!/usr/bin/env python
#coding=utf-8

import igraph
from codingenrich import iter_csv, print_csv

#Global vars
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']


def get_network(edges):

    def check_or_add(user):
        if user not in g.vs['user']:
            g.add_vertices(1)
            g.vs[len(g.vs)-1]['user'] = user

    g = igraph.Graph(n=0, directed=True)
    g.vs['user'] = []
    g.es['weight'] = []

    for writer, owner, weight in edges:
        check_or_add(writer)
        check_or_add(owner)

        e_from = g.vs['user'].index(writer)
        e_to = g.vs['user'].index(owner)

        g.add_edges((e_from, e_to))
        eid = g.get_eid(e_from, e_to, directed=True)
        g.es[eid]['weight'] = weight

    return g


def role_msg_matrix(_list, _dir):

    check_writer = {}
    check_owner = {}
    users_msg = {}
    users_received = {}
    users_msg_normalized = {}
    users_received_normalized = {}
    writers = {}

    for y in YEARS:
        check_writer[y] = {}
        check_owner[y] = {}
        writers[y] = {}
        users_msg[y] = {}
        users_received[y] = {}
        users_msg_normalized[y] = {}
        users_received_normalized[y] = {}
        for r in ROLES:
            check_writer[y][r] = []
            check_owner[y][r] = []
            writers[y][r] = 0
            users_msg[y][r] = 0
            users_received[y][r] = 0
            users_msg_normalized[y][r] = 0
            users_received_normalized[y][r] = 0

    for writer, owner, writer_role,owner_role, year in _list:
        if year not in YEARS:
            continue

        if writer_role in ROLES:
            if writer not in check_writer[year][writer_role]:
                check_writer[year][writer_role].append(writer)
            users_msg[year][writer_role] = (users_msg[year]).get(writer_role, 0) + 1

        if owner_role in ROLES:
            if owner not in check_owner[year][owner_role]:
                check_owner[year][owner_role].append(owner)
            users_received[year][owner_role] = (users_received[year]).get(owner_role, 0) + 1

    for y in YEARS:
        for r in ROLES:
            nw = len(check_writer[y][r])
            ow = len(check_owner[y][r])
            writers[y][r] = nw
            if nw:
                users_msg_normalized[y][r] = float(users_msg[y][r]) / nw
            else:
                users_msg_normalized[y][r] = 0
            if ow:
                users_received_normalized[y][r] = float(users_received[y][r]) / ow
            else:
                users_received_normalized[y][r] = 0

    print_matrix(writers, _dir+'user_writer_per_year_and_role.csv', writers['2008'].keys(), sorted(writers.keys()))
    print_matrix(users_msg, _dir+'msg_written_per_year_and_role.csv', users_msg['2008'].keys(), sorted(users_msg.keys()))
    print_matrix(users_msg_normalized, _dir+'msg_written_per_year_and_role_normalized.csv', users_msg_normalized['2008'].keys(), sorted(users_msg_normalized.keys()))
    print_matrix(users_received, _dir+'msg_received_per_year_and_role.csv', users_received['2008'].keys(), sorted(users_received.keys()))
    print_matrix(users_received_normalized, _dir+'msg_received_per_year_and_role_normalized.csv', users_received_normalized['2008'].keys(), sorted(users_received_normalized.keys()))


def talk_matrix(_list, _file, _year = None):
    d = {'normal user':0,'bot':0,'bureaucrat':0,'sysop':0,'anonymous':0}
    m = {}

    for k in d.keys():
        m[k] = d.copy()

    if _year:
        for writer, owner, year in _list:
            if year != _year:
                continue
            if writer in ROLES and owner in ROLES:
                m[writer][owner] = m[writer].get(owner, 0) + 1
    else:
        for writer, owner in _list:
            if writer in ROLES and owner in ROLES:
                m[writer][owner] = m[writer].get(owner, 0) + 1

    print_matrix(_dict=m, _file=_file)


def print_matrix(_dict, _file, _cols=None, _rows=None, _percentage=None):

    with open(_file, 'w') as f:

        if not _cols:
            _cols = _dict.keys()
        if not _rows:
            _rows = _dict.keys()

        print >>f, ','+','.join([k for k in _cols])+',total'
        
        for k in _rows:
            l = _dict[k].values()
            t = sum(l)
        
            if _percentage:
                if t:
                    p = [float(e)/t*100 for e in l]
                else:
                    p = [0] * len(l)
                tot = str(t)+ ' | 100%'
                list = ['%d | %.2f%%' % (x[0],x[1],) for x in zip(l,p)]
            else:
                list = [str(x) for x in l]
                tot = str(t)

            print >>f, k+','+','.join(list)+','+tot


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter
    from os import path

    global user_roles

    op = OptionParser(usage="usage: %prog [options] file")

    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")
        
    _dir = path.dirname(args[0]) + "/"

    r = {}
    for i, v in enumerate(iter_csv(args[0], True)):
        r[i] = v

    talk_matrix(imap(itemgetter("Writer's role", "Owner's role"), r.itervalues()), _dir+'msg_written_per_role.csv')
    for y in YEARS:
        talk_matrix(imap(itemgetter("Writer's role", "Owner's role", "year"), r.itervalues()), _dir+'msg_written_per_role_'+y+'.csv', y)

    role_msg_matrix(imap(itemgetter("Clean writer", "Owner", "Writer's role", "Owner's role", "year"), r.itervalues()), _dir)

    # Loading and printing network
    sg = get_network(imap(itemgetter("Clean writer", "Owner", "year"), r.itervalues()))
    sg.write_pajek(_dir+'network.net')

    return r


if __name__ == "__main__":
    d = main()
