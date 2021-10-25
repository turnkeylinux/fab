from typing import Optional, List, Tuple, Generator, Iterable
from os.path import join
import os
from debian.deb822 import Deb822
from .plan import Plan, Spec, PackageOrigins

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

def annotate_spec(spec: Iterable[str], packageorigins: PackageOrigins) -> str:
    if not spec:
        return ""

    annotated_spec = []

    column_len = max(len(s) + 1 for s in spec)
    for s in spec:
        name = s.split('=')[0]
        origins = " ".join(origin for origin in packageorigins[name])
        annotated_spec.append("%s # %s" % (s.ljust(column_len), origins))

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

    spec = plan.resolve()
    spec = annotate_spec(spec, plan.packageorigins)

    if output_path == '-':
        print(spec)
    else:
        with open(output_path, 'w') as fob:
            fob.write(str(spec) + '\n')
