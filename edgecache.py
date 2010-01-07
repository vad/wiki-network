import igraph as ig

class EdgeCache:
    """

    >>> ec = EdgeCache()
    >>> ec.cumulate_edge('me', {'him': 1, 'her': 3})
    >>> ec.cumulate_edge('you', {'him': 3})
    >>> ec.flush_cumulate()
    >>> ec.nodes
    {'me': 0, 'you': 3, 'him': 1, 'her': 2}
    >>> sorted(ec.edges)
    [(1, 0, 1), (1, 3, 3), (2, 0, 3)]

    """
    edges = []      # a list of tuples: [(sender_id, recipient_id, 20), ...]
    temp_edges = {} # a dict of dicts : {'recipient': {'sender1': 20, 'sender2': 2}}
    nodes = {}      # a dict of {'username': vertex_id}

    def cumulate_edge(self, user, talks):
        if not self.temp_edges.has_key(user):
            self.temp_edges[user] = talks
            return

        d = self.temp_edges[user]
        for speaker, msgs in talks.iteritems():
            d[speaker] = d.get(speaker, 0) + msgs


    def flush_cumulate(self):
        """
        This function assumes that all edges directed to the same node are present.

        For example you can call cumulate_edge twice with the same user, but in
        the meanwhile you can't call flush_cumulate()
        """

        for recipient, talk in self.temp_edges.iteritems():
            # find node with username recipient in self nodes
            # If not present add it; we give him the id rec_id
            rec_id = self.nodes.setdefault(recipient, len(self.nodes))

            for sender, msgs in talk.iteritems():
                send_id = self.nodes.setdefault(sender, len(self.nodes))
                self.edges.append((send_id, rec_id, msgs))

        self.temp_edges.clear()


    def get_network(self):
        """
        Get the resulting network and clean cached data
        """

        g = ig.Graph(n = 0, directed=True)
        g.es['weight'] = []
        g.vs['username'] = []

        g.add_vertices(len(self.nodes))

        for username, id in self.nodes.iteritems():
            g.vs[id]['username'] = username.encode('utf-8')
        self.nodes.clear()

        clean_edges = ((e[0], e[1]) for e in self.edges)
        g.add_edges(clean_edges)
        del clean_edges

        for e_from, e_to, weight in self.edges:
            eid = g.get_eid(e_from, e_to, directed=True)
            g.es[eid]['weight'] = weight
        self.edges = []

        return g