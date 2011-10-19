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

import help
import installer
from installer import Installer
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <spec> <pool> <chroot>" % sys.argv[0]


def spec_install(pool_path, spec_fh, chroot_path):
    if os.path.isfile(spec_fh):
        spec_lines = open(spec_fh, "r").readlines()
    else:
        spec_lines = spec_fh.splitlines()

    packages = set()
    for package in spec_lines:
        packages.add(package)

    installer = Installer(chroot_path, pool_path)
    installer.install(packages)

    
def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "")
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")

    if not len(args) == 3:
        usage()

    if args[0] == '-':
        spec_fh = sys.stdin
    else:
        spec_fh = file(args[0], "r")

    pool_path = args[1]
    chroot_path = args[2]
    
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    spec_install(pool_path, spec_fh.read(), chroot_path)

        
if __name__=="__main__":
    main()

