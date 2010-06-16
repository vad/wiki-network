#!/usr/bin/env python
#coding=utf-8


#Global vars
YEARS = ['2005', '2006', '2007', '2008', '2009']
ROLES = ['bureaucrat', 'normal user', 'bot', 'anonymous', 'sysop']


def print_csv(d, filename, header = None, delimiter = ","):

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
                        if h in v.keys():
                            ls.append(v[h])
                        else:
                            ls.append(None)
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

def role_msg_matrix(_list, _dir):

    check_writer = {}
    check_owner = {}
    users = {}
    users_msg = {}
    users_received = {}

    for y in YEARS:
        check_writer[y] = []
        check_owner[y] = []
        users[y] = {}
        users_msg[y] = {}
        users_received[y] = {}
        for r in ROLES:
            users[y][r] = 0 
            users_msg[y][r] = 0
            users_received[y][r] = 0

    for writer, owner, writer_role,owner_role, year in _list:
        
        if year not in YEARS:
            continue

        if writer_role in ROLES:

            if writer not in check_writer[year]:
                check_writer[year].append(writer)
                users[year][writer_role] = (users[year]).get(writer_role, 0) + 1

            users_msg[year][writer_role] = (users_msg[year]).get(writer_role, 0) + 1

        if owner_role in ROLES:

            if owner not in check_owner[year]:
                check_writer[year].append(owner)

            users_received[year][owner_role] = (users_received[year]).get(owner_role, 0) + 1
    
    #print_matrix(users, _dir+'users_msg_count_per_year_and_role.csv')
    #print_matrix(users_msg, _dir+'written_msg_count_per_year_and_role.csv')
    #print_matrix(users_received, _dir+'received_msg_count_per_year_and_role.csv')


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

    print_matrix(m, _file)


def print_matrix(d, _file):

    with open(_file, 'w') as f:
        sk = sorted(d.keys())
        print >>f, ','+','.join([k for k in sk])+',total'
        
        for k in sk:
            print k
            l =  [d[k][j] for j in d[k]]
            t = sum(l)
            if t:
                p = [float(e)/t*100 for e in l]
            else:
                p = [0] * len(l)
            print >>f, k+','+','.join(['%d | %.2f' % (x[0],x[1],) for x in zip(l,p)])+','+str(t)+ ' | 100%'


def main():
    from optparse import OptionParser
    from itertools import imap
    from operator import itemgetter

    global user_roles

    op = OptionParser(usage="usage: %prog [options] file")

    opts, args = op.parse_args()

    if not args:
        op.error("Need a file to run analysis")
        
    _dir = args[0][0:-10]

    r = {}
    for i, v in enumerate(iter_csv(args[0], True)):
        r[i] = v

    talk_matrix(imap(itemgetter("Writer's role", "Owner's role"), r.itervalues()), _dir+'talk_matrix_complete.csv')
    for y in YEARS:
        talk_matrix(imap(itemgetter("Writer's role", "Owner's role", "year"), r.itervalues()), _dir+'talk_matrix_'+y+'.csv', y)

    role_msg_matrix(imap(itemgetter("Writer", "Owner", "Writer's role", "Owner's role", "year"), r.itervalues()), _dir)

    return r


if __name__ == "__main__":
    d = main()
