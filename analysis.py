#!/usr/bin/env python

import igraph as ig
from time import ctime
from getopt import *
import os, sys
import gc

## GLOBAL VARIABLES

## FUNCTIONS

def meanDegree(g, type):
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
    try:                                
        opts, args = getopt(sys.argv[1:], "hdeirtsp", ["help", "details", "degree", "distance", 'density', 'transitivity', 'summary', 'plot']) 
    except GetoptError:
        usage(2)

    if len(args) != 1:
        usage(1)

    _details = _degree = _distance = _density = _transitivity = _summary = _plot = False
    for opt, arg in opts:
        if opt in ('-d', '--details'):
            _details = True
        if opt in ('-e', '--degree'):
            _degree = True
        if opt in ('-i', '--distance'):
            _distance = True
        if opt in ('-r', '--density'):
            _density = True
        if opt in ('-t', '--transitivity'):
            _transitivity = True
        if opt in ('-s', '--summary'):
            _summary = True
        if opt in ('-p', '--plot'):
            _plot = True

    fn = args[0]
    s = os.path.split(fn)[1]
    lang = s[:s.index('wiki')]
    g = ig.load(fn)

    if _details:
        print "Vertex: %d" % (len(g.vs),)
        print "Edge: %d" % (len(g.es),)

    if _density:
        print "Density: %.10f" % (g.density(),)

        lenvs = len(g.vs)
        print "Calculated density: %.10f" % (1.*len(g.es)/lenvs/(lenvs-1))
        print ""

    if _degree:
        mid = meanDegree(g, ig.IN)
        mod = meanDegree(g, ig.OUT)

        print "Mean IN degree: %f" % mid
        print "Mean OUT degree: %f" % mod

        print "Variance IN Degree: %f" % degreeVariance(g, ig.IN, mid)
        print "Variance OUT Degree: %f" % degreeVariance(g, ig.OUT, mod)

    #if _transitivity:
    #    print " * transitivity: %f" % (nx.transitivity(g), )
    
    if _summary:
        print "* summary: %s" % (g.summary(), )

    if _distance:
        giant = g.clusters().giant()

        print "Length max cluster: %d" % (len(giant.vs), )

        printAverageDistance(giant)

        #print "Average distance 2: %f" % giant.average_path_length(True, False)

    if _plot:
        import math
        bots = g.vs.select(bot=True)
        bots['color'] = ('purple',)*len(bots)
        
        burs = g.vs.select(bureaucrat=True)
        burs['color'] = ('blue',)*len(burs)

        sysops = g.vs.select(sysop=True)
        sysops['color'] = ('yellow',)*len(sysops)

        bur_sysops = g.vs.select(bureaucrat=True, sysop=True)
        bur_sysops['color'] = ('orange',)*len(bur_sysops)

        set_weighted_indegree(g)
        g.vs['size'] = [math.sqrt(v['indegree']+1)*10 for v in g.vs]

        ig.plot(g, target=lang+"_general.png", bbox=(0,0,4000,2400), edge_color='grey', layout='fr')
        weights = g.es['weight']
        max_weight = max(weights)
        
        g.es['color'] = [(255.*e['weight']/max_weight, 0., 0.) for e in g.es]
        g.es['width'] = weights

        ig.plot(g, target=lang+"_weighted_edges.png", bbox=(0,0,4000,2400), layout='fr', vertex_label=' ')

    print 'END', ctime()

