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
import os, sys
import igraph as ig
from mwlib import addGroupAttribute

def main():
    import re
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    
    opts, files = p.parse_args()
    
    if not files:
        p.error("Give me a file, please ;-)")
    fn = files[0]

    s = os.path.split(fn)[1]
    print s
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})',s)
    date = ''.join([res.group(x) for x in xrange(1,4)])

    g = ig.load(fn)

    groups = ('bot', 'sysop', 'bureaucrat', 'checkuser', 'steward', 'import', 'transwiki', 'uploader', 'ipblock-exempt', 'oversight', 'founder', 'rollbacker', 'accountcreator', 'autoreviewer', 'abusefilter')

    for group in groups:
        g = addGroupAttribute(g, lang, group)

    print g.attributes()
    #print g.vs['bot']
    #print len(g.vs.select(bot=True))
    g.write("%swiki-%s_rich.pickle" % (lang, date), format="pickle")

    
if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
