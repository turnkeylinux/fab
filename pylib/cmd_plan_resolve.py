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
import plan
from chroot import Chroot
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> [ /path/to/bootstrap ]" % sys.argv[0]

def bootstrap_packages(bootstrap_path):
    if not os.path.isdir(bootstrap_path):
        fatal("bootstrap does not exist: " + bootstrap_path)

    chroot = Chroot(bootstrap_path, chrootmounts=False)
    output = chroot.execute("dpkg-query --show -f='${Package}\\n'",
                            get_stdout=True)

    return set(output.splitlines())

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.getopt(args, "o:p:h",
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
        packages = bootstrap_packages(bootstrap_path)
    except IndexError:
        packages = set()

    spec = plan.resolve(plan_path, pool_path, cpp_opts, packages)
    spec = "\n".join(spec) + "\n"

    if output_path is None:
        print spec
    else:
        open(output_path, "w").write(spec)
    
    
if __name__=="__main__":
    main()


