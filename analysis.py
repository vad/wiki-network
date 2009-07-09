#!/usr/bin/env python

import igraph as ig
from time import ctime
from optparse import OptionParser
import os, sys, re
import gc

## GLOBAL VARIABLES

## FUNCTIONS

def meanDegree(g, type):
    isinstance(g, ig.Graph) # helper for wing
    degree = g.degree(type=type)
    mean = 1.*sum(degree)/len(degree)
    return mean


def degreeVariance(g, type, mean):
    '''
    g:      graph
    type:   type (igraph.IN or igraph.OUT)
    mean:   mean degree for this type
    '''
    degree = g.degree(type=type)
    variance = 1.*sum([(nodeDegree - mean)**2 for nodeDegree in degree])/len(g.vs)
    return variance


def printAverageDistance(g):
    #print 'DISTANCES', ctime()
    dSum = 0
    step = 1000
    n = len(g.vs)
    for i in range(0, n, step):
        if not (i+1) % 100:
            print 'Step:', i
            print 1.*dSum*step/i
        uplimit = min(n, i+step)
        
        dSum += 1.*sum([sum(d) for d in g.shortest_paths(range(i, uplimit), weights='weight')]) / (n-1) / (uplimit - i)

    avg_dist = 1.*dSum / len(range(0, n, step))
    #print "Average distance: %f" % avg_dist


def set_weighted_indegree(g):
    #todo: improve self-loops check
    for node in g.vs:
        edges = g.adjacent(node.index, type=ig.IN)
        g_edges = (e for e in edges if not g.is_loop(e))
        node['indegree'] = sum(g.es[eid]['weight'] for eid in g_edges)


def usage(error = 0):
    print "SYNTAX: test.py filename"
    print ""

    sys.exit(error)


if __name__ == '__main__':
    op = OptionParser('%prog [options] graph')
    
    op.add_option('-d', '--details', action="store_true", dest="details",
        help="Print details about this graph (# of vertexes and # of edges)")
    op.add_option('-e', '--degree', action="store_true", dest="degree",
        help="Print the mean vertex-vertex distance of the graph")
    op.add_option('-r', '--density', action="store_true", dest="density",
        help="Print the density of the graph")
    op.add_option('-t', '--transitivity', action="store_true", dest="transitivity")
    op.add_option('-i', '--distance', action="store_true", dest="distance")
    op.add_option('-s', '--summary', action="store_true", dest="summary")
    op.add_option('-p', '--plot', action="store_true", dest="plot")
    op.add_option('-c', '--histogram', action="store_true", dest="histogram")
    op.add_option('-g', '--gnuplot', action="store_true", dest="gnuplot")
    
    (options, args) = op.parse_args()

    if len(args) != 1:
        print "Insert one (and only one) file to process\n"
        op.print_help()

    fn = args[0]
    s = os.path.split(fn)[1]
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})',s)
    date = ''.join([res.group(x) for x in xrange(1,4)])
    g = ig.load(fn)

    if options.details:
        print "Vertex: %d" % (len(g.vs),)
        print "Edge: %d" % (len(g.es),)

    if options.density:
        print "Density: %.10f" % (g.density(),)

        lenvs = len(g.vs)
        print "Calculated density: %.10f" % (1.*len(g.es)/lenvs/(lenvs-1))
        print ""

    if options.degree:
        mid = meanDegree(g, ig.IN)
        mod = meanDegree(g, ig.OUT)

        print "Mean IN degree: %f" % mid
        print "Mean OUT degree: %f" % mod

        print "Variance IN Degree: %f" % degreeVariance(g, ig.IN, mid)
        print "Variance OUT Degree: %f" % degreeVariance(g, ig.OUT, mod)

    if options.transitivity:
        #print " * transitivity: %f" % (nx.transitivity(g), )
        pass
    
    if options.summary:
        print "* summary: %s" % (g.summary(), )

    if options.distance:
        giant = g.clusters().giant()

        print "Length max cluster: %d" % (len(giant.vs), )

        printAverageDistance(giant)

        #print "Average distance 2: %f" % giant.average_path_length(True, False)

    if options.plot or options.histogram:
        set_weighted_indegree(g)


    if options.histogram:
        indegrees = sorted(g.vs['indegree'])
        
        # group
        nogrp_indegrees = g.vs.select(sysop_ne=True,bot_ne=True)['indegree']
        nogrp_list = [(degree, 1) for degree in nogrp_indegrees if degree]
        
        sysops_indegrees = g.vs.select(sysop=True)['indegree']
        sysops_list = [(degree, 2) for degree in sysops_indegrees if degree]
        
        bots_indegrees = g.vs.select(bot=True)['indegree']
        bots_list = [(degree, 3) for degree in bots_indegrees if degree]
        
        if options.gnuplot:
            f = open('hist.dat', 'w')
        else:
            f = open('%swiki-%s-hist.dat' % (lang, date), 'w')

        for indegree, grp in sorted(sysops_list + nogrp_list + bots_list, reverse=True):
            for i in range(grp - 1):
                print >>f, 0,
            print >>f, indegree,
            for i in range(grp, 3):
                print >>f, 0,
            print >>f, ""
        f.close()

    if options.gnuplot:
        from popen2 import Popen3
        
        process = Popen3('gnuplot hist.gnuplot')
        process.wait()
        
        os.rename('hist.png', '%swiki-%s-hist.png' % (lang, date))
        
            
    if options.plot:
        import math
        bots = g.vs.select(bot=True)
        bots['color'] = ('purple',)*len(bots)
        
        burs = g.vs.select(bureaucrat=True)
        burs['color'] = ('blue',)*len(burs)

        sysops = g.vs.select(sysop=True)
        sysops['color'] = ('yellow',)*len(sysops)

        bur_sysops = g.vs.select(bureaucrat=True, sysop=True)
        bur_sysops['color'] = ('orange',)*len(bur_sysops)

        g.vs['size'] = [math.sqrt(v['indegree']+1)*10 for v in g.vs]

        ig.plot(g, target=lang+"_general.png", bbox=(0,0,4000,2400), edge_color='grey', layout='fr')
        weights = g.es['weight']
        max_weight = max(weights)
        
        g.es['color'] = [(255.*e['weight']/max_weight, 0., 0.) for e in g.es]
        g.es['width'] = weights

        ig.plot(g, target=lang+"_weighted_edges.png", bbox=(0,0,4000,2400), layout='fr', vertex_label=' ')


