import os
import sys
import tempfile
import getopt

class Error(Exception):
    pass

# patch gnu_getopt to support "-" as a argument (like getopt does)
def gnu_getopt(args, options, long_options=[]):
    def list_replace(l, a, b):
        for i in range(len(l)):
            if l[i] == a:
                l[i] = b

    list_replace(args, "-", "__stdin__")

    opts, args = getopt.gnu_getopt(args, options, long_options)

    list_replace(args, "__stdin__", "-")
    return opts, args
    
def mkdir(path):
    path = str(path)
    if not os.path.exists(path):
        os.makedirs(path)

def get_tmpdir():
    """return unique temporary directory path"""
    tmpdir = os.environ.get('FAB_TMPDIR', '/var/tmp')
    if not os.path.isabs(tmpdir):
        raise Error('FAB_TMPDIR is not absolute path')

    mkdir(tmpdir)
    return tempfile.mkdtemp(prefix="fab-", dir=tmpdir)

## cli common
def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def warn(s):
    print >> sys.stderr, "warning: " + str(s)
