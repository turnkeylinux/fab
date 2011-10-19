#!/usr/bin/python
"""Executes command in chroot

Arguments:
  <chroot>          Path to chroot

Options:
  command           Command to execute in chroot
                    If no command is specified, an interactive shell is assumed
  --mount           Mount virtual filesystems in chroot

"""


import os
import sys
import getopt

import help
from installer import Chroot
from cli_common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> [command]" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", 
                                       ['mount'])
    except getopt.GetoptError, e:
        usage(e)

    chrootmounts = False
    for opt, val in opts:
        if opt == '--mount':
            chrootmounts = True

    if len(args) == 1:
        args.append("/bin/bash")
        
    if not len(args) == 2:
        usage()
    
    chroot_path = args[0]
    command = args[1]
    
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    chroot = Chroot(chroot_path, chrootmounts=chrootmounts)
    chroot.execute(command)

        
if __name__=="__main__":
    main()

