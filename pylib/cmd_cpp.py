#!/usr/bin/python
"""Pre-process a plan

Arguments:
  <plan>         Path to read plan from (- for stdin)
                 If path/to/plan, dir of plan will be searched for header files

"""

import sys

import help
import cpp_opts
from utils import system_pipe
    

@help.usage(__doc__ + cpp_opts.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def main():
    if not len(sys.argv) > 1:
        usage()
    
    cmd_cpp, args = cpp_opts.parse(sys.argv[1:])

    if not args:
        usage()

    if args[0] == '-':
        fh = sys.stdin
    else:
        fh = file(args[0], "r")

    system_pipe(cmd_cpp, fh.read())

        
if __name__=="__main__":
    main()

