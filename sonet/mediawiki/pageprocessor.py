import xml.etree.cElementTree as etree

class PageProcessor(object):
    count = 0
    count_archive = 0
    ecache = None
    tag = None
    user_talk_names = None
    search = None
    lang = None

    def __init__(self, ecache=None, tag=None, user_talk_names=None,
                 search=None, lang=None):
        self.ecache = ecache
        self.tag = tag
        self.user_talk_names = user_talk_names
        self.search = search
        self.lang = lang

    def start(self, f):
        import inspect
        dfunc = {}

        ## FIND PROCESS METHODS
        for member_name, type_ in inspect.getmembers(self):
            if not member_name.startswith('process_'): continue
            member = self.__getattribute__(member_name)
            if not inspect.ismethod(member): continue
            dfunc[self.tag[member_name[8:]]] = member

        context = etree.iterparse(f)
        for elem in (elem for _, elem in context if elem.tag in dfunc):
            dfunc[elem.tag](elem)
            elem.clear()
        del context