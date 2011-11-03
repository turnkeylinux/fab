#!/usr/bin/python
"""
Install packages into chroot

If a package is specified without a version, install the newest version.

Argument:
  <chroot>          Path to chroot
    
Option:
  -i --input <file> File from which we read package list (- for stdin)
                    Plan and spec type input are accepted
  -p --pool         Mandatory: Relative or absolute pool path
                               Defaults to environment: POOL
  --no-deps         Do not resolve and install package dependencies

"""

import re
import os
import sys
import getopt

import help
import cpp
from plan import Plan
from installer import Installer
from common import get_poolpath, fatal

@help.usage(__doc__ + cpp.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> [ package[=version] ... ]" % sys.argv[0]

def plan_resolve(cpp_opts, pre_processed, pool_path, resolve_deps):
    cpp_opts += [ ("-U", "linux") ]

    plan = Plan(pool_path)
    
    print "processing as if plan..."
    plan.process("\n".join(pre_processed), cpp_opts)
    packages = set(plan.packages)

    if resolve_deps:
        print "resolving dependencies..."
        spec = plan.resolve_to_spec()
        packages.update(spec.list())

    return packages

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.gnu_getopt(args, 'i:p:',
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
                cpp_opts += [ ("-I", os.path.dirname(val)) ]

        elif opt in ('-p', '--pool'):
            pool_path = val

        elif opt in ('--no-deps'):
            opt_resolve_deps = False

    chroot_path = args[0]
    pre_processed = args[1:]

    if input is not None:
        pre_processed.extend(input.readlines())

    pool_path = get_poolpath(pool_path)
    
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    packages = plan_resolve(cpp_opts, pre_processed, pool_path,
                            opt_resolve_deps)

    installer = Installer(chroot_path, pool_path)
    installer.install(packages)


if __name__=="__main__":
    main()

