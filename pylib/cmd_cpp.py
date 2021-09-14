#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Preprocess a plan

Arguments:
  <plan>         Path to read plan from
                 If path/to/plan, dir of plan will be searched for header files

Supports the following subset of standard cpp(1) options:
  -D <name[=def]>  Predefine name as a macro, with optional definition
                   If definition is not specified, default is 1
  -U <name>        Cancel any previous definition of name
  -I <dir>         Include dir to add to list of dirs searched for header files

See cpp(1) man page for further details.

"""

import sys
import help
import cpp


@help.usage(__doc__)
def usage():
    print("Syntax: %s [-options] <plan>" % sys.argv[0], file=sys.stderr)


def main():
    args = sys.argv[1:]
    if not args or "-h" in args:
        usage()

    cpp_opts, args = cpp.getopt(sys.argv[1:])

    if not args:
        usage()

    plan_path = args[0]
    print(cpp.cpp(plan_path, cpp_opts))


if __name__ == "__main__":
    main()
