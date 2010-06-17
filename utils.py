#!/usr/bin/env python

import csv


def print_csv(d, filename, header=None, delimiter=","):

    print "Writing filename %s" % (filename,)

    try:
        with open(filename, 'w') as f:
            wr = csv.writer(f, delimiter=delimiter)

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
