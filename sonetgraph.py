import igraph as ig
import numpy

def load(fn):
    return Graph(ig.load(fn))



class Graph(object):
    #g = attr(ig.Graph)

    def __init__(self, g):
        self.g = g
        self.classes = {}

    def invert_edge_attr(self, source, dest):
        self.g.es[dest] = 1./numpy.array(self.g.es[source])


    def efficiency(self, weight=None):
        r"""Returns the efficiency of the graph

        @param weight: (string) specify which attribute to use. Do not specify if the graph is not weighted
        """
        isinstance(self.g, ig.Graph) # helper for wing
        effSum = 0.
        step = 100
        n = len(self.g.vs)
        for i in range(0, n, step):
            #if not i % 100:
            #    print 'Step:', i
            #    print 1.*dSum*step/i
            uplimit = min(n, i+step)

            # distances from nodes in range (i, i+step) to all the other nodes
            if weight:
                aDistances = self.g.shortest_paths(range(i, uplimit), weights=weight)
            else:
                aDistances = self.g.shortest_paths(range(i, uplimit))

            aDistances = numpy.array(aDistances)

            effSum += (1./aDistances[aDistances.nonzero()]).sum()

        efficiency = effSum/(1.*n*(n-1)) # maybe there should be a factor of 2 somewhere (directed graph)
        return efficiency


    def set_weighted_degree(self, type=ig.IN):
        #todo: improve self-loops check
        stype = type == ig.IN and "in" or "out"
        k = 'weighted_%sdegree' % stype

        for node in self.g.vs:
            edges = self.g.adjacent(node.index, type=type)
            g_edges = (e for e in edges if not self.g.is_loop(e))
            node[k] = sum(self.g.es[eid]['weight'] for eid in g_edges)



    def averageDistance(self, weight=None):
        r"""Returns the average shortest path length of the graph

        @param weight: (string) specify which attribute to use. Do not specify if the graph is not weighted
        """
        isinstance(self.g, ig.Graph) # helper for wing
        dSum = 0.
        step = 1000
        n = len(self.g.vs)
        for i in range(0, n, step):
            ##if not (i+1) % 100:
            ##    print 'Step:', i
            ##    print 1.*dSum*step/i
            uplimit = min(n, i+step)

            # distances from nodes in range (i, i+step) to all the other nodes
            if weight:
                aDistances = self.g.shortest_paths(range(i, uplimit), weights=weight)
            else:
                aDistances = self.g.shortest_paths(range(i, uplimit))

            aDistances = numpy.array(aDistances)

            dSum += 1.*aDistances.sum() / (n-1) / (uplimit - i)

        avg_dist = 1.*dSum / len(range(0, n, step))
        return avg_dist


    def defineClass(self, cls, attr):
        # maybe it's better to store attr only (and not the whole VertexSet)
        self.classes[cls] = self.g.vs.select(**attr)
        
        
    def writeAdjacency(self, fn, label, weight='weight'):
        """
        fn: name of the file to write
        label: a node attribute to use as node label
        """
        isinstance(self.g, ig.Graph)
        isinstance(self.g.es, ig.EdgeSeq)
        
        matrix = self.g.get_adjacency(ig.GET_ADJACENCY_BOTH, weight, 0)
        vs = self.g.vs
        with open(fn, 'w') as f:
            accumulate = ["",]
            for node in self.g.vs:
                accumulate.append(node['username'])
            print >>f, ','.join(accumulate)

            for i in range(len(vs)):
                accumulate = []
                accumulate.append(vs[i]['username'])

                accumulate += [str(e) for e in matrix[i]]
                print >>f, ','.join(accumulate)

                
    def getTopIndegree(self, limit):
        for v in self.g.vs:
            if v['weighted_indegree'] > 15:
                print v.index, v['weighted_indegree'], v['username']
                
