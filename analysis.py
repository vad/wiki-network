#!/usr/bin/env python

## SYSTEM
import os
import sys
import numpy
import igraph as ig
import logging

## PROJECT
from sonet.tablr import Tablr
from sonet.timr import Timr
from sonet import mediawiki as mwlib, graph as sg

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

## GLOBAL VARIABLES

groups = {
    'all': {},
    'bot': {'bot': True},
    'not_bot': {'bot_ne': True},
    'sysop': {'sysop': True, 'bureaucrat_ne': True, 'steward_ne': True,
              'founder_ne': True},
    'bureaucrat': {'bureaucrat': True, 'steward_ne': True, 'founder_ne': True},
    'steward': {'steward': True, 'founder_ne': True},
    'founder': {'founder': True},
    'su': {'sysop': True},
    'normal_user': {'sysop_ne': True, 'bureaucrat_ne': True,
                    'steward_ne': True, 'founder_ne': True, 'bot_ne': True,
                    'anonymous_ne': True},
    'blocked': {'blocked': True},
    'not_blocked': {'blocked_ne': True},
    'anonymous': {'anonymous': True},
    'not_anonymous': {'anonymous_ne': True},
}

## FUNCTIONS
def top(l, nelem=5, accuracy=10):
    #TODO: if l is a numpy array use numpy.array.sort() instead of sorted
    import types

    if not len(l):
        return 'nan'
    else:
        if type(l[0]) in (types.IntType, numpy.int64, numpy.int32):
            format = "%d"
        else:
            format = '%%.%df' % (accuracy,)
        return ', '.join(format % e for e in sorted(l, reverse=True)[:nelem])

def create_option_parser():
    from optparse import OptionParser, OptionGroup
    from sonet.lib import SonetOption

    op = OptionParser('%prog [options] graph', option_class=SonetOption)

    time_group = OptionGroup(op, 'Time related options')
    time_group.add_option('-S', '--start', action="store", dest='start',
                          type="yyyymmdd", default=None, metavar="YYYYMMDD",
                          help="Look for revisions starting from this date")
    time_group.add_option('-E', '--end', action="store", dest='end',
                          type="yyyymmdd", default=None, metavar="YYYYMMDD",
                          help="Look for revisions until this date"
                          )
    op.add_option_group(time_group)

    op.add_option('--as-table', action="store_true", dest="as_table",
        help="Format output as a table row")
    op.add_option('--group', action="store_true", dest="group",
        help="Analyze groups")
    op.add_option('-d', '--details', action="store_true", dest="details",
        help="Print details about this graph (# of vertexes and # of edges)")
    op.add_option('-e', '--degree', action="store_true", dest="degree",
        help="Print the mean vertex-vertex distance of the graph")
    op.add_option('-r', '--density', action="store_true", dest="density",
        help="Print the density of the groups (requires --groups)")
    op.add_option('--reciprocity', action="store_true", dest="reciprocity",
        help="Print the reciprocity of the groups  (requires --groups)")
    op.add_option('-t', '--transitivity', action="store_true",
                  dest="transitivity")
    op.add_option('-i', '--distance', action="store_true", dest="distance")
    op.add_option('-f', '--efficiency', action="store_true", dest="efficiency")
    op.add_option('-s', '--summary', action="store_true", dest="summary")
    op.add_option('-c', '--centrality', action="store", dest="centrality",
                  type="string", metavar="all|pagerank|betweenness|degree",
                  help="Compute the specified centrality measures")
    op.add_option('-p', '--plot', action="store_true", dest="plot")
    op.add_option('--histogram', action="store_true", dest="histogram")
    op.add_option('-g', '--gnuplot', action="store_true", dest="gnuplot")
    op.add_option('-w', '--power-law', action="store_true", dest="power_law")
    op.add_option('-a', '--adjacency', action="store_true", dest="adjacency",
        help="Write the adjacency matrix of the giant component to a file")
    op.add_option('--users-role', action="store_true", dest="users_role",
        help="Write a list users-role to a file")

    return op


