#!/usr/bin/python
"""Pre-process a plan (internal command)

Arguments:
  <plan>         Path to read plan from (- for stdin)
                 If path/to/plan, dir of plan will be searched for header files

Options:
  --cpp=         Arbitrary CPP definitions to effect plan preprocessing

"""

import os
import sys
import help
import getopt
import subprocess

from os.path import *
import re

class Error(Exception):
    pass

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def system_pipe(command, pipein):
    p = subprocess.Popen(command,
                         stdin = subprocess.PIPE, 
                         close_fds = True)
    return p.communicate(pipein)

def read_plan(fh):
    plan = ""
    for line in fh.readlines():
        plan += line
    return plan

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['cpp='])
    except getopt.GetoptError, e:
        usage(e)
    
    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not args:
        usage()

    opt_cpp = []
    inc = os.getenv('FAB_PLAN_INCLUDE_PATH')
    if inc:
        opt_cpp.append("-I" + inc)
    
    if args[0] == '-':
        input = sys.stdin
    else:
        input = file(args[0], "r")
        opt_cpp.append("-I" + dirname(args[0]))
    
    for opt, val in opts:
        if opt == '--cpp':
            opt_cpp.append(val)

    cmd = opt_cpp
    cmd.insert(0, "cpp")
    system_pipe(cmd, read_plan(input))

        
if __name__=="__main__":
    main()

