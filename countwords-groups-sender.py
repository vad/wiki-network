#!/usr/bin/env python2.6
#coding=utf-8

"""
currently does not work
"""

import nltk
import sys
from operator import itemgetter

stopwords = nltk.corpus.stopwords.words('italian')
classes = ('anonymous', 'bot', 'bureaucrat', 'sysop', 'normal user')
tokenizer = nltk.PunktWordTokenizer()
## dictionary of frequency distributions
fd = dict(zip(classes, [nltk.FreqDist() for _ in range(len(classes))]))
dstpw = dict(zip(stopwords, [0]*len(stopwords)))

def freq_dist(cls, msg):
    global fd

    tokens = tokenizer.tokenize(nltk.clean_html(msg.lower()))

    text = nltk.Text(t for t in tokens if len(t) > 2 and t not in dstpw)
    fd[cls].update(text)


def iter_csv(filename, _hasHeader = False):
    from csv import reader
    fieldNames = None

    print 'Reading from %s' % (filename,)

    try:
        cf = open(filename, 'rb')
    except IOError, e:
        print e
        sys.exit(1)

    try:
        lines = reader(cf)
    except IOError, e:
        print e[0], e[1]
        sys.exit(1)

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
    from itertools import imap

    return imap(itemgetter("Owner's role", "original message"), iterator)
    #return imap(itemgetter("Writer's role", "original message"), iterator)


def main():
    from optparse import OptionParser

    p = OptionParser(
        usage="usage: %prog src_file dest_dir")
    _, args = p.parse_args()

    try:
        src = args[0]         # source file name
        dest = args[1]        # dest dir name
    except IndexError:
        p.error('Missing arguments')



    for cls, text in (
        (cls, text) for cls, text in iter_roletext(
            e for e in iter_csv(src, True)
            if e["template: welcome 1=yes; 0=no"] == "0"
            ) if cls):
        freq_dist(cls, text)

    for cls in classes:
        with open("%s/%s.dat" %
                  (dest, cls.replace(' ', '_')), 'w') as out:
            for k, v in sorted(fd[cls].items(), key=itemgetter(1),
                               reverse=True):
                print >> out, v, k


if __name__ == "__main__":
    main()
