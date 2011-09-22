#!/usr/bin/python
"""Executes command in chroot

Arguments:
  <chroot>          Path to chroot

Options:
  command           Command to execute in chroot
                    If no command is specified, an interactive shell is assumed
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
    print >> sys.stderr, "Syntax: %s <chroot> [command]" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", [])
    except getopt.GetoptError, e:
        usage(e)

    if len(args) == 1:
        args.append("/bin/bash")
        
    if not len(args) == 2:
        usage()
    
    chroot = args[0]
    command = args[1]
    
    if not isdir(chroot):
        fatal("chroot does not exist: " + chroot)

    fab.chroot_execute(chroot, command)

        
if __name__=="__main__":
    main()

