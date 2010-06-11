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
#import re
#from time import time
#from itertools import ifilter
import cProfile as profile
from functools import partial
from sonetgraph import load as sg_load
import lib

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
user_classes = None

## frequency distribution
stopwords = nltk.corpus.stopwords.words('italian')

### CHILD PROCESS
def get_freq_dist(q, done_q, fd=None, classes=None):
    dstpw = dict(zip(stopwords, [0]*len(stopwords)))
    tokenizer = nltk.PunktWordTokenizer()
    
    if not classes:
        classes = ('anonymous', 'bot', 'bureaucrat', 'sysop', 'normal user')

    # prepare a dict of empty FreqDist, one for every class
    if not fd:
        fd = dict(zip(classes,
                      [nltk.FreqDist() for _ in range(len(classes))]))
    
    while 1:
        try:
            cls, msg = q.get()
        except TypeError: ## end
            for cls, freq in fd.iteritems():
                done_q.put((cls, freq.items()))
            done_q.put(None)
            
            return
        
        tokens = tokenizer.tokenize(nltk.clean_html(msg.encode('utf-8')
                                                        .lower()))
            
        text = nltk.Text(t for t in tokens if len(t) > 2 and t not in dstpw)
        fd[cls].update(text)
        

def get_freq_dist_wrapper(q, done_q, fd=None):
    profile.runctx("get_freq_dist(q, done_q, fd)",
        globals(), locals(), 'profile')


### MAIN PROCESS
def process_page(elem, queue):
    user = None
    global count
    
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
                    queue.put((user_classes[user.encode('utf-8')], rc.text))
                    
                    count += 1
                    
                    if not count % 500:
                        print >> sys.stderr, count
                except:
                    print "Warning: exception with user %s" % (
                        user.encode('utf-8'),)
                    raise
    

def main():
    import optparse
    from operator import itemgetter

    p = optparse.OptionParser(usage="usage: %prog [options] file")

    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]

    global lang_user_talk, lang_user, tag, user_classes

    src = BZ2File(xml)

    tag = mwlib.getTags(src)
    lang, date = mwlib.explode_dump_filename(xml)
    path = os.path.split(xml)[0]
    if path:
        path += '/'
    rich_fn = "%s%swiki-%s_rich.pickle" % (path,
                                            lang, date)
    user_classes = dict(sg_load(rich_fn).getUserClass('username',
                                  ('anonymous', 'bot', 'bureaucrat','sysop')))
    
    p = Process(target=get_freq_dist, args=(queue, done_queue))
    p.start()

    lang_user, lang_user_talk = mwlib.getTranslations(src)

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"
    
    _fast = True
    if _fast:
        src.close()
        src = lib.BZ2FileExt(xml)

    partial_process_page = partial(process_page, queue=queue)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page']),
                    partial_process_page)
    
    queue.put(0) ## this STOPS the process
    
    print >> sys.stderr, "end of parsing"
    
    while 1:
        try:
            cls, fd = done_queue.get()
        except TypeError:
            break
        
        with open("%swiki-%s-words-%s.dat" %
                  (lang, date,
                   cls.replace(' ', '_')), 'w') as out:
            for k, v in sorted(fd, key=itemgetter(1), reverse=True):
                print >> out, v, k
        
    p.join()
    
    print >> sys.stderr, "end of FreqDist"


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
