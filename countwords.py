#!/usr/bin/env python

##########################################################################
#                                                                        #
#  This program is free software; you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation; version 2 of the License.               #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
##########################################################################

from bz2 import BZ2File
import mwlib
import os, sys
import re
from time import time
from itertools import ifilter
import cProfile as profile

## etree
from lxml import etree


## nltk
import nltk

## multiprocessing
from multiprocessing import Queue, Process

count = 0
lang = None
old_user = None
g = None
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"
queue, done_queue = Queue(), Queue()

## frequency distribution
stopwords = nltk.corpus.stopwords.words('italian')

### CHILD PROCESS
def get_freq_dist(q, done_q, fd=None):
    global stopwords
    dstpw = dict(zip(stopwords, [0]*len(stopwords)))
    tokenizer = nltk.PunktWordTokenizer()

    if not fd:
        fd = nltk.FreqDist()
    
    while 1:
        s = q.get()
        
        try:
            tokens = tokenizer.tokenize(nltk.clean_html(s.encode('utf-8')
                                                        .lower()))
        except AttributeError: ## end
            done_q.put(fd.items())
            
            return
            
        text = nltk.Text(t for t in tokens if len(t) > 2 and t not in dstpw)
        fd.update(text)
        

def get_freq_dist_wrapper(q, done_q, fd=None):
    profile.runctx("get_freq_dist(q, done_q, fd)",
        globals(), locals(), 'profile')


### MAIN PROCESS
def process_page(elem, queue):
    user = None
    global count, it_stopwords
    
    for child in elem:
        if child.tag == tag['title'] and child.text:
            a_title = child.text.split('/')[0].split(':')

            try:
                if a_title[0] in (en_user_talk, lang_user_talk):
                    user = a_title[1]
                else:
                    return
            except KeyError:
                return
        elif child.tag == tag['revision']:
            for rc in child:
                if rc.tag != tag['text']:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                try:
                    queue.put(rc.text)
                    
                    count += 1
                    
                    if not count % 500:
                        print >>sys.stderr, count
                except:
                    print "Warning: exception with user %s" % (
                        user.encode('utf-8'),)
                    raise
    

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")

    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    global templates
    global lang_user_talk, lang_user, tag

    src = BZ2File(xml)

    tag = mwlib.getTags(src)
    
    p = Process(target=get_freq_dist, args=(queue, done_queue))
    p.start()

    lang_user, lang_user_talk = mwlib.getTranslations(src)

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    mwlib.fast_iter_queue(etree.iterparse(src, tag=tag['page']),
                          process_page, queue)
    
    queue.put(0) ## this STOPS the process
    
    print >>sys.stderr, "end of parsing"
    
    fd = done_queue.get()
    p.join()
    
    print >>sys.stderr, "end of FreqDist"
    
    for k, v in sorted(fd,cmp=lambda x,y: cmp(x[1], y[1]), reverse=True):
        print v, k


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
