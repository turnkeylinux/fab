#!/usr/bin/python
"""Apply overlay ontop of given path

Arguments:
  <overlay>         Path to overlay
  <path>            Path to apply overlay ontop of (ie. chroot)

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
    print >> sys.stderr, "Syntax: %s <overlay> <path>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "")
    except getopt.GetoptError, e:
        usage(e)

    if not len(args) == 2:
        usage()
    
    overlay = args[0]
    dstpath = args[1]

    for dir in [overlay, dstpath]:
        if not isdir(dir):
            fatal("does not exist: " + dir)

    fab.apply_overlay(overlay, dstpath)

        
if __name__=="__main__":
    main()

