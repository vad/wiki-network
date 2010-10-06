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

## PROJECT LIBS
from sonet.edgecache import EdgeCache
import sonet.mediawiki as mwlib
from sonet.mediawiki import PageProcessor
from sonet import lib
from sonet.timr import Timr

class CurrentPageProcessor(PageProcessor):
    """
    Inherits PageProcessor to process "current" dumps of wikipedia to find
    signatures on UTP.
    """
    _skip = False
    user = None
    sig_finder = None

    def __init__(self, *args, **kwargs):
        super(CurrentPageProcessor, self).__init__(*args, **kwargs)
        sf_kwargs = {'lang': self.lang}
        if 'signature' in kwargs:
            sf_kwargs['signature'] = kwargs['signature']

        self.sig_finder = mwlib.SignatureFinder(self.search, **sf_kwargs)

    def process_title(self, elem):
        text = elem.text
        if not text:
            self._skip = True
            return

        a_title = text.split('/')[0].split(':')

        if len(a_title) > 1 and a_title[0] in self.user_talk_names \
           and a_title[1]:
            self.user = a_title[1]
        else:
            self._skip = True

    def process_text(self, elem):
        assert self.user, "User still not defined"

        text = elem.text
        if not (text and self.user):
            return

        if (mwlib.isHardRedirect(text) or mwlib.isSoftRedirect(text)):
            return

        talks = self.sig_finder.find(text)

        self.ecache.add(mwlib.normalize_pagename(self.user), talks)
        self.count += 1
        if not self.count % 500:
            print self.count

    def process_page(self, _):
        """
        Called at the end of every <page> tag.
        """
        self._skip = False

    def end(self):
        self.ecache.flush()

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog file")
    p.add_option('-v', action="store_true", dest="verbose", default=False,
                 help="Verbose output (like timings)")
    p.add_option('-s', action="store", dest="signature", default=None,
                 help="Signature in this language (e.g. sig, firma..)")
    opts, files = p.parse_args()
    if opts.verbose:
        import sys, logging
        logging.basicConfig(stream=sys.stderr,
                            level=logging.DEBUG)

    try:
        xml = files[0]
    except KeyError:
        p.error("Give me one file, please")

    en_user, en_user_talk = u"User", u"User talk"

    lang, date, type_ = mwlib.explode_dump_filename(xml)

    src = BZ2File(xml)

    tag = mwlib.get_tags(src)

    ns_translation = mwlib.get_translations(src)
    lang_user, lang_user_talk = ns_translation['User'], \
             ns_translation['User talk']

    assert lang_user, "User namespace not found"
    assert lang_user_talk, "User Talk namespace not found"

    lang_user = unicode(lang_user)
    en_user = unicode(en_user)

    # open dump with an external process to use multiple cores
    _fast = True
    if _fast:
        src.close()
        src = lib.BZ2FileExt(xml)

    if opts.signature is not None:
        processor = CurrentPageProcessor(ecache=EdgeCache(), tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang,
                              signature=opts.signature)
    else:
        processor = CurrentPageProcessor(ecache=EdgeCache(), tag=tag,
                              user_talk_names=(lang_user_talk, en_user_talk),
                              search=(lang_user, en_user), lang=lang)

    with Timr('Processing'):
        processor.start(src)

    with Timr('Create network'):
        g = processor.ecache.get_network()

    print "Len:", len(g.vs)
    print "Edges:", len(g.es)

    g.write("%swiki-%s%s.pickle" % (lang, date, type_), format="pickle")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
