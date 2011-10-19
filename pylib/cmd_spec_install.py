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
from cli_common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <spec> <pool> <chroot>" % sys.argv[0]

def spec_install(pool, spec_fh, chroot_path):
    chroot_path = realpath(chroot_path)
    pkgdir_path = join(chroot_path, "var/cache/apt/archives")

    if isfile(spec_fh):
        spec_lines = open(spec_fh, "r").readlines()
    else:
        spec_lines = spec_fh.splitlines()

    packages = set()
    for package in spec_lines:
        packages.add(package)

    pool = Pool(pool_path)
    pool.get(packages, pkgdir_path)

    c = Chroot(chroot_path)
    c.mountpoints()
    c.apt_install(pkgdir_path)
    c.apt_clean()
    c.umountpoints()

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
        fh = sys.stdin
    else:
        fh = file(args[0], "r")

    pool = args[1]
    chroot = args[2]
    
    if not os.path.isdir(chroot):
        fatal("chroot does not exist: " + chroot)

    spec_install(pool, fh.read(), chroot)

        
if __name__=="__main__":
    main()

