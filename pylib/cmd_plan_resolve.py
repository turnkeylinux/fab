#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan> := ( - | path/to/plan | package )

Options:
  -o --output       Path to spec-output (default is stdout)
  -p --pool=PATH    Set pool path (default: $FAB_POOL_PATH)

  --bootstrap=PATH  Extract list of installed packages from the bootstrap and
                    append to the plan

  (Also accepts fab-cpp options to effect plan preprocessing)

"""

import os
from os.path import *
import re
import sys
import getopt

from stdtrap import StdTrap

import help
import cpp

from plan import Plan
from chroot import Chroot
from common import fatal, gnu_getopt

import debinfo

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> ..." % sys.argv[0]

def iter_packages(root):
    def parse_status(path):
        control = ""
        for line in file(path).readlines():
            if not line.strip():
                yield control
                control = ""
            else:
                control += line

        if control.strip():
            yield control

    for control in parse_status(join(root, "var/lib/dpkg/status")):
        d = debinfo.parse_control(control)
        if d['Status'] == 'install ok installed':
            yield d['Package']

def annotate_spec(spec, packageorigins):
    if not spec:
        return ""

    annotated_spec = []

    column_len = max([ len(s) + 1 for s in spec ])
    for s in spec:
        name = s.split("=")[0]
        origins = " ".join(list([ origin for origin in packageorigins[name] ]))
        annotated_spec.append("%s # %s" % (s.ljust(column_len), origins))

    return "\n".join(annotated_spec)

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = gnu_getopt(args, "o:p:h",
                                ["output=",
                                 "pool=",
                                 "bootstrap=",])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()
    
    output_path = None
    pool_path = None
    bootstrap_path = None
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt in ('-o', '--output'):
            output_path = val
    
        if opt in ('-p', '--pool'):
            pool_path = val

        if opt == "--bootstrap":
            if not os.path.isdir(val):
                fatal("directory does not exist (%s)" % val)

            bootstrap_path = val

    if pool_path is None:
        pool_path = os.environ.get('FAB_POOL_PATH')

    plan = Plan(pool_path=pool_path)
    if bootstrap_path:
        bootstrap_packages = set(iter_packages(bootstrap_path))
        plan |= bootstrap_packages

        for package in bootstrap_packages:
            plan.packageorigins.add(package, 'bootstrap')

    for arg in args:
        if arg == "-" or exists(arg):
            subplan = Plan.init_from_file(arg, cpp_opts, pool_path)
            plan |= subplan

            for package in subplan:
                plan.packageorigins.add(package, arg)

        else:
            plan.add(arg)
            plan.packageorigins.add(arg, '_')

    trap = StdTrap(stdout=(output_path is None), stderr=False)
    try:
        spec = plan.resolve()
    finally:
        trap.close()

    if output_path is None:
        trapped_output = trap.stdout.read()
        print >> sys.stderr, trapped_output,

    spec = annotate_spec(spec, plan.packageorigins)

    if output_path is None:
        print spec
    else:
        open(output_path, "w").write(str(spec) + "\n")

if __name__=="__main__":
    main()


