# -*- coding: utf-8 -*-
##########################################################################
#                                                                        #
#  This program is free software; you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation; version 2 of the License.               #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
#  This code is part of the trustlet project (http://trustlet.org)       #
#                                                                        #
##########################################################################



import os
import cPickle as pickle
from gzip import GzipFile
import re


mtime = lambda f: int(os.stat(f).st_mtime)

def load(key,path,version=False,fault=None,cachedcache=True,info=False):
    """
    Cache.
    Loads data stored by save.
    fault is the value returned if key is not stored in cache.
    If info will return data and metadata (data: load(...)['dt'])
    """

    #print '                   ',path
    #return fault

    def onlydata(x):
        if hasattr(x,'has_key') and x.has_key('dt'):
            return x['dt']

        print 'Warning: old cache format'
        return x

    getret = info and (lambda x: x) or onlydata


    def checkversion(x):
        if version is False:
            return getret(x)

        if not hasattr(x,'has_key') or not x.has_key('vr') or x['vr']!=version:
            return fault
        else:
            return getret(x)

    #memory cache
    if not globals().has_key('cachedcache'):
        #print 'create cache'
        globals()['cachedcache'] = {}
    cache = globals()['cachedcache']

    if os.path.exists(path) and cache.has_key(path) and cachedcache and mtime(path) == cache[path][0]:
        # check if cachedcache is valid -> mtime()...

        if cache[path][1].has_key(hashable(key)):
            #xprint 'DEBUG: cachedcache hit'
            return checkversion(cache[path][1][hashable(key)])

    #if cachedcache: print 'DEBUG: cachedcache fault'

    try:
        d = pickle.load(GzipFile(path))
    except:
        return fault

    if d.has_key(hashable(key)):
        data = d[hashable(key)]
    else:
        return fault

    #save in memory cache
    cache[path] = (mtime(path),d) # (mtime,data)
    #print '*****************************',type(data)
    #return None
    return checkversion(data)


def hashable(x):
    """
    Cache.
    Return an hashable object that can be used as key in dictionary cache.
    """
    if type(x) in (str,tuple,frozenset,int,float):
        return x
    if type(x) is list:
        return (list,)+tuple(x)
    if type(x) is set:
        return frozenset(x)
    if type(x) is dict:
        tupleslist = []
        for k,v in x.iteritems():
            tupleslist.append( (k,v) )
        return frozenset(tupleslist)

    raise TypeError,"I don't know this type "+str(type(x))

    
def getCollaborators( rawWikiText, search, searchEn ):
    rex = '\[\[(%s|%s)\:([^]]*)\]\]' % (search, searchEn)
    matches = re.finditer(rex, rawWikiText)

    weights = {}
    for u in matches:
        un = u.group(1)
        weights[un] = weights.get(un, 0) + 1

    return [(k,v) for k,v in weights.iteritems()]

