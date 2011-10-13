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
import cpp_opts
from utils import system_pipe, warning, fatal


@help.usage(__doc__ + cpp_opts.__doc__)
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
    if not len(sys.argv) > 1:
        usage()
    
    cmd_cpp, args, opts = cpp_opts.parse(sys.argv[1:],
                                         ['output='])
    
    if not args:
        usage()
        
    if not len(args) in (2, 3):
        usage("bad number of arguments")
    
    if args[0] == '-':
        plan_fh = sys.stdin
    else:
        plan_fh = file(args[0], "r")

    pool_path = args[1]
    
    try:
        bootstrap_path = args[2]
    except IndexError:
        bootstrap_path = None

    opt_out = None
    for opt, val in opts:
        if opt == '--output':
            opt_out = val

    cmd_cpp.append("-Ulinux")
    out = system_pipe(cmd_cpp, plan_fh.read(), quiet=True)[0]
    plan = calculate_plan(out)

    if bootstrap_path:
        if not os.path.isdir(bootstrap_path):
            fatal("bootstrap does not exist: " + bootstrap_path)
        
        out = fab.chroot_execute(bootstrap_path, "dpkg-query --show -f='${Package}\n'", get_stdout=True)
        for entry in out.split("\n"):
            plan.add(entry)

    fab.plan_resolve(pool_path, plan, opt_out)

        
if __name__=="__main__":
    main()

