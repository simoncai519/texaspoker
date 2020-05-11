import os
class simple_logger(object):
    def __init__(self):
        pass
    def info(self, s):
        print(s, flush=True)
    def debug(self, s):
        print(s, flush=True)
    def error(self, s):
        print(s, flush=True)
    def warn(self, s):
        print(s, flush=True)

class file_logger(object):
    def __init__(self, name):
        self.file = open(name, 'w')
        self.name = name
        self.size = 0
    def __del__(self):
        self.file.close()
        if self.size == 0:
            os.remove(self.name)
    def info(self, s):
        print(s)
        self.file.write(s + '\n')
        self.size += len(s) + 1
    def debug(self, s):
        self.file.write(s + '\n')
        self.size += len(s) + 1
    def error(self, s):
        self.file.write(s + '\n')
        self.size += len(s) + 1
    def warn(self, s):
        self.file.write(s + '\n')
        self.size += len(s) + 1

