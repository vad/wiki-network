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
import sys

## etree
from lxml import etree

## multiprocessing
from multiprocessing import Queue, Process

from sonet import mediawiki as mwlib
from sonet.graph import load as sg_load

count = 0
lang = None
old_user = None
g = None
lang_user, lang_user_talk = None, None
tag = {}
en_user, en_user_talk = u"User", u"User talk"
templates = {}
queue, done_queue = Queue(), Queue()



### CHILD PROCESS
def merge_templates(big, small):
    for k,v in small.iteritems():
        big.setdefault(k, 0) #set big[k] if not already defined
        big[k] += v


def get_freq_dist(q, done_q, templates=None):
    '''
    Accepts as input a queue q containing data to be analyzed
    done_q is a queue with returned results
    '''
    if not templates:
        templates = {}

    while 1:
        s = q.get()

        try:
            page_templates = mwlib.getTemplates(s)

            ##TODO: replace this with collections.Counter
            merge_templates(templates, page_templates)
        except TypeError: ## end
            done_q.put(templates)

            return


### MAIN PROCESS
def process_page(elem, queue=None):
    q = queue
    user = None
    global count

    for child in elem:
        if child.tag == tag['title'] and child.text:
            a_title = child.text.split('/')[0].split(':')

            if len(a_title) > 1 and a_title[0] in (en_user, lang_user):
            #if len(a_title) > 1 and a_title[0] == en_user:
                user = a_title[1]
            else:
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
                    q.put((user_classes[user], rc.text))
                except:
                    ## fix for anonymous users not in the rich file
                    if mwlib.isip(user):
                        send.send(('anonymous', rc.text))
                    else:
                        logging.warn("Exception with user %s", user)
                        count_missing += 1

                count += 1
                if not count % 500:
                    print >>sys.stderr, count


def main():
    from functools import partial
    import optparse
    from operator import itemgetter

    p = optparse.OptionParser(
        usage="usage: %prog [options] current_dump rich_graph"
    )
    _, files = p.parse_args()

    if len(files) != 2:
        p.error("Give me a file, please ;-)")
    xml_filename = files[0]
    rich_fn = files[1]

    global lang_user_talk, lang_user, tag, templates

    src = BZ2File(xml_filename)

    tag = mwlib.get_tags(src)

    translations = mwlib.get_translations(src)
    lang_user, lang_user_talk = translations['User'], translations['User talk']

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    user_classes = dict(sg_load(rich_fn).get_user_class('username',
                            ('anonymous', 'bot', 'bureaucrat','sysop')))

    p = Process(target=get_freq_dist, args=(queue, done_queue))
    p.start()

    ## XML Reader Process
    partial_process_page = partial(process_page, queue=queue)
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page']),
                    partial_process_page)

    print >>sys.stderr, "end of XML processing"

    queue.put(None) ## this STOPS the process
    templates = done_queue.get()
    p.join()

    for k, v in sorted(templates.items(), key=itemgetter(1), reverse=True):
        print v, k.encode('utf-8')


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
