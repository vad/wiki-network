#!/usr/bin/env python

# system

from time import ctime
from optparse import OptionParser
import os, sys, re
import gc
import numpy
import sonetgraph as sg
import igraph as ig

# project
from tablr import Tablr

## GLOBAL VARIABLES

groups = {
    'all': {},
    'bot': {'bot': True},
    'not_bot': {'bot_ne': True},
    'sysop': {'sysop': True, 'bureaucrat_ne': True, 'steward_ne': True, 'founder_ne': True},
    'bureaucrat': {'bureaucrat': True, 'steward_ne': True, 'founder_ne': True},
    'steward': {'steward': True, 'founder_ne': True},
    'founder': {'founder': True},
    'su': {'sysop': True},
    'normal_user': {'sysop_ne': True, 'bureaucrat_ne': True, 'steward_ne': True, 'founder_ne': True, 'bot_ne': True, 'anonymous_ne': True},
    'blocked': {'blocked': True},
    'not_blocked': {'blocked_ne': True},
    'anonymous': {'anonymous': True},
    'not_anonymous': {'anonymous_ne': True},
}

## FUNCTIONS
def top(l, nelem=5):
    #TODO: if l is a numpy array use numpy.array.sort() instead of sorted
    import types

    if not len(l):
        return 'nan'
    elif type(l[0]) in (types.IntType, numpy.int64, numpy.int32):
        return ', '.join('%d' % e for e in sorted(l, reverse=True)[:nelem])
    else:
        return ', '.join('%6f' % e for e in sorted(l, reverse=True)[:nelem])


