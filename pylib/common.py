import os
import sys
import getopt

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

def get_environ(env_conf):
    environ = {}
    if env_conf:
        for var in env_conf.split(":"):
            val = os.environ.get(var)
            if val is not None:
                environ[var] = val
            
    return environ

## cli common
def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def warn(s):
    print >> sys.stderr, "warning: " + str(s)
