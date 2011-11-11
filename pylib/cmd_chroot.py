#!/usr/bin/python
"""Executes command in a new root
"""
import os
import sys
import getopt

import help
from chroot import Chroot
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <newroot> [ command ... ]" % sys.argv[0]

def main():
    args = sys.argv[1:]
    if not args:
        usage()
    
    if len(args) == 1:
        args.append("/bin/bash")
        
    newroot = args[0]
    
    if not os.path.isdir(newroot):
        fatal("chroot does not exist: " + newroot)

    chroot = Chroot(newroot)
    chroot.system(*args[1:])
        
if __name__=="__main__":
    main()

