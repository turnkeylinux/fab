"""Optional arbitrary CPP options to effect plan preprocessing:
  -D <name[=def]>  Predefine name as a macro, with supplied definition
                   If definition is not supplied, default is 1
  -U <name>        Cancel any previous definition of name
  -I <dir>         Include dir to add to list of dirs searched for header files

  Refer to cpp documentation (eg. man cpp) for options full description

"""

import os
import sys
from subprocess import *

from executil import getoutput

CPP_ARGS = ("-I", "-D", "-U")

class Error(Exception):
    pass

def getopt(argv):
    """get cpp arguments in argv -> (cpp_arguments, non_cpp_arguments)"""

    argv = argv[:]

    opts = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        
        for cpp_arg in CPP_ARGS:
            if arg.startswith(cpp_arg):
                if arg == cpp_arg:
                    opt = arg
                    try:
                        val = argv[i + 1]
                    except IndexError:
                        raise Error("no value for option " + opt)

                    del argv[i + 1]
                    del argv[i]
                else:
                    opt = arg[:len(cpp_arg)]
                    val = arg[len(cpp_arg):]

                    del argv[i]

                opts.append((opt, val))
                break
        else:
              i += 1
              
    return opts, argv

def _getoutput(command, input=None):
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate(input)[0]

    error = p.returncode
    if error:
        raise Error("command non-zero exitcode (%d)" % error, 
                    output, command, input)
    return output

def cpp(input, cpp_opts=[]):
    """preprocess <input> through cpp -> preprocessed output
       input may be path/to/file or iterable data type
    """

    args = []
    for opt, val in cpp_opts:
        args.append(opt + val)

    include_path = os.environ.get('FAB_PLAN_INCLUDE_PATH')
    if include_path:
        args.append("-I" + include_path)

    if os.path.isfile(input):
        return getoutput("cpp", input, *args)
    else:
        command = ["cpp"]
        command.extend(args)
        return _getoutput(command, input)

