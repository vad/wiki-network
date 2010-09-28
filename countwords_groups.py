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

## etree
from lxml import etree

import sys
from bz2 import BZ2File
import re
#import cProfile as profile
from functools import partial
import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from sonet.graph import load as sg_load
from sonet import lib
import sonet.mediawiki as mwlib

## nltk
import nltk

## multiprocessing
from multiprocessing import Pipe, Process

count_utp, count_missing = 0, 0
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"
user_classes = None

### CHILD PROCESS
def get_freq_dist(recv, send, fd=None, classes=None):
    """
    recv and send are two Pipe connections.
    """
    from operator import itemgetter
    stopwords = frozenset(
        nltk.corpus.stopwords.words('italian')
        ).union(
            frozenset("[]':,(){}.?!")
        )
    tokenizer = nltk.PunktWordTokenizer()

    if not classes:
        classes = ('anonymous', 'bot', 'bureaucrat', 'sysop', 'normal user',
                   'all')

    # prepare a dict of empty FreqDist, one for class
    if not fd:
        fd = dict([(cls, nltk.FreqDist()) for cls in classes])

    while 1:
        try:
            cls, msg = recv.recv()
        except TypeError: ## end
            for cls, freq in fd.iteritems():
                send.send((cls, sorted(freq.items(),
                                       key=itemgetter(1),
                                       reverse=True)[:1000]))
            send.send(0)

            return

        tokens = tokenizer.tokenize(nltk.clean_html(msg.encode('utf-8')
                                                        .lower()))

        text = nltk.Text(t for t in tokens if t not in stopwords)
        fd[cls].update(text)
        fd['all'].update(text)


#def get_freq_dist_wrapper(q, done_q, fd=None):
#    profile.runctx("get_freq_dist(q, done_q, fd)",
#        globals(), locals(), 'profile')


### MAIN PROCESS
def process_page(elem, send):
    """
    send is a Pipe connection, write only
    """
    user = None
    title = None
    global count_utp, count_missing

    for child in elem:
        if child.tag == tag['title'] and child.text:
            title = child.text
            colon_idx = title.find(':')
            namespace = title[:colon_idx]

            if colon_idx > 0 and namespace in (en_user_talk, lang_user_talk):
                semititle = title[colon_idx+1:]
                a_semititle = semititle.split('/')
                if len(a_semititle) > 1: ##title is Namespace:User/Extra
                    extra_title = '/'.join(a_semititle[1:])
                    if not re.match('(?:archiv|vecch)', extra_title, re.I):
                        logging.warn('Discard page %s' % (
                            title.encode('utf-8')))
                        return
                user = a_semititle[0]
            else:
                return
        elif child.tag == tag['revision']:
            for rc in child:
                if rc.tag != tag['text']:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                try:
                    send.send((user_classes[user.encode('utf-8')], rc.text))
                except:
                    logging.warn("Exception with user %s, page %s" % (
                        user.encode('utf-8'), title.encode('utf-8')))
                    count_missing += 1

                count_utp += 1

                if not count_utp % 500:
                    print >> sys.stderr, count_utp


def main():
    import optparse

    p = optparse.OptionParser(
        usage="usage: %prog [options] dump enriched_pickle"
    )

    _, args = p.parse_args()

    if len(args) != 2:
        p.error("Too few or too many arguments")
    xml, rich_fn = args

    global lang_user_talk, lang_user, tag, user_classes
    ## pipe to send data to the  subprocess
    p_receiver, p_sender = Pipe(duplex=False)
    ## pipe to get elaborated data from the subprocess
    done_p_receiver, done_p_sender = Pipe(duplex=False)

    src = BZ2File(xml)

    tag = mwlib.getTags(src)
    lang, date, _ = mwlib.explode_dump_filename(xml)
    user_classes = dict(sg_load(rich_fn).get_user_class('username',
                                  ('anonymous', 'bot', 'bureaucrat','sysop')))

    p = Process(target=get_freq_dist, args=(p_receiver, done_p_sender))
    p.start()

    translations = mwlib.getTranslations(src)
    lang_user, lang_user_talk = translations['User'], translations['User talk']

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    ## open with a faster decompressor (probably this cannot seek)
    src.close()
    src = lib.BZ2FileExt(xml)

    partial_process_page = partial(process_page, send=p_sender)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page']),
                    partial_process_page)
    logging.info('Users missing in the rich file: %d' % (count_missing,))

    p_sender.send(0) ## this STOPS the process

    print >> sys.stderr, "end of parsing"

    while 1:
        try:
            cls, fd = done_p_receiver.recv()
        except TypeError:
            break

        with open("%swiki-%s-words-%s.dat" %
                  (lang, date,
                   cls.replace(' ', '_')), 'w') as out:
            for k, v in fd:
                print >> out, v, k

    p.join()

    print >> sys.stderr, "end of FreqDist"


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
