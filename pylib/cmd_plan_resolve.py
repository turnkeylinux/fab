#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  [bootstrap]       Extract list of installed packages from the bootstrap and
                    append to the plan

Options:
  -p --pool         Mandatory: Relative or absolute pool path
                               Defaults to environment: POOL
  -o --output       Path to spec-output (default is stdout)

"""

import os
import re
import sys
import getopt

import help
import cpp
from plan import Plan
from chroot import Chroot
from common import get_poolpath, fatal

@help.usage(__doc__ + cpp.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> [ /path/to/bootstrap ]" % sys.argv[0]

def plan_resolve(cpp_opts, plan_path, pool_path, bootstrap_path):
    cpp_opts += [ ("-U", "linux") ]
    
    plan = Plan(pool_path)
    plan.process(plan_path, cpp_opts)
    
    if bootstrap_path:
        if not os.path.isdir(bootstrap_path):
            fatal("bootstrap does not exist: " + bootstrap_path)

        chroot = Chroot(bootstrap_path, chrootmounts=False)
        output = chroot.execute("dpkg-query --show -f='${Package}\\n'",
                                get_stdout=True)

        for package in output.splitlines():
            plan.add(package)

    spec = plan.resolve_to_spec()
    return "\n".join(spec.list())

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.getopt(args, "op:h", 
                                   ["output=",
                                    "pool="])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()
    
    if not len(args) in (1, 2):
        usage("bad number of arguments")

    output_path = None
    pool_path = None
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt in ('-o', '--output'):
            output_path = val
    
        if opt in ('-p', '--pool'):
            pool_path = val

    plan_path = args[0]
    pool_path = get_poolpath(pool_path)

    try:
        bootstrap_path = args[1]
    except IndexError:
        bootstrap_path = None

    spec = plan_resolve(cpp_opts, plan_path, pool_path, bootstrap_path)
    if output_path is None:
        print spec
    else:
        open(output_path, "w").write(spec)
    
    
if __name__=="__main__":
    main()


