#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH

Options:
  --output=         Path to spec-output (default is stdout)
  --chroot=         Path to chroot installed with packages to append to <plan>
  
"""

import os
import re
import sys

import help
import fab
import cpp_opts
from utils import system_pipe, warning


@help.usage(__doc__ + cpp_opts.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> <pool>" % sys.argv[0]

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
                                         ['output=', 'chroot='])
    
    if not len(args) == 2:
        usage()
    
    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")

    pool = args[1]

    opt_out = None
    opt_chroot = None
    for opt, val in opts:
        if opt == '--output':
            opt_out = val
        elif opt == '--chroot':
            opt_chroot = val

    cmd_cpp.append("-Ulinux")
    out, err = system_pipe(cmd_cpp, fh.read(), quiet=True)
    plan = calculate_plan(out)

    if opt_chroot:
        if not os.path.isdir(opt_chroot):
            fatal("chroot does not exist: " + opt_chroot)
        
        out = fab.chroot_execute(opt_chroot, "dpkg-query --show -f='${Package}\n'", get_stdout=True)
        for entry in out.split("\n"):
            plan.add(entry)

    fab.plan_resolve(pool, plan, opt_out)

        
if __name__=="__main__":
    main()

