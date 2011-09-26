#!/usr/bin/python
"""Pre-process a plan (internal command)

Arguments:
  <plan>         Path to read plan from (- for stdin)
                 If path/to/plan, dir of plan will be searched for header files

Optional arbitrary CPP definitions to effect plan preprocessing:
  -D <name>      Predefine name as a macro, with definition 1
  -U <name>      Cancel any previous definition of name
  -I <dir>       Include dir to add to list of dirs searched for header files

"""

import re
import os
import sys
import help
import getopt
from os.path import *

from utils import *

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "I:D:U:", [])
    except getopt.GetoptError, e:
        usage(e)
    
    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not args:
        usage()

    cmd_cpp = ['cpp']
    inc = os.getenv('FAB_PLAN_INCLUDE_PATH')
    if inc:
        cmd_cpp.append("-I" + inc)
    
    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")
        cmd_cpp.append("-I" + dirname(args[0]))
    
    for opt, val in opts:
        if opt == '-I':
            cmd_cpp.append("-I" + val)
        elif opt == '-D':
            cmd_cpp.append("-D" + val)
        elif opt == '-U':
            cmd_cpp.append("-U" + val)

    system_pipe(cmd_cpp, fh.read())

        
if __name__=="__main__":
    main()

