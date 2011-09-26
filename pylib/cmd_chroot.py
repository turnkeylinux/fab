#!/usr/bin/python
"""Executes command in chroot

Arguments:
  <chroot>          Path to chroot

Options:
  command           Command to execute in chroot
                    If no command is specified, an interactive shell is assumed
  --nomount         Do not mount virtual filesystems in chroot
"""


import os
import sys
import getopt

import fab
import help
from utils import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> [command]" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", 
                                       ['nomount'])
    except getopt.GetoptError, e:
        usage(e)

    opt_mountpoints = True
    for opt, val in opts:
        if opt == '--nomount':
            opt_mountpoints = False

    if len(args) == 1:
        args.append("/bin/bash")
        
    if not len(args) == 2:
        usage()
    
    chroot = args[0]
    command = args[1]
    
    if not os.path.isdir(chroot):
        fatal("chroot does not exist: " + chroot)

    fab.chroot_execute(chroot, command, opt_mountpoints)

        
if __name__=="__main__":
    main()