def main():
    op = create_option_parser()

    (options, args) = op.parse_args()

    if len(args) != 1:
        print "Insert one (and only one) file to process\n"
        op.print_help()
        sys.exit(2)

    fn = args[0]
    lang, date, type_ = mwlib.explode_dump_filename(fn)

    g = sg.load(fn)
    g.time_slice_subgraph(start=options.start, end=options.end)
    g.invert_edge_attr('weight', 'length')

    vn = len(g.g.vs) # number of vertexes
    en = len(g.g.es) # number of edges

    timr = Timr()

    if options.as_table:
        tablr = Tablr()
        tablr.start(1024*32, lang)

    if options.group or options.users_role:
        for group_name, group_attr in groups.iteritems():
            g.defineClass(group_name, group_attr)
            print ' * %s : nodes number : %d' % (group_name,
                                                 len(g.classes[group_name]))
    else:
        g.defineClass('all', {})

    print " * lang: %s" % (lang,)
    print " * date: %s" % (date,)

    if options.details:
        with Timr("details"):
            print " * nodes number: %d" % (vn,)
            print " * edges number: %d" % (en,)

            nodes_with_outdegree = len(g.g.vs.select(_outdegree_ge=1))
            nodes_with_indegree = len(g.g.vs.select(_indegree_ge=1))

            print " * nodes with out edges number: %d (%6f%%)" % (
                nodes_with_outdegree, 100.*nodes_with_outdegree/vn)
            print " * nodes with in edges number: %d (%6f%%)" % (
                nodes_with_indegree, 100.*nodes_with_indegree/vn)
            print " * max weights on edges : %s" % top(g.g.es['weight'])

            #print " * diameter : %6f" % g.g.diameter(weights='length')

            #print " * average weight : %6f" % numpy.average(g.g.es['weight'])


    if options.density or options.reciprocity:
        with Timr('density&reciprocity'):
            for cls, vs in g.classes.iteritems():
                if not len(vs) > 1:
                    continue

                subgraph = vs.subgraph()

                print " * %s : density : %.10f" % (cls, subgraph.density())
                print " * %s : reciprocity : %.10f" % (cls,
                                                       subgraph.reciprocity())


    if options.degree:
        with Timr('degree'):
            g.g.vs['indegree'] = g.g.degree(type=ig.IN)
            g.g.vs['outdegree'] = g.g.degree(type=ig.OUT)

            for cls, vs in g.classes.iteritems():
                if not vs:
                    continue

                ind = numpy.array(vs['indegree'])
                outd = numpy.array(vs['outdegree'])

                print " * %s : mean IN degree (no weights): %f" % (
                    cls, numpy.average(ind))
                print " * %s : mean OUT degree (no weights): %f" % (
                    cls, numpy.average(outd))
                print " * %s : max IN degrees (no weights): %s" % (cls,
                                                                   top(ind))
                print " * %s : max OUT degrees (no weights): %s" % (cls,
                                                                    top(outd))

                print " * %s : stddev IN degree (no weights): %f" % (
                    cls, numpy.sqrt(numpy.var(ind)))
                print " * %s : stddev OUT degree (no weights): %f" % (
                    cls, numpy.sqrt(numpy.var(outd)))

    if options.transitivity:
        ##print " * transitivity: %f" % (nx.transitivity(g), )
        pass

    if options.summary:
        # don't use with --as-table
        print " * summary: %s" % (g.g.summary(), )

    if options.distance:
        with Timr('split clusters'):
            vc = g.g.clusters()
            size_clusters = vc.sizes()
            giant = vc.giant()

            print " * length of 5 max clusters: %s" % top(size_clusters)
            #print " * #node in 5 max clusters/#all nodes: %s" % top(
            #    [1.*cluster_len/vn for cluster_len in size_clusters])


    if options.distance:
        with Timr('distance'):
            gg = sg.Graph(giant)
            print " * average distance in the giant component: %f" % \
                  gg.averageDistance(weight='length')
            print " * average hops in the giant component: %f" % \
                  gg.averageDistance()

            #print "Average distance 2: %f" % giant.average_path_length(True,
            #                                                           False)


    if options.efficiency:
        with Timr('efficiency'):
            print " * efficiency: %f" % g.efficiency(weight='length')


    ##TODO: compute for centrality only if "all" or "degree"
    if (options.plot or options.histogram or options.power_law or
        options.centrality):
        with Timr('set weighted indegree'):
            g.set_weighted_degree()


    if options.centrality:
        timr.start('centrality')
        centralities = options.centrality.split(',')
        if 'all' in centralities:
            centralities = 'betweenness,pagerank,degree'.split(',')

        if set(centralities).difference(
            'betweenness,pagerank,degree'.split(',')):
            logging.error('Unknown centrality')
            sys.exit(0)

        if "betweenness" in centralities:
            print >> sys.stderr, "betweenness"
            g.g.vs['bw'] = g.g.betweenness(weights='length', directed = True)

        #g.g.vs['ev'] = g.g.evcent(weights='weight') # eigenvector centrality

        if 'pagerank' in centralities:
            print >> sys.stderr, "pagerank"
            g.g.vs['pr'] = g.g.pagerank(weights='weight') # pagerank

        if 'degree' in centralities:
            print >> sys.stderr, "outdegree"
            g.set_weighted_degree(type=ig.OUT)
        #total_weights = sum(g.g.es['weight'])
        max_edges = vn*(vn-1)

        for cls, vs in g.classes.iteritems():
            if not vs:
                continue

            if "betweenness" in centralities:
                norm_betweenness = numpy.array(g.classes[cls]['bw'])/max_edges
                print " * %s : average betweenness : %.10f" % (
                    cls, numpy.average(norm_betweenness))
                print " * %s : stddev betweenness : %.10f" % (
                    cls, numpy.sqrt(numpy.var(norm_betweenness)))
                print " * %s : max betweenness: %s" % (
                    cls, top(numpy.array(g.classes[cls]['bw'])/max_edges))

            #print " * Average eigenvector centrality : %6f" % numpy.average(
            #    g.vs['ev'])
            if 'pagerank' in centralities:
                print " * %s : average pagerank : %.10f" % (
                    cls, numpy.average(g.classes[cls]['pr']))
                print " * %s : stddev pagerank : %.10f" % (
                    cls, numpy.sqrt(numpy.var(g.classes[cls]['pr'])))
                print " * %s : max pagerank: %s" % (
                    cls, top(g.classes[cls]['pr']))

            if 'degree' in centralities:
                wi = g.classes[cls]['weighted_indegree']
                print " * %s : average IN degree centrality (weighted): %.10f" % (
                    cls, numpy.average(wi))
                print " * %s : stddev IN degree centrality (weighted): %.10f" % (
                    cls, numpy.sqrt(numpy.var(wi)))
                print " * %s : max IN degrees centrality (weighted): %s" % (
                    cls, top(wi))
                del wi

                wo = g.classes[cls]['weighted_outdegree']
                print " * %s : average OUT degree centrality (weighted) : %.10f" %\
                      (cls, numpy.average(wo))
                print " * %s : stddev OUT degree centrality (weighted) : %.10f" % \
                      (cls, numpy.sqrt(numpy.var(wo)))
                print " * %s : max OUT degrees centrality (weighted): %s" % (
                    cls, top(wo))
                del wo

        timr.stop('centrality')

    if options.power_law:
        with Timr('power law'):
            for cls, vs in g.classes.iteritems():
                if not vs:
                    continue

                indegrees = vs['weighted_indegree']

                try:
                    alpha_exp = ig.statistics.power_law_fit(indegrees, xmin=6)
                    print " * %s : alpha exp IN degree distribution : %10f " %\
                          (cls, alpha_exp)
                except ValueError:
                    print >> sys.stderr,\
                          " * %s : alpha exp IN degree distribution : ERROR" %\
                          (cls,)

    if options.histogram:
        list_with_index = lambda degrees, idx: [(degree, idx) for degree
                                                in degrees if degree]
        all_list = []

        nogrp_indegrees = g.g.vs.select(sysop_ne=True, bureaucrat_ne=True,
                                        steward_ne=True, founder_ne=True,
                                        bot_ne=True)['weighted_indegree']
        all_list += list_with_index(nogrp_indegrees, 1)

        sysops_indegrees = g.classes['sysop']['weighted_indegree']
        all_list += list_with_index(sysops_indegrees, 2)

        burs_indegrees = g.classes['bureaucrat']['weighted_indegree']
        all_list += list_with_index(burs_indegrees, 3)

        stewards_indegrees = g.classes['steward']['weighted_indegree']
        all_list += list_with_index(stewards_indegrees, 4)

        founders_indegrees = g.classes['founder']['weighted_indegree']
        all_list += list_with_index(founders_indegrees, 5)

        bots_indegrees = g.classes['bot']['weighted_indegree']
        all_list += list_with_index(bots_indegrees, 6)

        if options.gnuplot:
            f = open('hist.dat', 'w')
        else:
            f = open('%swiki-%s-hist.dat' % (lang, date), 'w')

        all_list.sort(reverse=True)

        for indegree, grp in all_list:
            for _ in range(grp - 1):
                print >> f, 0,
            print >> f, indegree,
            for _ in range(grp, 6):
                print >> f, 0,
            print >> f, ""
        f.close()

    if options.gnuplot:
        from popen2 import Popen3

        process = Popen3('gnuplot hist.gnuplot')
        process.wait()

        os.rename('hist.png', '%swiki-%s-hist.png' % (lang, date))
        os.rename('hist.dat', '%swiki-%s-hist.dat' % (lang, date))

    if options.plot:
        ## TODO: evaluate if this can be done with
        ## http://bazaar.launchpad.net/~igraph/igraph/0.6-main/revision/2018
        with Timr('plot'):
            import math

            ## filter:
            #print len(g.g.vs), len(g.g.es)
            #g.set_weighted_degree(type=ig.OUT)
            #g.g = g.g.subgraph(g.g.vs.select(weighted_indegree_ge=10,
            #                           weighted_outdegree_ge=1))
            #g.g.write_graphml('itwiki-20100729-stub-meta-history_in10_out1.graphml')
            #print len(g.g.vs), len(g.g.es)

            bots = g.g.vs.select(bot=True)
            bots['color'] = ('purple',)*len(bots)
            logging.debug('bots: ok')

            burs = g.g.vs.select(anonymous=True)
            burs['color'] = ('blue',)*len(burs)

            sysops = g.g.vs.select(sysop=True)
            sysops['color'] = ('yellow',)*len(sysops)

            bur_sysops = g.g.vs.select(bureaucrat=True, sysop=True)
            bur_sysops['color'] = ('orange',)*len(bur_sysops)

            g.g.vs['size'] = [math.sqrt(v['weighted_indegree']+1)*10 for v
                              in g.g.vs]

            logging.debug('plot: begin')
            ig.plot(g.g, target=lang+"_general.png", bbox=(0, 0, 8000, 8000),
                    edge_color='grey', layout='drl')
            logging.debug('plot: end')
            weights = g.g.es['weight']
            max_weight = max(weights)

            g.g.es['color'] = [(255.*e['weight']/max_weight, 0., 0.) for e
                               in g.g.es]
            g.g.es['width'] = weights

            ig.plot(g.g, target=lang+"_weighted_edges.png", bbox=(0, 0, 4000,
                                                                  2400),
                    layout='fr', vertex_label=' ')


    if options.as_table:
        tablr.stop()

        #tablr.printHeader()
        #tablr.printData()
        tablr.saveInDjangoModel()


    if options.adjacency:
        giant = g.g.clusters().giant()
        #destAdj = "%s/%swiki-%s-adj.csv" % (os.path.split(fn)[0], lang, date)
        destAdj = "%swiki-%s-adj.csv" % (lang, date)
        #destRec = "%s/%swiki-%s-rec.csv" % (os.path.split(fn)[0], lang, date)
        destRec = "%swiki-%s-rec.csv" % (lang, date)
        sg.Graph(giant).writeAdjacencyMatrix(destAdj, 'username')
        sg.Graph(giant).writeReciprocityMatrix('username', destRec)


    if options.users_role:
        l = g.get_user_class('username', ('anonymous', 'bot', 'bureaucrat',
                                        'sysop'))

        #destUR = "%s/%swiki-%s-ur.csv" % (os.path.split(fn)[0], lang, date)
        destUR = "%swiki-%s-ur.csv" % (lang, date)
        with open(destUR, 'w') as f:
            for username, role in sorted(l):
                print >> f, "%s,%s" % (username, role)

        from random import shuffle
        #destCls = "%s/%swiki-%s-%%s.csv" % (os.path.split(fn)[0], lang, date)
        destCls = "%swiki-%s-%%s.csv" % (lang, date)
        for cls in ('anonymous', 'bot', 'bureaucrat', 'sysop', 'normal_user'):
            users = g.classes[cls]['username']
            shuffle(users)
            with open(destCls % cls, 'w') as f:
                for username in users:
                    print >> f, \
                          ("%s,http://vec.wikipedia.org/w/index.php?title="+\
                          "Discussion_utente:%s&action=history&offset="+\
                          "20100000000001") % (username, username)


if __name__ == '__main__':
    main()
