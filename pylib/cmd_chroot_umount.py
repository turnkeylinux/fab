#!/usr/bin/python
"""Umount chroot virtual filesystems if mounted

Arguments:
  <chroot>          Path to chroot

Options:
  --strict          Fatal error if chroot does not exist

"""


import os
import sys
import getopt

import help
from chroot import Chroot
from common import fatal, warn

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <chroot>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", 
                                       ['strict'])
    except getopt.GetoptError, e:
        usage(e)

    opt_strict = False
    for opt, val in opts:
        if opt == '--strict':
            opt_strict = True

    if not len(args) == 1:
        usage()
    
    chroot_path = args[0]
    
    if not os.path.isdir(chroot_path):
        msg = "chroot does not exist: " + chroot_path
        if opt_strict:
            fatal(msg)
        else:
            warn(msg)
            sys.exit(0)

    Chroot(chroot_path).umount_chrootmounts()

        
if __name__=="__main__":
    main()

