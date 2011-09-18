#!/usr/bin/python
"""Resolve plan into spec using the latest packages from a given pool

Arguments:
  <plan>                Path to read plan from (- for stdin)
  <pool>                Relative or absolute pool path
                        If relative, pool path is looked up in FAB_POOL_PATH

Options:
  --output=             Path to spec-output (default is stdout)
  --cpp=                Arbitrary CPP definitions to effect plan preprocessing

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
    print >> sys.stderr, "Syntax: %s [-options] <plan> <pool> [/path/to/bootstrap]" % sys.argv[0]

def clean_plan(raw):
    plan = []
    for line in raw.split("\n"):
        line = re.sub(r'#.*', '', line)
        line = line.strip()
        if not line:
            continue
        plan.append(line)
    return plan

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['output=', 'cpp='])
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
        
    if not len(args) == 2:
        usage()
    
    cmd_cpp = ['./fab-cpp', '-']
    opt_cpp = ['-Ulinux']
    opt_out = None

    inc = os.getenv('FAB_PLAN_INCLUDE_PATH')
    if inc:
        opt_cpp.append("-I" + inc)
    
    if args[0] == '-':
        input = sys.stdin
    else:
        input = file(args[0], "r")
        opt_cpp.append("-I" + dirname(args[0]))

    pool = args[1]
    
    for opt, val in opts:
        if opt == '--cpp':
            opt_cpp.append(val)
        elif opt == '--output':
            opt_out = val

    for o in opt_cpp:
        cmd_cpp.append("--cpp=" + o)
    
    out, err = system_pipe(cmd_cpp, read_filehandle(input), quiet=True)
    plan = clean_plan(out)

    fab.Plan(pool).resolve(plan, opt_out)

        
if __name__=="__main__":
    main()

