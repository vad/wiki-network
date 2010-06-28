#!/usr/bin/env python
#coding=utf-8

from edgecache import *
from utils import iter_csv, print_csv, ensure_dir
import sonetgraph as sg
import urllib as ul
import numpy


#Global vars
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']


def getedges(_list, _selfedge=True, _year=None):

    d = {}

    for writer, owner, year in _list:
        if _year and _year != year:
            continue

        if writer == 'NONE' or owner == 'NONE':
            continue

        if not _selfedge and writer == owner:
            continue

        o = ul.unquote(owner.decode('utf-8'))
        w = ul.unquote(writer.decode('utf-8'))

        if o not in d:
            d[o] = {}

        d[o][w] = (d[o]).get(w,0) + 1

    for k, v in d.iteritems():
        yield k, v


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


def talker_matrix(_list, _file, _year = None):
    d = {'normal user':0,'bot':0,'bureaucrat':0,'sysop':0,'anonymous':0}
    l = {'normal user':[],'bot':[],'bureaucrat':[],'sysop':[],'anonymous':[]}
    check_writer = {}
    m = {}

    for k in d.keys():
        m[k] = d.copy()
        check_writer[k] = l.copy()

    for writer, owner, role_w, role_o in _list:
        if role_w in ROLES and role_o in ROLES:
            if writer in check_writer[role_w][role_o]:
                continue
            check_writer[role_w][role_o].append(writer)
            m[role_w][role_o] = m[role_w].get(role_o, 0) + 1

    print_matrix(_dict=m, _file=_file)



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


def fill_user_roles(_list):

    d = {}

    for writer, owner, wr, owr in _list:
        if wr not in d:
            d[wr] = []
        if owr not in d:
            d[owr] = [] 

        w = ul.unquote(writer.decode('utf-8'))
        o = ul.unquote(owner.decode('utf-8'))

        if [w,'sender'] not in d[wr]:
            d[wr].append([w, 'sender']) 

        if [o,'receiver'] not in d[owr]:
            d[owr].append([o,'receiver'])

    return d


def get_user_role(user, d):

    if user is None or user == '' or user == 'NONE':
        return None

    for k, v in d.iteritems():
        if user in [e[0] for e in v]:
            return k

    return None


def print_stats(d, file):

    with open(file, 'w') as f:

        print >>f, 'SENDERS BY TYPE'
        i = 0
        for k, v in d.iteritems():
            t = len([e for e in v if e[1] == 'sender'])
            i += t
            print >>f, '\t',k,str(t)
        print >>f, 'Total:', str(i)
        print >>f, '\nRECEIVERS BY TYPE'
        i = 0
        for k, v in d.iteritems():
            t = len([e for e in v if e[1] == 'receiver'])
            print >>f, '\t',k,str(t)
            i+= t
        print >>f, 'Total:', str(i)
        print >>f, '\nSENDERS + RECEIVERS'
        i = 0
        for k, v in d.iteritems():
            t = len(list(set([e[0] for e in v])))
            i += t
            print >>f, '\t',k,str(t)
        print >>f, 'Total:', str(i)


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter
    from os import path

    op = OptionParser(usage="usage: %prog [options] file1 [file2 ...]")

    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")

    results = {}
    wpy = {} # writers per year

    for x, file in enumerate(args):
        _dir = path.dirname(file)
        dest = _dir + "/" + _dir.split("/")[-1] + "_"

        r = {}
        for i, v in enumerate(iter_csv(file, True)):
            r[i] = v

        user_roles = fill_user_roles(imap(itemgetter("Clean writer", "Owner", "Writer's role", "Owner's role"), r.itervalues()))

        print_stats(user_roles, dest+'user_stats.txt')

        talker_matrix(imap(itemgetter("Clean writer", "Owner", "Writer's role", "Owner's role"), r.itervalues()), dest+'user_writer_per_role.csv')
        talk_matrix(imap(itemgetter("Writer's role", "Owner's role"), r.itervalues()), dest+'msg_written_per_role.csv')
        for y in YEARS:
            talk_matrix(imap(itemgetter("Writer's role", "Owner's role", "year"), r.itervalues()), dest+'msg_written_per_role_'+y+'.csv', y)

        role_msg_matrix(imap(itemgetter("Clean writer", "Owner", "Writer's role", "Owner's role", "year"), r.itervalues()), dest)

        # Networks!
        dest_net = dest + 'networks/'
        ensure_dir(dest_net)
        for y in [None]+YEARS:

            suff = '_'+y if y else '' # filename suffix

            # Loading and printing network
            ec = EdgeCache()
            for cw,o in getedges(imap(itemgetter("Clean writer", "Owner", "year"), r.itervalues()), _year=y):
                ec.add(cw, o)
            ec.flush()
            g = sg.Graph(ec.get_network("Label"))
            # Adding 'role' attribute to each vertex in the graph
            g.g.vs.set_attribute_values('role', map(lambda x: get_user_role(x.decode('utf-8'), user_roles), g.g.vs['Label']))
            # 
            g.g.write(dest_net+'network'+suff+'.graphml', format="graphml")
            #g.g.write(dest_net+'network'+suff+'.net', format="pajek")

            g.set_weighted_degree() # set weighted indegree
            g.g.vs['bw'] = g.g.betweenness(directed=True) # betweenness centrality for each vertex

            w_dg = numpy.average(numpy.array(g.g.vs.degree(type="in"))) # average indegree
            w_adg = numpy.average(numpy.array(g.g.vs['weighted_indegree'])) # average weighted indegree

            # print network stats
            with open(dest_net+'network'+suff+'_summary.txt', 'w') as f:
                print >>f, g.g.summary()
                print >>f, '\nAverage indegree: %f' % (w_dg,)
                print >>f, 'Average weighted indegree: %f' % (w_adg,)
                print >>f, '\nList of users (max 10) with higher betweenness centrality:'
                for vx in sorted([v for v in g.g.vs(bw_gt=0.0)], key=lambda v: v['bw'], reverse=True)[0:10]:
                    print >>f, '\t', vx['Label'], vx['role'], vx['bw']


            if y is None: # complete network!
                wrts = [v[0] for v in zip(g.g.vs["Label"], g.g.outdegree()) if v[1]]
            else: # Analysing one particular year -> y
                wpy[y] = [v[0] for v in zip(g.g.vs["Label"], g.g.outdegree()) if v[1]]

        with open(dest+'writers_per_year.csv', 'w') as f:
            print >>f, ',%s, total' % (','.join(YEARS))
            for w in sorted(wrts):
                l = [int(w in wpy[y]) for y in YEARS]
                t = sum(l)
                if t:
                    print >>f, '%s,%s,%d' % (w, ','.join([str(e) for e in l]),t,)
            
        print "Analysis for %s completed. File saved in directory %s" % (file, _dir,)

        results[x] = r

    return results


if __name__ == "__main__":
    d = main()
