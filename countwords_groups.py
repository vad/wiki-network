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

from bz2 import BZ2File
import sys
#import cProfile as profile
from functools import partial
import logging
from collections import Counter
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
try:
    import re2 as re
except ImportError:
    logging.warn("pyre2 not available. It's gonna be a long job")
    import re

## multiprocessing
from multiprocessing import Pipe, Process

from sonet.graph import load as sg_load
from sonet import lib
import sonet.mediawiki as mwlib

## nltk
import nltk

count_utp, count_missing = 0, 0
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"
user_classes = None

### CHILD PROCESS

# smile dictionary
dsmile = {
    'happy': (r':[ -]?[)\]>]', r'=[)\]>]', r'\^[_\- .]?\^', 'x\)', r'\(^_^\)'),
    'sad': (r':[\- ]?[(\[<]', r'=[(\[<]'),
    'laugh': (r':[ -]?D', '=D'),
    'tongue': (':-?[pP]', '=[pP]', 'xP'),
    'normal': (r':[\- ]?\|',),
    'cool': (r'8[\- ]?\)',),
}

def build_smile_re(dsmile):
    out = {}
    for name, lsmile in dsmile.items():
        out[name] = re.compile(r'(?:(?:\s|^)%s)' % (r'|(?:\s|^)'.join(lsmile)))

    return out

re_smile = build_smile_re(dsmile)

## r argument is just for caching
def remove_templates(text, r=re.compile(r"{{.*?}}")):
    """
    Remove Mediawiki templates from given text:

    >>> remove_templates("hello{{template}} world")
    'hello world'
    >>> remove_templates("hello{{template}} world{{template2}}")
    'hello world'
    """
    return r.sub("", text)

## dsmile argument is just for caching
def find_smiles(text):
    """
    Find smiles in text and returns a dictionary of found smiles

    >>> find_smiles(':) ^^')
    {'happy': 2}
    >>> find_smiles('^^')
    {'happy': 1}
    >>> find_smiles(' :|')
    {'normal': 1}
    """
    res = {}
    for name, regex in re_smile.items():
        matches = len([1 for match in regex.findall(text) if match])

        if matches:
            res[name] = matches

    return res

def get_freq_dist(recv, send, fd=None, dcount_smile=None, classes=None):
    """
    Find word frequency distribution and count smile in the given text.

    Parameters
    ----------
    recv : multiprocessing.Connection
        Read only
    send : multiprocessing.Connection
        Write only
    fd : dict
        Word frequency distributions
    dcount_smile : dict
        Smile counters
    """
    from operator import itemgetter
    stopwords = frozenset(
        nltk.corpus.stopwords.words('italian')
        ).union(
            frozenset("[]':,(){}.?!*\"")
        ).union(
            frozenset(("==", "--"))
        )
    tokenizer = nltk.PunktWordTokenizer()

    if not classes:
        classes = ('anonymous', 'bot', 'bureaucrat', 'sysop', 'normal user',
                   'all')

    # prepare a dict of empty Counter, one for every class
    if not fd:
        fd = {cls: Counter() for cls in classes}
    if not dcount_smile:
        dcount_smile = fd = {cls: Counter() for cls in classes}

    while 1:
        try:
            cls, msg = recv.recv()
        except TypeError: ## end
            for cls in set(classes).difference(('all',)):
                fd['all'].update(fd[cls])
                dcount_smile['all'].update(dcount_smile[cls])

            send.send([(cls, sorted(freq.items(),
                                    key=itemgetter(1),
                                    reverse=True)[:1000])
                       for cls, freq in fd.iteritems()])
            send.send([(cls, sorted(counters.items(),
                                    key=itemgetter(1),
                                    reverse=True))
                       for cls, counters in dcount_smile.iteritems()])

            return

        msg = remove_templates(msg.encode('utf-8'))

        count_smile = find_smiles(msg)
        dcount_smile[cls].update(count_smile)

        tokens = tokenizer.tokenize(nltk.clean_html(msg.lower()))

        tokens = [t for t in tokens if t not in stopwords]
        fd[cls].update(tokens)


#def get_freq_dist_wrapper(recv, send, fd=None, dcount_smile=None, classes=None):
#    profile.runctx("get_freq_dist(recv, send, dcount_smile, classes)",
#        globals(), locals(), 'profile')


### MAIN PROCESS

def get_class(g, cls):
    if cls == 'all':
        users = g.g.vs
    elif cls == 'normal user':
        users = g.g.vs.select(**{'bot_ne': True, 'anonymous_ne': True,
                                 'sysop_ne': True,
                                 'bureaucrat_ne': True})
    else:
        users = g.g.vs.select(**{cls: True})
    return users

def process_page(elem, send):
    """
    send is a Pipe connection, write only
    """
    user = None
    global count_utp, count_missing

    for child in elem:
        if child.tag == tag['title'] and child.text:
            title = child.text

            try:
                user = mwlib.username_from_utp(title,
                                               (en_user_talk, lang_user_talk))
            except ValueError:
                return
        elif child.tag == tag['revision']:
            for rc in child:
                if rc.tag != tag['text']:
                    continue

                #assert user, "User still not defined"
                if not (rc.text and user):
                    continue

                user = user.encode('utf-8')
                try:
                    send.send((user_classes[user], rc.text))
                except KeyError:
                    ## fix for anonymous users not in the rich file
                    if mwlib.isip(user):
                        send.send(('anonymous', rc.text))
                    else:
                        logging.warn("Exception with user %s", user)
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

    tag = mwlib.get_tags(src)
    lang, date, _ = mwlib.explode_dump_filename(xml)
    g = sg_load(rich_fn)
    user_classes = dict(g.get_user_class('username',
                                  ('anonymous', 'bot', 'bureaucrat','sysop')))

    p = Process(target=get_freq_dist, args=(p_receiver, done_p_sender))
    p.start()

    translations = mwlib.get_translations(src)
    lang_user, lang_user_talk = translations['User'], translations['User talk']

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    ## open with a faster decompressor (probably this cannot seek)
    src.close()
    src = lib.BZ2FileExt(xml)

    partial_process_page = partial(process_page, send=p_sender)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page']),
                    partial_process_page)
    logging.info('Users missing in the rich file: %d', count_missing)

    p_sender.send(0) ## this STOPS the process

    print >> sys.stderr, "end of parsing"

    g.set_weighted_degree()
    users_cache = {}
    # get a list of pair (class name, frequency distributions)
    for cls, fd in done_p_receiver.recv():
        with open("%swiki-%s-words-%s.dat" %
                  (lang, date,
                   cls.replace(' ', '_')), 'w') as out:
            # users in this group
            try:
                users = users_cache[cls]
            except KeyError:
                users = get_class(g, cls)
                users_cache[cls] = users
            print >> out, '#users: ', len(users)
            print >> out, '#msgs: ', sum(users['weighted_indegree'])
            for k, v in fd:
                print >> out, v, k
    del fd

    for cls, counters in done_p_receiver.recv():
        with open("%swiki-%s-smile-%s.dat" %
                  (lang, date,
                   cls.replace(' ', '_')), 'w') as out:
            # users in this group
            try:
                users = users_cache[cls]
            except KeyError:
                users = get_class(g, cls)
                users_cache[cls] = users
            print >> out, '#users: ', len(users)
            print >> out, '#msgs: ', sum(users['weighted_indegree'])
            for k, v in counters:
                print >> out, v, k

    p.join()

    print >> sys.stderr, "end of FreqDist"


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
