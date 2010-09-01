import sys
from time import time
import logging

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
            logging.info("START %s" % name)
            self.counters[name] = time()
        else:
            logging.info("START TIMER")
            self.main_counter = time()

    def stop(self, name=None):
        if name:
            logging.info("STOP %s: %6f" % (
                name,  time() - self.counters[name]))
        else:
            logging.info("STOP TIMER: %6f" % (time() - self.main_counter, ))
