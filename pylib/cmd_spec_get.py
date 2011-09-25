#!/usr/bin/python
"""Get packages according to spec

Arguments:
  <spec>            Path to read spec from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH
  <outdir>          Path to store packages

"""

import re
import os
import sys
import help
import getopt
from os.path import *

import fab
from utils import *


@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <spec> <pool> <outdir>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", [])
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not len(args) == 3:
        usage()
    
    if args[0] == '-':
        input = sys.stdin
    else:
        input = file(args[0], "r")

    spec = read_filehandle(input)
    pool = args[1]
    outdir = realpath(args[2])
    
    if not isdir(outdir):
        fatal("outdir does not exist: " + outdir)

    fab.spec_get(pool, spec, outdir)

        
if __name__=="__main__":
    main()

