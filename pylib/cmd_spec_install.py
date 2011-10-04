#!/usr/bin/python
"""Install packages into chroot according to spec

Arguments:
  <spec>            Path to read spec from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH
  <chroot>          Path to chroot

"""


import os
import sys
import getopt

import fab
import help
from utils import fatal


@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <spec> <pool> <chroot>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not len(args) == 3:
        usage()
    
    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")

    pool = args[1]
    chroot = args[2]
    
    if not os.path.isdir(chroot):
        fatal("chroot does not exist: " + chroot)

    fab.spec_install(pool, fh.read(), chroot)

        
if __name__=="__main__":
    main()

