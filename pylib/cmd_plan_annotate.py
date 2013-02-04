#!/usr/bin/python
# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Annotate plan with short package descriptions

(comments, cpp macros and already annotated packages are ignored)

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)
  -i --inplace      Edit plan inplace
"""

import os
import re
import sys
import getopt
import hashlib

import help
import debinfo

from pyproject.pool.pool import Pool
from temp import TempDir

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] path/to/plan" % sys.argv[0]

def parse_plan(plan):
    # strip c-style comments
    plan = re.sub(r'(?s)/\*.*?\*/', '', plan)
    plan = re.sub(r'//.*', '', plan)

    packages = set()
    for expr in plan.split('\n'):
        expr = re.sub(r'#.*', '', expr)
        expr = expr.strip()
        expr = expr.rstrip("*")
        if not expr:
            continue

        if expr.startswith("!"):
            package = expr[1:]
        else:
            package = expr

        packages.add(package)

    return packages

def get_packages_info(packages, pool_path):
    info = {}

    pool = Pool(pool_path)

    tmpdir = TempDir()
    pool.get(tmpdir.path, packages, strict=True)

    for package in os.listdir(tmpdir.path):
        path = os.path.join(tmpdir.path, package)
        if path.endswith('.deb'):
            control = debinfo.get_control_fields(path)
            info[control['Package']] = control['Description']

    return info

def plan_lint(plan_path, pool_path):
    package_info = {}

    plan = file(plan_path, 'r').read().strip()

    packages = parse_plan(plan)
    packages_info = get_packages_info(packages, pool_path)

    if not packages:
        column_len = 0
    else:
        column_len = max([ len(package) for package in packages ])

    comments = {}
    def get_comment_key(m):
        comment = m.group(1)
        key = hashlib.md5(comment).hexdigest()
        comments[key] = comment
        return "$" + key

    plan = re.sub(r'(?s)(/\*.*?\*/)', get_comment_key, plan)
    plan_linted = ""

    for line in plan.split('\n'):
        if re.search(r'#|\$|//', line) or line.strip() == "":
            plan_linted += line + "\n"
            continue

        expr = line.strip()
        description = packages_info[expr.lstrip("!").rstrip("*")]
        plan_linted += "%s # %s\n" % (expr.ljust(column_len + 3),
                                      description)

    plan_linted = re.sub(r'\$(\S+)', lambda m: comments[m.group(1)], plan_linted)
    return plan_linted

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "p:ih",
                                                    ["pool=",
                                                     "inplace"])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if not len(args) == 1:
        usage("bad number of arguments")

    inplace = False
    pool_path = None
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt in ('-i', '--inplace'):
            inplace = True

        if opt in ('-p', '--pool'):
            pool_path = val

    plan_path = args[0]
    if pool_path is None:
        pool_path = os.environ.get('FAB_POOL_PATH')

    newplan = plan_lint(plan_path, pool_path)

    if inplace:
        open(plan_path, "w").write(newplan)
    else:
        print newplan


if __name__=="__main__":
    main()

