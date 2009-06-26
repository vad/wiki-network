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

    
def getCollaborators( rawWikiText, i18n, lang ):
    """
    return a list of tuple with ( user, value ), where user is the name of user
    that put a message on the page, and the value is the number of times that
    he appear in rawText passed.
    parameter:
       lang: lang of wiki [it|nap|vec|en|la]
       rawWikiText: text in wiki format (normally discussion in wiki)
    """
    import re
    from string import index

    resname = []

    start = 0
    search = '[['+i18n[lang][1]+":"
    searchEn = '[['+i18n['en'][1]+":"
    io = len(search)

    while True:
        #search next user
        try:
            iu = index( rawWikiText, search, start ) #index of username
        except ValueError:
            if search == searchEn:
                break
            
            # now search for English signatures
            search = searchEn
            start = 0
            io = len(search)
            continue
            
        #begin of the username
        start = iu + io
        #find end of username with regex
        username = re.findall( "[^]|&/]+",rawWikiText[start:] )[0]
        
        if username == '' or username == None:
            print "Damn! I cannot be able to find the name!"
            print "This is the raw text:"
            print rawWikiText[start:start+30]
           
            print "What is the end character? (all the character before first were ignored)"
            newdelimiter = sys.stdin.readline().strip()[0]
            
            try:
                end.append( index( rawWikiText, newdelimiter, start ) )
            except ValueError:
                print "Damn! you give me a wrong character!.."
                exit(0)


        resname.append( username ) # list of all usernames (possibly more than one times for one)
        start += len(username) + 1 # not consider the end character
        
    #return a list of tuple, the second value of tuple is the weight    
    return weight( resname )


def weight( list, diz=False ):
    """
    takes a list of object and search for each object
    other occurrences of object equal to him.
    Return a list of tuple with (object,n) where object is object (repeated only once)
    and n is the number of times that he appear in list
    Parameter:
      list: list of object
    Example:
      weight( ["mario","pluto","mario"] )
      ---> [("mario",2),("pluto",1)]
    """
    if diz:
        listweight = {}
    else:
        listweight = []
    tmp = list
    
    def update( list, val, diz=False ):

        if diz:
            if list.has_key(val):
                new = list.get(val)
                new += 1
                list[val] = new
            else:
                list[val] = 1

        else:
            find = False
            
            for x in xrange(len(list)):
                if list[x][0] == val:
                    find = True
                    break

            if find:
                new = list[x][1] + 1
                del list[x]
                list.append( (val,new) )
            else:
                list.append( (val,1) )

        return

    for x in tmp:
        update( listweight, x, diz=diz )

    return listweight
