#!/usr/bin/python
"""Umount chroot virtual filesystems if mounted

Arguments:
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
    print >> sys.stderr, "Syntax: %s <chroot>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", [])
    except getopt.GetoptError, e:
        usage(e)

    if not len(args) == 1:
        usage()
    
    chroot = args[0]
    
    if not isdir(chroot):
        fatal("chroot does not exist: " + chroot)

    fab.Chroot(chroot).umountpoints()


        
if __name__=="__main__":
    main()

