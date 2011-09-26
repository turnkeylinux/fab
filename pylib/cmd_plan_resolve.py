#!/usr/bin/python
"""Resolve plan into spec using latest packages from pool

Arguments:
  <plan>            Path to read plan from (- for stdin)
  <pool>            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH

Options:
  --exclude=        Path to spec of packages not to be resolved (ie. bootstrap)
  --output=         Path to spec-output (default is stdout)
  --cpp=            Arbitrary CPP definitions to effect plan preprocessing

"""

import re
import os
import sys
import help
import getopt
from os.path import *

import fab
from utils import *


@help.usage(__doc__)
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
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['exclude=', 'output=', 'cpp='])
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not len(args) == 2:
        usage()
    
    cmd_cpp = ['fab-cpp', '-']
    opt_cpp = ['-Ulinux']
    opt_out = None
    opt_exclude = None

    inc = os.getenv('FAB_PLAN_INCLUDE_PATH')
    if inc:
        opt_cpp.append("-I" + inc)
    
    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")
        opt_cpp.append("-I" + dirname(args[0]))

    pool = args[1]
    
    for opt, val in opts:
        if opt == '--cpp':
            opt_cpp.append(val)
        elif opt == '--output':
            opt_out = val
        elif opt == '--exclude':
            opt_exclude = val

    for o in opt_cpp:
        cmd_cpp.append("--cpp=" + o)
    
    out, err = system_pipe(cmd_cpp, fh.read(), quiet=True)
    plan = calculate_plan(out)

    fab.plan_resolve(pool, plan, opt_exclude, opt_out)

        
if __name__=="__main__":
    main()