if __name__ == '__main__':
    op = OptionParser('%prog [options] graph')

    op.add_option('--as-table', action="store_true", dest="as_table",
        help="Format output as a table row")
    op.add_option('--group', action="store_true", dest="group",
        help="Analyze groups")
    op.add_option('-d', '--details', action="store_true", dest="details",
        help="Print details about this graph (# of vertexes and # of edges)")
    op.add_option('-e', '--degree', action="store_true", dest="degree",
        help="Print the mean vertex-vertex distance of the graph")
    op.add_option('-r', '--density', action="store_true", dest="density",
        help="Print the density of the graph")
    op.add_option('-t', '--transitivity', action="store_true", dest="transitivity")
    op.add_option('-i', '--distance', action="store_true", dest="distance")
    op.add_option('-f', '--efficiency', action="store_true", dest="efficiency")
    op.add_option('-s', '--summary', action="store_true", dest="summary")
    op.add_option('-c', '--centrality', action="store_true", dest="centrality")
    op.add_option('-p', '--plot', action="store_true", dest="plot")
    op.add_option('--histogram', action="store_true", dest="histogram")
    op.add_option('-g', '--gnuplot', action="store_true", dest="gnuplot")
    op.add_option('--power-law', action="store_true", dest="power_law")

    (options, args) = op.parse_args()

    if len(args) != 1:
        print "Insert one (and only one) file to process\n"
        op.print_help()
        sys.exit(2)

    fn = args[0]
    s = os.path.split(fn)[1]
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})',s)
    date = ''.join([res.group(x) for x in xrange(1,4)])

    g = sg.load(fn)
    ##print 'loaded'
    g.invert_edge_attr('weight', 'length')
    ##print 'inverted'

    vn = len(g.g.vs) # number of vertexes
    en = len(g.g.es) # number of edges

    if options.as_table:
        tablr = Tablr()
        tablr.start(1024*32, lang)

    if options.group:
        for group_name, group_attr in groups.iteritems():
            g.defineClass(group_name, group_attr)
            print ' * %s : # : %d' % (group_name, len(g.classes[group_name]))
    else:
        g.defineClass('all', {})

    if options.details:
        print " * vertexes: %d" % (vn,)
        print " * edges: %d" % (en,)

        nodes_with_outdegree = len(g.g.vs.select(_outdegree_ge=1))
        nodes_with_indegree = len(g.g.vs.select(_indegree_ge=1))

        print " * #nodes with out edges: %d (%6f%%)" % (nodes_with_outdegree, 100.*nodes_with_outdegree/vn)
        print " * #nodes with in edges: %d (%6f%%)" % (nodes_with_indegree, 100.*nodes_with_indegree/vn)
        print " * 5 max numMsg on edges : %s" % top(g.g.es['weight'])
        print " * reciprocity : %6f" % g.g.reciprocity()
        #print " * diameter : %6f" % g.g.diameter(weights='length')

        print " * Average weights : %6f" % numpy.average(g.g.es['weight'])


    if options.density:
        print " * density: %.10f" % (g.g.density(),)

        #print " * calculated density: %.10f" % (1.*len(g.es)/lenvs/(lenvs-1))

    if options.degree:
        g.g.vs['indegree'] = g.g.degree(type=ig.IN)
        g.g.vs['outdegree'] = g.g.degree(type=ig.OUT)

        for cls, vs in g.classes.iteritems():

            ind = numpy.array(vs['indegree'])
            outd = numpy.array(vs['outdegree'])

            print " * %s : mean IN degree (no weights): %f" % (cls, numpy.average(ind))
            print " * %s : mean OUT degree (no weights): %f" % (cls, numpy.average(outd))
            print " * %s : 5 max IN degree (no weights): %s" % (cls, top(ind))
            print " * %s : 5 max OUT degree (no weights): %s" % (cls, top(outd))

            print " * %s : variance IN Degree (no weights): %f" % (cls, numpy.var(ind))
            print " * %s : variance OUT Degree (no weights): %f" % (cls, numpy.var(outd))

    if options.transitivity:
        ##print " * transitivity: %f" % (nx.transitivity(g), )
        pass

    if options.summary:
        # don't use with --as-table
        print " * summary: %s" % (g.g.summary(), )

    if options.distance:
        vc = g.g.clusters()
        size_clusters = vc.sizes()
        giant = vc.giant()

        print " * length 5 max clusters: %s" % top(size_clusters)
        print " * #node in 5 max clusters/#all nodes: %s" % top([1.*cluster_len/vn for cluster_len in size_clusters])

    if options.distance:
        gg = sg.Graph(giant)
        print " * average distance in the giant component: %f" % gg.averageDistance(weight='length')
        print " * average hops in the giant component: %f" % gg.averageDistance()

        #print "Average distance 2: %f" % giant.average_path_length(True, False)

    if options.efficiency:
        print " * efficiency: %f" % g.efficiency(weight='length')

    if options.plot or options.histogram or options.power_law or options.centrality:
        g.set_weighted_degree()

    if options.centrality:
        g.g.vs['bw'] = g.g.betweenness(weights='length', directed = True)
        #g.g.vs['ev'] = g.g.evcent(weights='weight') # eigenvector centrality
        g.g.vs['pr'] = g.g.pagerank(weights='weight') # pagerank
        g.set_weighted_degree(type=ig.OUT)
        #total_weights = sum(g.g.es['weight'])
        max_edges = vn*(vn-1)

        for cls, vs in g.classes.iteritems():
            print " * %s : Average betweenness : %6f" % (cls, numpy.average(g.classes[cls]['bw'])/max_edges)
            print " * %s : 5 max betweenness centrality: %s" % (cls, top(g.classes[cls]['bw']))
            #print " * Average eigenvector centrality : %6f" % numpy.average(g.vs['ev'])
            print " * %s : Average pagerank : %6f" % (cls, numpy.average(g.classes[cls]['pr']))
            print " * %s : 5 max pageranks: %s" % (cls, top(g.classes[cls]['pr'], 5))
            print " * %s : Average IN degree centrality (weighted): %6f" % (cls, numpy.average(g.classes[cls]['weighted_indegree']))
            print " * %s : 5 max IN degrees central: %s" % (cls, top(g.classes[cls]['weighted_indegree']))
            print " * %s : Average OUT degree centrality (weighted) : %6f" % (cls, numpy.average(g.classes[cls]['weighted_outdegree']))
            print " * %s : 5 max OUT degrees central: %s" % (cls, top(g.classes[cls]['weighted_outdegree']))

    if options.power_law:
        #TODO: gruppi
        indegrees = g.g.vs['weighted_indegree']

        alpha_exp = ig.statistics.power_law_fit(indegrees, xmin=6)

        print " * alpha exp of the power law : %6f " % alpha_exp

    if options.histogram:
        list_with_index = lambda degrees, idx: [(degree, idx) for degree in degrees if degree]
        all_list = []

        nogrp_indegrees = g.g.vs.select(sysop_ne=True, bureaucrat_ne=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        all_list += list_with_index(nogrp_indegrees, 1)

        sysops_indegrees = g.classes['sysop']['indegree']
        all_list += list_with_index(sysops_indegrees, 2)

        burs_indegrees = g.classes['bureaucrat']['indegree']
        all_list += list_with_index(burs_indegrees, 3)

        stewards_indegrees = g.classes['steward']['indegree']
        all_list += list_with_index(stewards_indegrees, 4)

        founders_indegrees = g.classes['founder']['indegree']
        all_list += list_with_index(founders_indegrees, 5)

        bots_indegrees = g.classes['bot']['indegree']
        all_list += list_with_index(bots_indegrees, 6)

        if options.gnuplot:
            f = open('hist.dat', 'w')
        else:
            f = open('%swiki-%s-hist.dat' % (lang, date), 'w')

        all_list.sort(reverse=True)

        for indegree, grp in sorted(sysops_list + nogrp_list + burs_list + stewards_list + founders_list + bots_list, reverse=True):
            for i in range(grp - 1):
                print >>f, 0,
            print >>f, indegree,
            for i in range(grp, 6):
                print >>f, 0,
            print >>f, ""
        f.close()

    if options.gnuplot:
        from popen2 import Popen3

        process = Popen3('gnuplot hist.gnuplot')
        process.wait()

        os.rename('hist.png', '%swiki-%s-hist.png' % (lang, date))
        os.rename('hist.dat', '%swiki-%s-hist.dat' % (lang, date))


    if options.plot:
        import math
        bots = g.g.vs.select(bot=True)
        bots['color'] = ('purple',)*len(bots)

        burs = g.g.vs.select(bureaucrat=True)
        burs['color'] = ('blue',)*len(burs)

        sysops = g.g.vs.select(sysop=True)
        sysops['color'] = ('yellow',)*len(sysops)

        bur_sysops = g.g.vs.select(bureaucrat=True, sysop=True)
        bur_sysops['color'] = ('orange',)*len(bur_sysops)

        g.g.vs['size'] = [math.sqrt(v['indegree']+1)*10 for v in g.g.vs]

        ig.plot(g.g, target=lang+"_general.png", bbox=(0,0,4000,2400), edge_color='grey', layout='fr')
        weights = g.g.es['weight']
        max_weight = max(weights)

        g.g.es['color'] = [(255.*e['weight']/max_weight, 0., 0.) for e in g.g.es]
        g.g.es['width'] = weights

        ig.plot(g.g, target=lang+"_weighted_edges.png", bbox=(0,0,4000,2400), layout='fr', vertex_label=' ')


    if options.as_table:
        tablr.stop()

        tablr.printHeader()
        tablr.printData()

