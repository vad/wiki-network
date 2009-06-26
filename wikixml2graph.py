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
##########################################################################

from bz2 import BZ2File
import trustletlib
import os

## etree
try:
  from lxml import etree
  print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")

#filename = "/hardmnt/neyo0/sra/setti/datasets/furwiki-20090619-pages-meta-current.xml.bz2"
filename = "/hardmnt/neyo0/sra/setti/datasets/dewiki-20090618-pages-meta-current.xml.bz2"
#the right translation for "Discussion User" in the language in key
i18n = trustletlib.load('language_parameters', os.path.join( os.environ['HOME'], 'shared_datasets', 'WikiNetwork', 'languageparameters.c2' ), fault=False ) 
page_tag = u'{http://www.mediawiki.org/xml/export-0.3/}page'
title_tag = u'{http://www.mediawiki.org/xml/export-0.3/}title'
revision_tag = u'{http://www.mediawiki.org/xml/export-0.3/}revision'
text_tag = u'{http://www.mediawiki.org/xml/export-0.3/}text'
lang = 'de'
search = '[['+i18n[lang][1]+':'
count = 0

def count_discussion(text):
    return trustletlib.getCollaborators(text, i18n, lang)

def process_page(elem):
    for child in elem:
        if child.tag == title_tag:
            a_title = child.text.split(':')
            if len(a_title) > 1 and a_title[0] == i18n[lang][0]:
                user = child.text
            else:
                return
        elif child.tag == revision_tag:
            for rc in child:
                if rc.tag == text_tag and rc.text:
                    count_discussion(rc.text)
                    global count
                    count += 1
                    print count


def fast_iter(context, func):
    for event, elem in context:
        func(elem)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context

src = BZ2File(filename)

fast_iter(etree.iterparse(src, tag=page_tag), process_page)

#cc = ''
#for event, elem in etree.iterparse(src, tag=page_tag):
#    if event == 'end' and elem.tag == page_tag:
#        process_page(elem)
#        #a_title = 
#        #if elem.findtext(title_tag) 
#        cc = elem
#        elem.clear()

