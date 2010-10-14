import xml.etree.cElementTree as etree
#from lxml import etree
from datetime import date
from random import random

class PageProcessor(object):
    count = 0
    count_archive = 0
    ecache = None
    tag = None
    user_talk_names = None
    search = None
    lang = None

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def start(self, f):
        import inspect
        dfunc = {}
        tag = self.tag
        tag_page = tag['page']

        ## FIND PROCESS METHODS
        for member_name, type_ in inspect.getmembers(self):
            if not member_name.startswith('process_'): continue
            member = self.__getattribute__(member_name)
            if not inspect.ismethod(member): continue
            dfunc[tag[member_name[8:]]] = member

        ## iterate over tags. skip if not in dfunc.
        ## self._skip is set by process_*() methods if all the tags have to be
        ## discarded up to the next page-tag (</page>)
        context = etree.iterparse(f)
        for elem in (elem for _, elem in context if elem.tag in dfunc and
                     (elem.tag == tag_page or not self._skip)):
            dfunc[elem.tag](elem)
            elem.clear()
            #while elem.getprevious() is not None:
            #    del elem.getparent()[0]
        del context

        self.end()

    def end(self):
        pass


class HistoryPageProcessor(PageProcessor):
    counter_pages = 0
    ## desired pages
    desired_pages = None
    ## initial date, used for comparison and substraction
    s_date = date(2000, 1, 1)
    _counter = None
    _title = None
    _type = None
    ## Whether the page should be skipped or not, according to its Namespace
    _skip = None
    threshold = 1.
    talkns = None
    _desired = False
    _editors = {}
    _date = None

    def get_number_of_editors(self, key_=None):
        if key_:
            return sum([1 for v in self._editors.values() if v == key_])
        else:
            return len(self._editors.keys())

    def set_desired(self, l):
        self.desired_pages = frozenset(l)

    def set_desired_from_csv(self, fn, encoding='latin-1'):
        import csv

        with open(fn, 'rb') as f:
            self.set_desired([l[0].decode(encoding) for l in csv.reader(f)
                              if l and not l[0][0] == '#'])

    def is_desired(self, title):
        return (title in self.desired_pages)

    def delattr(self, attrs):
        for attr in attrs:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    def process_title(self, elem):
        self.delattr(("_counter", "_type", "_title", "_skip", "_date"))
        self._editors.clear()

        a_title = elem.text.split(':')
        if len(a_title) == 1:
            self._type = 'normal'
            self._title = a_title[0]
        else:
            if a_title[0] == self.talkns:
                self._type = 'talk'
                self._title = a_title[1]
            else:
                self._skip = True
                return

        self._desired = self.is_desired(self._title)
        if not self._desired and self.threshold < 1.:
            if self.threshold == 0. or random() > self.threshold:
                self._skip = True
                return

        self._counter = {}

    def process_page(self, _):
        if not self._skip:
            self.save()
        self._skip = False

    def process_redirect(self, _):
        self._skip = True
