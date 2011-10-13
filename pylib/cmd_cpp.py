#!/usr/bin/python
"""Pre-process a plan

Arguments:
  <plan>         Path to read plan from (- for stdin)
                 If path/to/plan, dir of plan will be searched for header files

"""

import sys
import help
import cpp
    
@help.usage(__doc__ + cpp.__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def main():
    args = sys.argv[1:]
    if not args or '-h' in args:
        usage()
    
    cpp_opts, args = cpp.getopt(sys.argv[1:])

    if not args:
        usage()

    plan_path = args[0]
    print cpp.cpp(plan_path, cpp_opts)
        
if __name__=="__main__":
    main()

