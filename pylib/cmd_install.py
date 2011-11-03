#!/usr/bin/python
"""
Install packages into chroot

If a package is specified without a version, install the newest version.

Argument:
  <chroot>          Path to chroot
    
Option:
  -i --input <file> File from which we read package list (- for stdin)
  -p --pool         Mandatory: Relative or absolute pool path
                               Defaults to environment: POOL
  --no-deps         Do not resolve and install package dependencies

"""

import re
import os
import sys
import getopt

import help
from plan import Plan
from installer import Installer
from common import get_poolpath, fatal

# TODO:
#    add cpp support

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> [ package[=version] ... ]" % sys.argv[0]


def read_packages(fh):
    packages = set()
    for line in fh.readlines():
        line = re.sub(r'#.*', '', line)
        line = line.strip()
        if not line:
            continue
        packages.add(line)
    return packages
    
def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'ip:',
                                      ['input=', 'pool=', 'no-deps'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    input = None
    pool_path = None
    opt_resolve_deps = True

    for opt, val in opts:
        if opt in ('-i', '--input'):
            if val == '-':
                input = sys.stdin
            else:
                input = file(val, "r")

        elif opt in ('-p', '--pool'):
            pool_path = val

        elif opt in ('--no-deps'):
            opt_resolve_deps = False

    chroot_path = args[0]
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    pool_path = get_poolpath(pool_path)

    packages = set(args[1:])
    if input is not None:
        packages.update(read_packages(input))

    if opt_resolve_deps:
        print "resolving dependencies..."
        plan = Plan(pool_path)
        plan.packages.update(packages)
        
        spec = plan.resolve_to_spec()
        packages.update(spec.list())
    
    installer = Installer(chroot_path, pool_path)
    installer.install(packages)


        
if __name__=="__main__":
    main()

