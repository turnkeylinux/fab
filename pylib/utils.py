import sys

class Error(Exception):
    pass

def fatal(s):
    print >> sys.stderr, "FATAL: " + str(s)
    sys.exit(1)

def warning(s):
    print >> sys.stderr, "WARNING: " + str(s)
