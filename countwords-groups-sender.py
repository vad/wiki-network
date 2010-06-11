#!/usr/bin/env python2.6
#coding=utf-8

import sonetgraph as sg

user_roles = None


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
            
            
def iter_roletext(iterator):
    from operator import itemgetter
    from itertools import imap
    
    return imap(itemgetter("Writer's role", "original message"), iterator)
            
def main():
    from optparse import OptionParser

    global user_roles

    p = OptionParser(
        usage="usage: %prog [options] src_file dest_dir")
    _, args = p.parse_args()

    try:
        src = args[0]         # source file name
        dest = args[1]        # dest dir name
    except IndexError:
        p.error('Missing arguments')

    for e in iter_roletext(iter_csv(src, True)):
        print e


if __name__ == "__main__":
    main()
