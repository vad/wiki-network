import igraph as ig

class EdgeCache:
    """
    Acts as a cache to speed up graph creation

    >>> ec = EdgeCache()
    >>> ec.add('me', {'him': 1, 'her': 3})
    >>> ec.add('you', {'him': 3})
    >>> ec.flush()
    >>> ec.nodes
    {'me': 0, 'you': 3, 'him': 1, 'her': 2}
    >>> sorted(ec.edges)
    [(1, 0, 1), (1, 3, 3), (2, 0, 3)]

    """
    edges = None      # a list of tuples: [(sender_id, recipient_id, 20), ...]
    temp_edges = None # a dict of dicts : {'recipient': {'sender1': 20,
                      #                    'sender2': 2}}
    nodes = None      # a dict of {'username': vertex_id}

    def __init__(self):
        self.edges = []
        self.temp_edges = {}
        self.nodes = {}

    def add(self, user, talks):
        """
        user: string
        talks: dict
        """
        try:
            d = self.temp_edges[user]
        except KeyError:
            self.temp_edges[user] = talks
            return

        for speaker, msgs in talks.iteritems():
            # if msgs is an int, sum it to the number of message already counted
            # if it's a list (i.e. a list of mwlib.Message) extend it
            if isinstance(msgs, int):
                d[speaker] = d.get(speaker, 0) + msgs
            else:
                try:
                    d[speaker].extend(msgs)
                except KeyError:
                    d[speaker] = msgs

    def flush(self):
        """
        This function assumes that all edges directed to the same node are
        already in self.temp_edges. You can't add other edges to these nodes
        after calling flush().

        For example you can call cumulate_edge twice with the same user, but in
        the meanwhile you can't call flush()
        """

        for recipient, talk in self.temp_edges.iteritems():
            # find node with username recipient in self nodes
            # If not present add it; we give him the id rec_id
            rec_id = self.nodes.setdefault(recipient, len(self.nodes))

            for sender, msgs in talk.iteritems():
                send_id = self.nodes.setdefault(sender, len(self.nodes))
                self.edges.append((send_id, rec_id, msgs))

        self.temp_edges.clear()

    def get_network(self, vertex_label='username', edge_label='weight'):
        """
        Get the resulting network and clean cached data
        """
        ##TODO: replace with igraph.Graph.DictList()
        ## see https://mulcyber.toulouse.inra.fr/scm/viewvc.php/pyrocleaner/\
        ##       duplicat_analyze.py?root=pyrocleaner&view=markup
        from operator import itemgetter

        g = ig.Graph(n = len(self.nodes), directed=True)
        g.es[edge_label] = []

        g.vs[vertex_label] = [n.encode('utf-8') for n, _ in sorted(
            self.nodes.items(), key=itemgetter(1))]
        self.nodes = []

        clean_edges = map(itemgetter(0, 1), self.edges)
        g.add_edges(clean_edges)
        del clean_edges

        for e_from, e_to, attr in self.edges:
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid][edge_label] = attr
        self.edges = []

        return g
