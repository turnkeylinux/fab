#!/usr/bin/python
"""Executes command in chroot

Arguments:
  <chroot>          Path to chroot
  command           Command to execute in chroot
                    If no command is specified, /bin/bash is assumed (shell)
"""
import os
import sys
import getopt

import help
from chroot import Chroot
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <chroot> [command]" % sys.argv[0]

def main():
    args = sys.argv[1:]
    if not args:
        usage()
    
    if len(args) == 1:
        args.append("/bin/bash")
        
    chroot_path = args[0]
    
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    chroot = Chroot(chroot_path)
    chroot.system(*args[1:])
        
if __name__=="__main__":
    main()

