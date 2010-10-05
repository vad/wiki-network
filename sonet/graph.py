import igraph as ig
import numpy

def load(fn):
    """
    Load a graph from file with name fn.

    Returns a sonet.graph.Graph
    """
    return Graph(ig.load(fn))


class Graph(object):
    g = None

    def __init__(self, g):
        self.g = g
        self.classes = {}

    def invert_edge_attr(self, source, dest):
        self.g.es[dest] = 1./numpy.array(self.g.es[source])

    def efficiency(self, weight=None):
        r"""Returns the efficiency of the graph

        @param weight: (string) specify which attribute to use.
                       Do not specify if the graph is not weighted
        """
        isinstance(self.g, ig.Graph) # helper for wing
        effSum = 0.
        step = 100
        n = len(self.g.vs)
        for i in xrange(0, n, step):
            #if not i % 100:
            #    print 'Step:', i
            #    print 1.*dSum*step/i
            uplimit = min(n, i+step)

            # distances from nodes in range (i, i+step) to all the other nodes
            if weight:
                aDistances = self.g.shortest_paths(range(i, uplimit),
                                                   weights=weight)
            else:
                aDistances = self.g.shortest_paths(range(i, uplimit))

            aDistances = numpy.array(aDistances)

            effSum += (1./aDistances[aDistances.nonzero()]).sum()

        #TODO: maybe there should be a factor of 2 somewhere (directed graph)
        efficiency = effSum/(1.*n*(n-1))
        return efficiency

    def set_weighted_degree(self, type=ig.IN, remove_loops=True):
        #TODO: improve self-loops check
        stype = type == ig.IN and "in" or "out"
        k = 'weighted_%sdegree' % stype

        for node in self.g.vs:
            if remove_loops:
                edges = (e for e in self.g.adjacent(node.index, type=type)
                         if not self.g.is_loop(e))
            else:
                edges = self.g.adjacent(node.index, type=type)

            node[k] = sum(self.g.es[eid]['weight'] for eid in edges)

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
                aDistances = self.g.shortest_paths(range(i, uplimit),
                                                   weights=weight)
            else:
                aDistances = self.g.shortest_paths(range(i, uplimit))

            aDistances = numpy.array(aDistances)

            dSum += 1.*aDistances.sum() / (n-1) / (uplimit - i)

        avg_dist = 1.*dSum / len(range(0, n, step))
        return avg_dist

    def defineClass(self, cls, attr):
        # maybe it's better to store attr only (and not the whole VertexSet)
        self.classes[cls] = self.g.vs.select(**attr)

    def writeAdjacencyMatrix(self, fn, label, weight='weight'):
        """
        writes the matrix like:

        ,Bar,Foo,TOTAL
        Bar,0,2,2
        Foo,1,2,3
        TOTAL,1,4,5

        fn: name of the file to write
        label: a node attribute to use as node label

        """
        isinstance(self.g, ig.Graph)
        isinstance(self.g.es, ig.EdgeSeq)

        matrix = self.g.get_adjacency(ig.GET_ADJACENCY_BOTH, weight, 0)
        vs = self.g.vs
        with open(fn, 'w') as f:
            usernames = vs[label]

            accumulate = ["",]
            print >>f, ','.join(['',]+ usernames +['TOTAL',])

            for i in range(len(vs)):
                accumulate = [usernames[i],]

                msgs = matrix[i]
                accumulate += [str(e) for e in msgs]
                accumulate.append(str(sum(msgs)))
                print >>f, ','.join(accumulate)

            # write TOTAL line
            accumulate = ['TOTAL',]

            msgs = [sum([matrix[(j, i)] for j in range(len(vs))]) for i in
                    range(len(vs))]
            accumulate += [str(e) for e in msgs]
            accumulate.append(str(sum(msgs)))
            print >>f, ','.join(accumulate)


    def writeReciprocityMatrix(self, label, fn=None):
        """
        writes the matrix like:

        ,Bar,Foo,TOTAL
        Bar,1,1,2
        Foo,1,0,1
        TOTAL,2,1,3

        It's obviousbly a simmetric matrix. On the main diagonal are there self-edges.

        >>> g = ig.Graph(n=3, directed=True)
        >>> g.vs['name'] = ['me', 'you', 'she']
        >>> g = Graph(g.add_edges(((1,0),(0,1),(0,2))))
        >>> g.writeReciprocityMatrix('name')
        ,me,you,she,TOTAL
        me,0,1,0,1
        you,1,0,0,1
        she,0,0,0,0
        TOTAL,1,1,0,2


        fn: name of the file to write
        label: a node attribute to use as node label

        """
        isinstance(self.g, ig.Graph)
        isinstance(self.g.es, ig.EdgeSeq)
        isinstance(self.g.vs, ig.VertexSeq)

        matrix = self.g.get_adjacency(ig.GET_ADJACENCY_BOTH, default=0)
        vs = self.g.vs
        N = len(vs)

        # len(vs) x len(vs) matrix
        rmatrix_data = [N*[0] for i in xrange(N)]
        for i in xrange(N):
            for j in xrange(i+1):
                if matrix[(i,j)] and matrix[(j,i)]:
                    rmatrix_data[i][j] = rmatrix_data[j][i] = 1

        if fn is None:
            import sys
            f = sys.stdout
        else:
            f = open(fn, 'w')

        labels = vs[label]

        print >>f, ','.join(['',]+ labels +['TOTAL',])

        rmatrix = ig.datatypes.Matrix(rmatrix_data)
        for i, label in enumerate(labels):
            accumulate = [label,]

            msgs = rmatrix[i]
            accumulate += [str(e) for e in msgs]
            accumulate.append(str(sum(msgs)))
            print >>f, ','.join(accumulate)

        # write TOTAL line
        accumulate = ['TOTAL',]

        msgs = [sum(rmatrix[(j, i)] for j in range(len(vs))) for i in
                range(len(vs))]
        accumulate += [str(e) for e in msgs]
        accumulate.append(str(sum(msgs)))
        print >>f, ','.join(accumulate)

    def getTopIndegree(self, lb=15, label='username'):
        self.getTopDegree(type=ig.IN, lb=lb, label=label)

    def getTopDegree(self, type=ig.IN, limit=None, lb=1, label='username'):
        from operator import itemgetter
        stype = 'weighted_%sdegree' % ('in' if type == ig.IN else 'out',)
        kwargs = {stype+'_gt': lb}

        nodes = self.g.vs(**kwargs)
        for v in sorted(nodes, cmp=itemgetter(stype), reverse=True)[0:limit]:
            print v.index, v[stype], v[label]
            #TODO: add role

    def get_user_class(self, label, classes=None):
        if not classes:
            classes = self.classes.keys()

        vs = self.g.vs
        for n in vs:
            found = False
            attrs = n.attributes()
            for cls in classes:
                if attrs[cls]:
                    found = True
                    yield (n[label], cls)
                    break
            if not found:
                yield (n[label], 'normal user')

    def remove_if(self, attrs):
        kwargs = dict([(attr+'_ne', True) for attr in attrs])
        self.g = self.g.subgraph(self.g.vs.select(**kwargs))

    def time_slice_subgraph(self, start=None, end=None,
                            time_label='timestamp', weight_label='weight',
                            remove_empty_edges=True,
                            remove_isolated_nodes=True):
        g = self.g
        isinstance(g, ig.Graph)
        if start is None and end is None:
            return
        for e in g.es:
            e[time_label] = [message for message in e[time_label]
                              if (start is None or start < message.time)
                              and (end is None or end > message.time)]
            e[weight_label] = len(e[time_label])
        if remove_empty_edges:
            kwargs = {weight_label: 0}
            g.delete_edges(**kwargs)
        if remove_isolated_nodes:
            g.delete_vertices(g.vs.select(_indegree=0, _outdegree=0))
