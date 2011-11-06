#!/usr/bin/python
"""Add short description comment to each package in plan
CPP includes, comments and blank lines are skipped
Package ordering is not changed

Arguments:
  <plan>            Path to read plan from

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)
  -i --inplace      Edit plan inplace
"""

import os
import re
import sys
import shutil
import getopt

import help
import debinfo
from pool import Pool
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def parse_plan(plan):
    packages = set()
    for expr in plan:
        expr = re.sub(r'#.*', '', expr)
        expr = expr.strip()
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
    packagedir = pool.get(packages)

    for package in os.listdir(packagedir):
        path = os.path.join(packagedir, package)
        if path.endswith('.deb'):
            control = debinfo.get_control_fields(path)
            info[control['Package']] = control['Description']

    shutil.rmtree(packagedir)
    return info

def plan_lint(plan_path, pool_path):
    package_info = {}

    plan = file(plan_path, 'r').readlines()

    packages = parse_plan(plan)
    packages_info = get_packages_info(packages, pool_path)

    column_len = max([ len(package) + 5 for package in packages ])

    output = []
    for expr in plan:
        expr = expr.strip()
        if expr.startswith('#') or expr == '':  # skip comments/includes/blanks
            output.append(expr)

        else:
            expr = re.sub(r'#.*', '', expr)     # clean off old comments
            expr = expr.strip()
            description = packages_info[expr.lstrip("!")]
            output.append("%s # %s" % (expr.ljust(column_len),
                                       description.capitalize()))

    lastline = output[-1]
    if lastline is not '':
        output.append('')

    return "\n".join(output)

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
    newplan = plan_lint(plan_path, pool_path)

    if inplace:
        open(plan_path, "w").write(newplan)
    else:
        print newplan
    
    
if __name__=="__main__":
    main()

