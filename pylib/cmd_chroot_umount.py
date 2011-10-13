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

import fab
import help
from cli_common import fatal, warning

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
    
    chroot = args[0]
    
    if not os.path.isdir(chroot):
        msg = "chroot does not exist: " + chroot
        if opt_strict:
            fatal(msg)
        else:
            warning(msg)
            sys.exit(0)
            
    fab.Chroot(chroot).umountpoints()


        
if __name__=="__main__":
    main()

