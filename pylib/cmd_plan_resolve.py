#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  [bootstrap]       Extract list of installed packages from the bootstrap and
                    append to the plan

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)
  -o --output       Path to spec-output (default is stdout)

  (Also accepts fab-cpp options to effect plan preprocessing)

"""

import os
import re
import sys
import getopt

import help
import cpp
from plan import Plan
from chroot import Chroot
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> [ /path/to/bootstrap ]" % sys.argv[0]

def bootstrap_packages(bootstrap_path):
    if not os.path.isdir(bootstrap_path):
        fatal("bootstrap does not exist: " + bootstrap_path)

    chroot = Chroot(bootstrap_path)
    output = chroot.getoutput("dpkg-query --show -f='${Package}\\n'")

    return set(output.splitlines())

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.gnu_getopt(args, "o:p:h",
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

    try:
        bootstrap_path = args[1]
    except IndexError:
        bootstrap_path = None

    plan = Plan.init_from_file(plan_path, cpp_opts, pool_path)
    if bootstrap_path:
        plan |= bootstrap_packages(bootstrap_path)
        
    spec = plan.resolve()

    if output_path is None:
        print spec
    else:
        open(output_path, "w").write(str(spec) + "\n")
        
if __name__=="__main__":
    main()


