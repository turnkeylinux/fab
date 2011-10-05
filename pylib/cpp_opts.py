"""Optional arbitrary CPP options to effect plan preprocessing:
  -D <name[=def]>  Predefine name as a macro, with supplied definition
                   If definition is not supplied, default is 1
  -U <name>        Cancel any previous definition of name
  -I <dir>         Include dir to add to list of dirs searched for header files

  Refer to cpp documentation (eg. man cpp) for options full description

"""

import os
import sys
import getopt

def parse(argv, longopts=[]):
    cmd_cpp = ['cpp']
    extra_opts = []
    
    try:
        opts, args = getopt.gnu_getopt(argv, "I:D:U:", longopts)
    except getopt.GetoptError, e:
        print >> sys.stderr, e
        sys.exit(1)
    
    if argv.count("-") == 1:
        args.insert(0, "-")

    inc = os.getenv('FAB_PLAN_INCLUDE_PATH')
    if inc:
        cmd_cpp.append("-I" + inc)
    
    if not args[0] == '-':
        cmd_cpp.append("-I" + os.path.dirname(args[0]))
    
    for opt, val in opts:
        if opt == '-I':
            cmd_cpp.append("-I" + val)
        elif opt == '-D':
            cmd_cpp.append("-D" + val)
        elif opt == '-U':
            cmd_cpp.append("-U" + val)
        else:
            extra_opts.append([opt, val])
    
    if longopts:
        return cmd_cpp, args, extra_opts
    
    return cmd_cpp, args


