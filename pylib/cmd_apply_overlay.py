#!/usr/bin/python
"""Apply overlay on top of given path

Arguments:
  <overlay>         Path to overlay
  <path>            Path to apply overlay ontop of (ie. chroot)

Options:
  --preserve        Perserve mode,ownership and timestamps

"""

import os
import sys
import getopt

import help
import executil
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <overlay> <path>" % sys.argv[0]

def apply_overlay(overlay, dstpath, preserve=False):
    opts = "-TdR"
    if preserve:
        opts += "p"
    executil.system("cp %s %s/ %s/" % (opts, overlay, dstpath))

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['preserve'])
    except getopt.GetoptError, e:
        usage(e)

    if not len(args) == 2:
        usage()
    
    overlay = args[0]
    dstpath = args[1]

    kws = {}
    for opt, val in opts:
        kws[opt[2:]] = val

    for dir in (overlay, dstpath):
        if not os.path.isdir(dir):
            fatal("does not exist: " + dir)

    apply_overlay(overlay, dstpath, **kws)

        
if __name__=="__main__":
    main()

