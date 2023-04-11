from typing import Optional, List, Tuple, Generator, Iterable
from os.path import join
import os
from debian.deb822 import Deb822
import logging
from .plan import Plan, Spec, PackageOrigins

logger = logging.getLogger("fab.resolve")

def iter_packages(root: str) -> Generator[str, None, None]:
    control = ''
    with open(join(root, "var/lib/dpkg/status"), 'r') as fob:
        for line in fob:
            if not line.strip():
                deb = Deb822(control.splitlines())
                if deb['Status'] == 'install ok installed':
                    yield deb['Package']
                control = ''
            else:
                control += line

def annotate_spec(repo_spec: Iterable[str], pool_spec: Iterable[str], packageorigins: PackageOrigins) -> str:
    if not repo_spec and not pool_spec:
        return ""

    annotated_spec = []

    column_len = max(len(s) + 1 for s in [*repo_spec, *pool_spec])
    for s in repo_spec:
        name = s.split('=')[0]
        origins = " ".join(origin for origin in packageorigins[name])
        annotated_spec.append("%s # %s" % (s.ljust(column_len), origins))
    for s in pool_spec:
        name = s.split('=')[0]
        origins = " ".join(origin for origin in packageorigins[name])
        annotated_spec.append("%s # %s [FORCE_POOL]" % (s.ljust(column_len), origins))

    return '\n'.join(annotated_spec)


def resolve_plan(
        output_path: str,
        bootstrap_path: Optional[str],
        pool_path: str,
        cpp_opts: List[Tuple[str, str]],
        plans: List[str]) -> None:

    plan = Plan(pool_path=pool_path)
    if bootstrap_path:
        bootstrap_packages = set(iter_packages(bootstrap_path))
        plan |= bootstrap_packages

        for package in bootstrap_packages:
            plan.packageorigins.add(package, "bootstrap")

    for plan_path in plans:
        if plan_path == '-' or os.path.exists(plan_path):
            subplan = Plan.init_from_file(plan_path, cpp_opts, pool_path)
            plan |= subplan

            for package in subplan:
                plan.packageorigins.add(package, plan_path)
        else:
            plan.add(plan_path)
            plan.packageorigins.add(plan_path, "_")

    spec, unresolved = plan.resolve()
    logger.debug("unresolved" + '\n'.join(unresolved))
    spec = annotate_spec(unresolved, spec, plan.packageorigins)
    logger.debug(spec)
    logger.debug(f"{output_path=}")

    if output_path == '-':
        print(spec)
    else:
        with open(output_path, 'w') as fob:
            fob.write(str(spec) + '\n')
