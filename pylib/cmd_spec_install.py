#!/usr/bin/python
"""Installs packages from given pool in chroot according to the spec

Arguments:
  <spec>            Path to read spec from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH
  <chroot>          Path to chroot

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
    print >> sys.stderr, "Syntax: %s <spec> <pool> <chroot>" % sys.argv[0]

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
    chroot = args[2]

    fab.Plan(pool).install(spec, chroot)

        
if __name__=="__main__":
    main()

