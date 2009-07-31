import sys, mmap

class Tablr:
    cache = None
    end_pos = None
    identifier = None

    def __del__(self):
        self.cache.close()

    def start(self, size, identifier):
        self.cache = mmap.mmap(-1, size) #create an in-memory-file

        sys.stdout = self.cache
        self.identifier = identifier

    def stop(self):
        sys.stdout = sys.__stdout__  # restore stdout back to normal

        self.end_pos = self.cache.tell()

    def printData(self):
        self.cache.seek(0)
        table = [] # general values
        groupTable = {} # group values

        while self.cache.tell() < self.end_pos:
            l = self.cache.readline()
            if not l:
                break
            tmp = l.strip(' *').split(':')

            if len(tmp) == 3:
                #format: " * GROUP : data : value"
                group_values = groupTable.setdefault(tmp[0].strip(), [])
                group_values.append(tmp[2].strip())
            else:
                #format: " * data : value"
                table.append(tmp[1].strip())

        if table:
            print "||%s||%s||" % (self.identifier, '||'.join(table))

        if groupTable:
            print "GROUP TABLES:"
            for group_name, group_values in groupTable.iteritems():
                print "||%s_%s||%s||" % (group_name, self.identifier, '||'.join(group_values))


    def printHeader(self):
        self.cache.seek(0)
        table = []
        groupTable = []
        while self.cache.tell() < self.end_pos:
            l = self.cache.readline()
            if not l:
                break
            tmp = l.strip(' *').split(':')

            if len(tmp) == 3:
                #format: " * GROUP : data_description : value"
                desc = tmp[1].strip()
                if desc not in groupTable:
                    groupTable.append(desc)
            else:
                #format: " * data_description : value"
                table.append(tmp[0].strip())

        if table:
            print 'HEADER:'
            print "||id||%s||" % ('||'.join(table),)

        if groupTable:
            print "GROUP TABLES HEADER:"
            print "||id||%s||" % ('||'.join(groupTable),)


