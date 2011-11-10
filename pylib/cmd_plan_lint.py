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

from md5 import md5

from pool import Pool
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <plan>" % sys.argv[0]

def parse_plan(plan):
    # strip c-style comments
    plan = re.sub(r'(?s)/\*.*?\*/', '', plan)
    plan = re.sub(r'//.*', '', plan)
    
    packages = set()
    for expr in plan.split('\n'):
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

    plan = file(plan_path, 'r').read().strip()

    packages = parse_plan(plan)
    packages_info = get_packages_info(packages, pool_path)

    column_len = max([ len(package) for package in packages ])

    comments = {}
    def get_comment_key(m):
        comment = m.group(1)
        key = md5(comment).hexdigest()
        comments[key] = comment
        return "$" + key
    
    plan = re.sub(r'(?s)(/\*.*?\*/)', get_comment_key, plan)
    plan_linted = ""
    
    for line in plan.split('\n'):
        if re.search(r'#|\$|//', line) or line.strip() == "":
            plan_linted += line + "\n"
            continue

        expr = line.strip()
        description = packages_info[expr.lstrip("!")]
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
    newplan = plan_lint(plan_path, pool_path)

    if inplace:
        open(plan_path, "w").write(newplan)
    else:
        print newplan
    
    
if __name__=="__main__":
    main()

