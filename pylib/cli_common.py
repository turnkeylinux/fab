import sys

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def warn(s):
    print >> sys.stderr, "warning: " + str(s)
