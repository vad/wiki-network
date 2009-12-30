import sys
from time import time

class Timr(object):
    counters = {}
    main_counter = None
    name = None
    
    def __init__(self, name=None):
        self.name = name
        
    def __enter__(self):
        self.start(self.name)
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop(self.name)

    def start(self, name=None):
        if name:
            print >> sys.stderr, "START %s" % name
            self.counters[name] = time()
        else:
            print >> sys.stderr, "START TIMER"
            self.main_counter = time()

    def stop(self, name=None):
        if name:
            print >> sys.stderr, "STOP %s: %6f" % (name,  time() - self.counters[name])
        else:
            print >> sys.stderr, "STOP TIMER: %6f" % (time() - self.main_counter, )
