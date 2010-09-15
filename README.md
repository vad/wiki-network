## Install
To solve dependencies:
./setup.py develop

## Scripts
### utpedits2graph.py
Count edits on User Talk Pages and create a graph from it. Save the graph as a pickled iGraph object.

The graph is directed and weighted. For example, two edits made by User A on User B's Talk Page is represented as an edge from A to B with weight = 2.

This script should be used on complete dumps and on stub.

### signature2graph.py
Like utpedits2graph.py, but counting signature on User Talk Pages.

This script can be used on current dumps.

### enrich.py
Giving a pickled iGraph object, this script downloads useful information about the users (like if the user is a bot, a sysop, ..) from the wikipedia API and creates a new pickled iGraph object.