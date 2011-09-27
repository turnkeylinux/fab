#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH

Options:
  --exclude=        Path to spec of packages not to be resolved (ie. bootstrap)
  --output=         Path to spec-output (default is stdout)

"""

import re
import sys

import help
import fab
import cpp_opts
from utils import system_pipe


@help.usage(__doc__ + cpp_opts.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan> <pool>" % sys.argv[0]

def calculate_plan(raw):
    yes = set()
    no = set()
    for line in raw.split("\n"):
        line = re.sub(r'#.*', '', line)
        line = line.strip()
        if not line:
            continue
        m = re.match("!(.*)", line)
        if m:
            no.add(m.group(1))
        else:
            yes.add(line)

    return yes - no

def main():
    if not len(sys.argv) > 1:
        usage()
    
    cmd_cpp, args, opts = cpp_opts.parse(sys.argv[1:],
                                         ['exclude=', 'output=', 'cpp='])
    
    if not len(args) == 2:
        usage()
    
    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")

    pool = args[1]

    opt_out = None
    opt_exclude = None
    for opt, val in opts:
        if opt == '--output':
            opt_out = val
        elif opt == '--exclude':
            opt_exclude = val

    cmd_cpp.append("-Ulinux")
    out, err = system_pipe(cmd_cpp, fh.read(), quiet=True)
    plan = calculate_plan(out)

    fab.plan_resolve(pool, plan, opt_exclude, opt_out)

        
if __name__=="__main__":
    main()

