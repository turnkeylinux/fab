#!/usr/bin/python
"""Executes command in chroot

Arguments:
  <chroot>          Path to chroot

Optional Arguments:
  command           Command to execute in chroot
                    If no command is specified, /bin/bash is assumed (shell)

Options:
  --mount           Mount virtual filesystems proc and dev/pts into chroot

"""


import os
import sys
import getopt

import help
from chroot import Chroot
from common import fatal

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
        
    chroot_path = args[0]
    
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    chroot = Chroot(chroot_path, chrootmounts=chrootmounts)
    chroot.system(*args[1:])
        
if __name__=="__main__":
    main()

