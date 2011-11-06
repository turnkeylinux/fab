#!/usr/bin/python
"""
Install packages into chroot

Plan and spec type input files are accepted.
If a package is specified without a version, install the newest version.

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)
  --no-deps         Do not resolve and install package dependencies

  (Also accepts fab-cpp options to effect plan preprocessing)
"""

import re
import os
import sys
import getopt

import help
import cpp
import plan
from installer import Installer
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> < inputfile | package[=version] ... >"  % sys.argv[0]

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.gnu_getopt(args, 'p:',
                                   ['pool=', 'no-deps'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if not len(args) > 1:
        usage("bad number of arguments")

    pool_path = None
    opt_resolve_deps = True

    for opt, val in opts:
        if opt in ('-p', '--pool'):
            pool_path = val

        elif opt in ('--no-deps'):
            opt_resolve_deps = False

    chroot_path = args[0]
    input = args[1:]

    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    if os.path.isfile(input[0]):
        plan_path = input[0]
        packages = set(input[1:])
    else:
        plan_path = None
        packages = set(input)

    packages = plan.resolve(plan_path, pool_path, cpp_opts, packages,
                            opt_resolve_deps)

    installer = Installer(chroot_path, pool_path)
    installer.install(packages)


if __name__=="__main__":
    main()

