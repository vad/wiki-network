import sys

class Tablr:
    cache = None
    end_pos = None
    identifier = None

    def __del__(self):
        self.cache.close()

    def start(self, size, identifier):
        import mmap

        self.cache = mmap.mmap(-1, size) #create an in-memory-file

        sys.stdout = self.cache
        self.identifier = identifier

    def stop(self):
        sys.stdout = sys.__stdout__  # restore stdout back to normal

        self.end_pos = self.cache.tell()

    def printData(self):
        self.cache.seek(0)
        table = []
        while self.cache.tell() < self.end_pos:
            l = self.cache.readline()
            if not l:
                break
            table.append(l.split(':')[1].strip())

        print "||%s||%s||" % (self.identifier, '||'.join(table))

    def printHeader(self):
        self.cache.seek(0)
        table = []
        while self.cache.tell() < self.end_pos:
            l = self.cache.readline()
            if not l:
                break
            table.append(l.split(':')[0].strip(' *'))

        print "||id||%s||" % ('||'.join(table),)


