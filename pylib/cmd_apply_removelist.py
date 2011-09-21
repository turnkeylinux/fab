#!/usr/bin/python
"""Removes files and folders as specified by removelist from the path

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <path>            Path containing removelist entries (ie. chroot)

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
    print >> sys.stderr, "Syntax: %s <removelist> <path>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", [])
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not len(args) == 2:
        usage()
    
    if args[0] == '-':
        input = sys.stdin
    else:
        input = file(args[0], "r")

    rmlist = read_filehandle(input)
    path = args[1]
    
    if not isdir(path):
        fatal("path does not exist: " + path)

    fab.apply_removelist(rmlist, path)

        
if __name__=="__main__":
    main()

