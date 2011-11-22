#!/usr/bin/python
"""
Install packages into chroot

Arguments:
  <packages> := ( - | path/to/plan | path/to/spec | package[=version] ) ...
                If a version isn't specified, the newest version is implied.

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)
  -n --no-deps      Do not resolve and install package dependencies

  (Also accepts fab-cpp options to effect plan preprocessing)
"""

import re
import os
from os.path import *

import sys
import getopt

import help
import cpp
from plan import Plan
from installer import Installer
from common import fatal, gnu_getopt

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> <packages>" % sys.argv[0]

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = gnu_getopt(args, 'np:',
                                ['pool=', 'no-deps'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if not len(args) > 1:
        usage("bad number of arguments")

    pool_path = None
    opt_no_deps = False

    for opt, val in opts:
        if opt in ('-p', '--pool'):
            pool_path = val

        elif opt in ('-n', '--no-deps'):
            opt_no_deps = True

    chroot_path = args[0]
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    if pool_path is None:
        pool_path = os.environ.get('FAB_POOL_PATH')

    plan = Plan()
    for arg in args[1:]:
        if arg == "-" or exists(arg):
            plan |= Plan.init_from_file(arg, cpp_opts, pool_path)
        else:
            plan.add(arg)

    if not opt_no_deps:
        packages = list(plan.resolve())
    else:
        packages = list(plan)
        
    installer = Installer(chroot_path, pool_path)
    installer.install(packages)

if __name__=="__main__":
    main()

