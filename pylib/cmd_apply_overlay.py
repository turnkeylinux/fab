#!/usr/bin/python
"""Apply overlay ontop of given path

Arguments:
  <overlay>         Path to overlay
  <path>            Path to apply overlay ontop of (ie. chroot)

Options:
  --preserve        Perserve mode,ownership and timestamps

"""

import os
import sys
import getopt

import fab
import help
from utils import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <overlay> <path>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   ['preserve'])
    except getopt.GetoptError, e:
        usage(e)

    if not len(args) == 2:
        usage()
    
    overlay = args[0]
    dstpath = args[1]

    opt_preserve = False
    for opt, val in opts:
        if opt == '--preserve':
            opt_preserve = True

    for dir in [overlay, dstpath]:
        if not os.path.isdir(dir):
            fatal("does not exist: " + dir)

    fab.apply_overlay(overlay, dstpath, opt_preserve)

        
if __name__=="__main__":
    main()

