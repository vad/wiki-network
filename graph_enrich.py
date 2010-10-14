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
import igraph as ig
from sonet.mediawiki import addGroupAttribute, addBlockedAttribute, isip, \
     explode_dump_filename

def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [-s SOURCE] [-h] file")
    p.add_option('-s', '--source', metavar='SOURCE', dest='source',
                 help='Specify a graph to use as source for attributes '+ \
                 '(this will disable API calls)')

    opts, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    fn = files[0]

    lang, date, type_ = explode_dump_filename(fn)

    groups = ('bot', 'sysop', 'bureaucrat', 'checkuser', 'steward', 'import',
              'transwiki', 'uploader', 'ipblock-exempt', 'oversight',
              'founder', 'rollbacker', 'accountcreator', 'autoreviewer',
              'abusefilter')
    g = ig.load(fn)
    if opts.source:
        sourceg = ig.load(opts.source)
        for destv in g.vs:
            try:
                sourcev = sourceg.vs.select(username=destv['username'])[0]
            except IndexError:
                print destv['username'], 'not found in source'
                for group in groups:
                    destv[group] = None
                continue
            for group in groups:
                destv[group] = sourcev[group]

    else:
        for group in groups:
            addGroupAttribute(g, lang, group)

        print 'BLOCKED ACCOUNTS'
        addBlockedAttribute(g, lang)

    print 'ANONYMOUS USERS'
    g.vs['anonymous'] = map(isip, g.vs['username'])
    g.write("%swiki-%s%s_rich.pickle" % (lang, date, type_), format="pickle")


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
