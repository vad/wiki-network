#!/usr/bin/env python

import igraph as ig
from time import ctime
from optparse import OptionParser
import os, sys, re
import gc
import numpy

## GLOBAL VARIABLES

## FUNCTIONS

def averageDistance(g):
    isinstance(g, ig.Graph) # helper for wing
    #print 'DISTANCES', ctime()
    dSum = 0
    step = 1000
    n = len(g.vs)
    for i in range(0, n, step):
        #if not (i+1) % 100:
        #    print 'Step:', i
        #    print 1.*dSum*step/i
        uplimit = min(n, i+step)
        
        dSum += 1.*sum([sum(d) for d in g.shortest_paths(range(i, uplimit), weights='weight')]) / (n-1) / (uplimit - i)

    avg_dist = 1.*dSum / len(range(0, n, step))
    return avg_dist


def set_weighted_indegree(g):
    #todo: improve self-loops check
    for node in g.vs:
        edges = g.adjacent(node.index, type=ig.IN)
        g_edges = (e for e in edges if not g.is_loop(e))
        node['indegree'] = sum(g.es[eid]['weight'] for eid in g_edges)



if __name__ == '__main__':
    op = OptionParser('%prog [options] graph')
    
    op.add_option('--as-table', action="store_true", dest="as_table",
        help="Format output as a table row")
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
    isinstance(g, ig.Graph) # helper for wing

    if options.as_table:
        import mmap
        out = mmap.mmap(-1, 1024*1024) #create an in-memory-file
        sys.stdout = out
    
    if options.details:
        print " * vertexes: %d" % (len(g.vs),)
        print " * edges: %d" % (len(g.es),)

        nodes_with_outdegree = len(g.vs.select(_outdegree_ge=1))
        
        print " * #nodes with out edges: %d (%6f%%)" % (nodes_with_outdegree, 1.*nodes_with_outdegree/len(g.vs))
        print " * 5 max weights on edges : %s" % (', '.join(str(idx) for idx in sorted(g.es['weight'], reverse=True)[:5]),)

    if options.density:
        print " * density: %.10f" % (g.density(),)

        #lenvs = len(g.vs)
        #print " * calculated density: %.10f" % (1.*len(g.es)/lenvs/(lenvs-1))
        #print ""

    if options.degree:
        ind = g.degree(type=ig.IN)
        outd = g.degree(type=ig.OUT)
        mid = numpy.average(ind)
        mod = numpy.average(outd)

        print " * mean IN/OUT degree: %f" % mid
        print " * max IN degree: %f" % max(ind)
        print " * max OUT degree: %f" % max(outd)

        print " * variance IN Degree: %f" % numpy.var(ind)
        print " * variance OUT Degree: %f" % numpy.var(outd)

    if options.transitivity:
        #print " * transitivity: %f" % (nx.transitivity(g), )
        pass
    
    if options.summary:
        print " * summary: %s" % (g.summary(), )

    if options.distance:
        giant = g.clusters().giant()
        
        giant_len = len(giant.vs)
        print " * length max cluster: %d" % (giant_len, )
        print " * #node in max cluster/#all nodes: %6f" % (1.*giant_len/len(g.vs), )
        
    if options.distance:
        print " * average distance: %f" % averageDistance(giant)

        #print "Average distance 2: %f" % giant.average_path_length(True, False)

    if options.plot or options.histogram:
        set_weighted_indegree(g)


    if options.histogram:
        indegrees = sorted(g.vs['indegree'])
        
        # group
        nogrp_indegrees = g.vs.select(sysop_ne=True, bureaucrat_ne=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        nogrp_list = [(degree, 1) for degree in nogrp_indegrees if degree]
        
        sysops_indegrees = g.vs.select(sysop=True, bureaucrat_ne=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        sysops_list = [(degree, 2) for degree in sysops_indegrees if degree]
        
        burs_indegrees = g.vs.select(bureaucrat=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        burs_list = [(degree, 3) for degree in burs_indegrees if degree]
        
        stewards_indegrees = g.vs.select(steward=True, founder_ne=True, bot_ne=True)['indegree']
        stewards_list = [(degree, 4) for degree in stewards_indegrees if degree]
        
        founders_indegrees = g.vs.select(founder=True, bot_ne=True)['indegree']
        founders_list = [(degree, 5) for degree in founders_indegrees if degree]
        
        bots_indegrees = g.vs.select(bot=True)['indegree']
        bots_list = [(degree, 6) for degree in bots_indegrees if degree]
        
        if options.gnuplot:
            f = open('hist.dat', 'w')
        else:
            f = open('%swiki-%s-hist.dat' % (lang, date), 'w')

        all_list = sorted(sysops_list + nogrp_list + burs_list + stewards_list + founders_list + bots_list, reverse=True)
        ##from pylab import figure, show, ioff, ion
        ##import matplotlib
        ##import matplotlib.pyplot as plt

        ##fig = figure(facecolor='white', edgecolor='white')
        ##ax = fig.add_subplot(111) # a plot with a row and a column
        
        ##isinstance(fig, matplotlib.figure.Figure)
        ##isinstance(ax, matplotlib.axes.Axes)
        
        ##ax.set_yscale('log')
        ##ax.set_xscale('log')
        
        ##degrees = [x[0] for x in all_list]
        ##d_colors = { 1: '#BE1E2D', 2: '#EE8310', 3: 'green', 4: '#92D5EA', 5: 'violet', 6: '#666699'}
        ##colors = [d_colors[x[1]] for x in all_list]
        
        ##ioff()
        ##ax.bar(range(len(degrees)), degrees, color=colors, edgecolor='white', width=1., log=True)    
        ##ax.set_ylim(0.9, max(indegrees))
        ##ion()

        ##show()
        
        
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


    if options.as_table:
        sys.stdout = sys.__stdout__  # restore stdout back to normal
        
        end_pos = out.tell()
        out.seek(0)
        table = []
        while out.tell() < end_pos:
            l = out.readline()
            if not l:
                break
            table.append(l.split(':')[1].strip())
        
        out.close()
        
        print "||%s||%s||" % (lang, '||'.join(table))
