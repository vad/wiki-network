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

### usercontributions.py
Given a stub dump, this script counts contributions for every user on the whole wikipedia.

Results are stored in a database. Saved informations are:
<table>
<tr>
  <th>Field</th><th>Type</th><th>Description</th>
</tr>
<tr>
  <td>username</td><td>String</td><td></td>
</tr>
<tr>
  <td>lang</td><td>String</td><td>Data on this user are related to the "lang" wikipedia</td>
</tr>
<tr>
  <td>normal_edits</td><td>Integer</td><td>Edits on the article namespace</td>
</tr>
<tr>
  <td>namespace_edits</td><td>String</td><td>This is an array of integers. Each integer represents the number of edits made by this user on pages in a namespace. Namespaces are numbered starting from 0 in the order found at the beginning of the XML dump file</td>
</tr>
<tr>
  <td>first_edit</td><td>DateTime</td><td>Time of the first (oldest) edit</td>
</tr>
<tr>
  <td>last_edit</td><td>DateTime</td><td>Time of the last (most recent) edit</td>
</tr>
<tr>
  <td>comments_count</td><td>Integer</td><td>Number of comments left by this user</td>
</tr>
<tr>
  <td>comments_avg</td><td>Float</td><td>Comment average length</td>
</tr>
<tr>
  <td>minor</td><td>Integer</td><td>Number of minor edits</td>
</tr>
<tr>
  <td>welcome</td><td>Integer</td><td>Number of edits with a comment containing the word "welcome"</td>
</tr>
<tr>
  <td>npov</td><td>Integer</td><td>Number of edits with a comment containing the word "npov" (neutral point of view)</td>
</tr>
<tr>
  <td>please</td><td>Integer</td><td>Number of edits with a comment containing the word "please"</td>
</tr>
<tr>
  <td>thanks</td><td>Integer</td><td>Number of edits with a comment containing the word "thanks"</td>
</tr>
<tr>
  <td>revert</td><td>Integer</td><td>Number of edits with a comment containing the word "revert"</td>
</tr>
</table>

### usercontributions_export.py
Export data collected by usercontributions.py in a CSV file.

### events_anniversary.py
This script collects revision times for all the article and talk pages and for
a set of desired pages. The purpose of this analysis is to find if pages
related to events are changed in a neighbourhood of the anniversary.

Data are stored in a database.

### events_analysis.py
The script accepts in input a list of desired pages and the wikipedia language
to be analyzed. It retrieves data from db about all the revisions of the specified
language and processes revisions' statistics for each found page, such as number of
edits, number of unique editors, edits made in a range of days around event's
anniversary, etc...
Data are outputted in a csv file, bz2 compressed

### word_frequency.py
Given a list of words, find the frequency of these words in a random set of
pages and in a list of desired pages (and the related talk pages).

Data are stored in a database.

### countwords_groups.py
Given a current dump, count words found on every UTP and return the results
by group (the group which the user belongs).
