import os
import re
import sys
from tempfile import TemporaryDirectory
from debian import debfile
from typing import Set, List, Dict, Iterable, Match
import hashlib

def parse_plan(plan: str) -> Set[str]:
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

def get_packages_info(packages: List[str], pool_path: str) -> Dict[str, str]:
    info = {}

    from pool_lib import Pool
    pool = Pool(pool_path)

    tmpdir = TemporaryDirectory()
    pool.get(tmpdir.name, packages, strict=True)

    for package in os.listdir(tmpdir.name):
        path = os.path.join(tmpdir.name, package)
        if path.endswith('.deb'):
            control = debfile.DebFile(path).control.debcontrol()
            info[control['Package']] = control['Description']

    return info

def plan_lint(plan_path: str, pool_path: str) -> str:
    with open(plan_path, 'r') as fob:
        plan = fob.read().strip()

    packages = parse_plan(plan)
    packages_info: Dict[str, str] = get_packages_info(list(packages), pool_path)

    if not packages:
        column_len = 0
    else:
        column_len = max([ len(package) for package in packages ])

    comments = {}
    def get_comment_key(m: Match) -> str:
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
