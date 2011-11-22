import os
import temp

class Error(Exception):
    pass

class TempDir(temp.TempDir):
    def __init__(self):
        dir = os.environ.get('FAB_TMPDIR', '/var/tmp')
        if not os.path.isabs(dir):
            raise Error('FAB_TMPDIR is not absolute path')

        temp.TempDir.__init__(self, prefix="fab-", dir=dir)

