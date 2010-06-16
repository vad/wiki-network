#!/usr/bin/env python
#coding=utf-8


#Global vars
YEARS = [2005, 2006, 2007, 2008, 2009]


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


def talk_matrix(_list, _file):
    d = {
        'normal user': 0
        ,'bot': 0
        ,'bureaucrat':0
        ,'sysop': 0
        ,'anonymous':0
    }
    m = {}

    for k in d.keys():
        m[k] = d.copy()

    for writer, owner in _list:
        if writer != 'NONE' and owner != 'NONE':
            m[writer][owner] = m[writer].get(owner, 0) + 1

    with open(_file, 'w') as f:
        print >>f, ','+','.join([k for k in m.keys()])+',total'
        
        for k in m.keys():
            l =  m[k].values()
            t = sum(l)
            if t:
                p = [float(e)/t*100 for e in l]
            else:
                p = [0] * len(l)
            #print >>f, k+','+','.join([str(x[0])+' | '+str(x[1])+'%' for x in zip(l,p)])+','+str(t)
            print >>f, k+','+','.join(['%d | %.2f' % (x[0],x[1],) for x in zip(l,p)])+','+str(t)

        #for k in d.keys():
            #t = sum([])



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

    talk_matrix(imap(itemgetter("Writer's role", "Owner's role"), r.itervalues()), _dir+'talk_matrix.csv')

    return r


if __name__ == "__main__":
    d = main()
