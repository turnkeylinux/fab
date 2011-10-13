#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH

Optional Arguments:
  bootstrap         Extract list of installed packages from the bootstrap and
                    append to the plan

Options:
  --output=         Path to spec-output (default is stdout)

"""

import os
import re
import sys

import help
import fab
import cpp

import getopt
from utils import warning, fatal

@help.usage(__doc__ + cpp.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> <pool> [ /path/to/bootstrap ]" % sys.argv[0]

def calculate_plan(declarations):
    packages = set()
    for declaration in declarations.splitlines():
        declaration = re.sub(r'#.*', '', declaration)
        declaration = declaration.strip()
        if not declaration:
            continue
        
        if declaration.startswith("!"):
            package = declaration[1:]

            if package in packages:
                packages.remove(package)
            else:
                warning("retraction failed. package was not declared: " + package)

        else:
            package = declaration
            packages.add(package)
    
    return packages

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = getopt.getopt(args, "o:h", ["output="])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()
    
    if not len(args) in (2, 3):
        usage("bad number of arguments")

    output_path = None
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt in ('-o', '--output'):
            output_path = val
    
    plan_path = args[0]
    pool_path = args[1]
    
    try:
        bootstrap_path = args[2]
    except IndexError:
        bootstrap_path = None

    cpp_opts += [ ("-U", "linux") ]
    out = cpp.cpp(plan_path, cpp_opts)
    plan = calculate_plan(out)

    if bootstrap_path:
        if not os.path.isdir(bootstrap_path):
            fatal("bootstrap does not exist: " + bootstrap_path)
        
        out = fab.chroot_execute(bootstrap_path, "dpkg-query --show -f='${Package}\n'", get_stdout=True)
        for entry in out.split("\n"):
            plan.add(entry)

    fab.plan_resolve(pool_path, plan, output_path)
        
if __name__=="__main__":
    main()

