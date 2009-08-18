import sys
from time import time

class Timr(object):
    counters = {}
    main_counter = None

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
            print >> sys.stderr, "STOP TIMER: %6f" % (time() - self.counters[name], )
