#!/usr/bin/python
"""Removes files and folders as specified by removelist from the srcpath

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <srcpath>         Path containing removelist entries (ie. chroot)

Options:
  --dstpath=        Path to directory which will store removed items
                    If not specified, FAB_TMPDIR will be used
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
    print >> sys.stderr, "Syntax: %s [-options] <removelist> <srcpath>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", 
                                       ['dstpath='])
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
    srcpath = args[1]

    if not isdir(srcpath):
        fatal("srcpath does not exist: " + srcpath)

    opt_dstpath = None
    for opt, val in opts:
        if opt == '--dstpath':
            opt_removedir.append(val)

    fab.apply_removelist(rmlist, srcpath, opt_dstpath)

        
if __name__=="__main__":
    main()

