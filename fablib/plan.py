# Copyright (c) TurnKey GNU/Linux - https://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
import re
from collections.abc import Generator, Iterable, Iterator
from logging import getLogger
from os.path import basename, join
from tempfile import TemporaryDirectory
from typing import Any, ClassVar, Union

from debian import deb822, debfile, debian_support
from pool_lib import Pool

from . import cpp

logger = getLogger("fab.plan")


class Error(Exception):
    pass


class PackageOrigins:
    """class for holding package origins for dependency annotation"""

    def __init__(self) -> None:
        self._origins: dict[str, list[str]] = {}

    def add(self, name: str, origin: str) -> None:
        name = name.split("=")[0].strip("*")
        if name not in self._origins:
            self._origins[name] = []

        self._origins[name].append(origin)

    def __getitem__(self, name: str) -> list[str]:
        return self._origins[name]


class Spec:
    """class for holding a spec"""

    def __init__(self) -> None:
        self._pkgs: dict[str, str] = {}

    def add(self, name: str, version: str) -> None:
        """add package name and version to spec"""
        self._pkgs[name] = version

    def remove(self, name: str) -> None:
        del self._pkgs[name]

    def __iter__(self) -> Iterator[str]:
        """return list of packages, as name=version"""
        for name, version in self._pkgs.items():
            yield f"{name}={version}"

    def __str__(self) -> str:
        return "\n".join(self._pkgs)

    def exists(self, key: str) -> bool:
        return key in self._pkgs


class Dependency:
    """This class represents a dependency.

    The restriction parameters are parsed and can be accessed
    as attributes but for now they are ignored when calculating equality.

    Whether two dependencies are equal depends only on the name.
    """

    class Restrict:
        RELATIONS: ClassVar[dict[str, list[int]]] = {
            "<<": [-1],
            "<=": [-1, 0],
            "=": [0],
            ">=": [0, 1],
            ">>": [1],
        }

        def __init__(self, relation: str, version: str) -> None:
            if relation not in self.RELATIONS:
                raise Error(f"bad relation ({relation})")

            self.relation = relation
            self.version = version

        def __hash__(self) -> int:
            return hash(self.relation) ^ hash(self.version)

        def __eq__(self, other: Any) -> bool:  # noqa: ANN401
            if other is None:
                return False

            return (
                self.relation == other.relation
                and self.version == other.version
            )

        def __contains__(self, version: str) -> bool:
            true_results = self.RELATIONS[self.relation]

            return (
                debian_support.version_compare(version, self.version)
                in true_results
            )

        def __str__(self) -> str:
            return self.relation + " " + self.version

    restrict: Restrict | None

    def __init__(self, string: str) -> None:
        """initialize Dependency from a control file formatted dependency
        e.g.,
            libgpmg1 (>= 1.19.6-1)
        exception:
            package*  # promote recommends
            package** # promote recommends + suggests
        """
        string = string.strip()

        m = re.match(
            r"([a-z0-9][a-z0-9\+\-\.]+)[\:a-z]{0,4}([\*]{0,2})(?:\s+\((.*?)\))?$",
            string,
        )
        if not m:
            raise Error(f"illegally formatted dependency ({string})")

        self.name = m.group(1)
        promote = m.group(2)
        parens = m.group(3)

        self.fields = ["Pre-Depends", "Depends"]
        if promote:
            self.fields.append("Recommends")
        if len(promote) == 2:
            self.fields.append("Suggests")

        self.restrict = None
        if parens:
            m = re.match(r"([<>=]+)\s+([\w\~\-\.\+\:]+)$", parens)
            if not m:
                raise Error(f"illegal dependency restriction ({parens})")

            relation, version = m.groups()
            self.restrict = Dependency.Restrict(relation, version)

    def __str__(self) -> str:
        if not self.restrict:
            return self.name

        return f"{self.name} ({self.restrict})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, Dependency):
            return self.name == other.name
        raise TypeError(
            "don't know how to check equality between Dependency and "
            f"{other!r} ({type(other)})"
        )

    def is_version_ok(self, version: str) -> bool:
        """compare package := name(relation)ver and version by relation"""
        if not self.restrict:
            return True

        return version in self.restrict


class PackageGetter:
    def __init__(self, dep_list: Iterable[Dependency], pool: Pool) -> None:
        logger.debug(
            f"initializing PackageGetter({list(map(str, dep_list))}, {pool})"
        )
        self._deps: dict[Dependency, str | None] = {}

        def format_dep(dep: Dependency) -> str:
            if not dep.restrict or dep.restrict.relation != "=":
                return dep.name
            return f"{dep.name}={dep.restrict.version}"

        dir = TemporaryDirectory("package_getter", "pool")
        pool.get(dir.name, list(map(format_dep, dep_list)))

        deps = {d.name: d for d in dep_list}
        for fname in os.listdir(dir.name):
            if not fname.endswith(".deb"):
                continue

            package_name = fname.split("_")[0]
            self._deps[deps[package_name]] = join(dir.name, fname)

        missing: set[Dependency] = set(deps.values()) - set(self._deps)
        for dep in missing:
            self._deps[dep] = None
        self.missing = missing
        self.dir = dir

    def __getitem__(self, key: Dependency) -> str | None:
        return self._deps[key]


class Plan:
    @staticmethod
    def _parse_plan_file(
        path: str, cpp_opts: list[tuple[str, str]] | None = None
    ) -> set[str]:
        """process plan through cpp, then parse it and add packages to plan"""
        if cpp_opts is None:
            cpp_opts = []
        processed_plan = cpp.cpp(path, cpp_opts)
        packages: set[str] = set()
        for expr in processed_plan.splitlines():
            expr = re.sub(r"#.*", "", expr)
            expr = expr.strip()
            if not expr:
                continue

            if expr.startswith("!"):
                package = expr[1:]

                if package in packages:
                    packages.remove(package)

            else:
                package = expr
                packages.add(package)

        return packages

    @classmethod
    def init_from_file(
        cls: type["Plan"],
        plan_file_path: str,
        cpp_opts: list[tuple[str, str]] | None = None,
        pool_path: str | None = None,
    ) -> "Plan":
        if cpp_opts is None:
            cpp_opts = []
        return cls(cls._parse_plan_file(plan_file_path, cpp_opts), pool_path)

    pool: Pool | None

    def __init__(
        self, iterable: Iterable[str] = (), pool_path: str | None = None
    ) -> None:
        self._plan: set[str] = set(iterable)

        if pool_path is not None:
            self.pool = Pool(pool_path)
        else:
            self.pool = None

        self.packageorigins = PackageOrigins()

    def __iter__(self) -> Iterator[str]:
        return iter(self._plan)

    def __ior__(self, other: Union["Plan", set[str]]) -> "Plan":
        if isinstance(other, Plan):
            self._plan |= other._plan
        else:
            self._plan |= other
        return self

    def add(self, v: str) -> None:
        self._plan.add(v)

    def _get_new_deps(
        self,
        pkg_control: deb822.Deb822,
        old_deps: set[Dependency],
        depend_fields: list[str],
    ) -> set[Dependency]:
        def parse_depends(val: str | None) -> list[str]:
            if val is None or val.strip() == "":
                return []

            return re.split(r"\s*,\s*", val.strip())

        new_deps = set()

        raw_depends: list[str] = []
        for field_name in depend_fields:
            raw_depends += parse_depends(pkg_control.get(field_name))

        for raw_depend in raw_depends:
            if "|" not in raw_depend:
                new_deps.add(Dependency(raw_depend))
                continue

            alternatives = [Dependency(alt) for alt in raw_depend.split("|")]

            # continue if any of the alternatives are already in resolved or
            # unresolved sets
            if set(alternatives) & old_deps:
                continue

            # add the first alternative that exists in the pool to set of new
            # dependencies
            for alternative in alternatives:
                assert self.pool is not None
                if self.pool.kernel.exists(alternative.name):
                    new_deps.add(alternative)
                    break

        for dep in new_deps:
            v = pkg_control.get("Package")
            assert isinstance(v, str)
            self.packageorigins.add(dep.name, v)

        return new_deps

    @staticmethod
    def _get_provided(pkg_control: deb822.Deb822) -> set[str]:
        raw_provided = pkg_control.get("Provides")
        if raw_provided is None or raw_provided.strip() == "":
            return set()

        return set(re.split(r"\s*,\s*", raw_provided.strip()))

    def dctrls(self) -> dict[Dependency, deb822.Deb822]:
        """return plan dependencies control file info"""
        toquery = {Dependency(pkg) for pkg in self._plan}
        if self.pool is None:
            raise Error("attempt to use `None` pool value!")
        else:
            packages = PackageGetter(toquery, self.pool)

        dctrls = {}
        for dep in toquery:
            package_path = packages._deps[dep]
            if package_path is None:
                raise Error("could not find package", dep.name)
            dctrls[dep] = debfile.DebFile(package_path).control.debcontrol()
            dctrls[dep]["Filename"] = basename(package_path)

        return dctrls

    def resolve(self) -> tuple[Iterable[str], Iterable[str]]:
        """resolve plan dependencies recursively -> return spec"""
        logger.debug("resolve")

        spec = Spec()
        logger.debug("(unresolved=)" + repr(list(self)))

        if not self.pool:
            return list(self), []

        resolved: set[Dependency] = set()
        missing: set[Dependency] = set()
        provided: set[str] = set()

        def reformat2dep(pkg: str) -> str:
            if "=" not in pkg:
                return pkg

            name, version = pkg.split("=", 1)
            return f"{name} (= {version})"

        unresolved = {Dependency(reformat2dep(pkg)) for pkg in self}
        while unresolved:
            # get newest package versions of unresolved dependencies from the
            # pool and pray they don't conflict with our dependency
            # restrictions
            packages = PackageGetter(unresolved, self.pool)
            new_deps: set[Dependency] = set()
            for dep in unresolved:
                logger.debug(f"resolving dependency: {dep}")
                package_path = packages[dep]
                if not package_path:
                    continue

                pkg_control = debfile.DebFile(package_path).debcontrol()

                version = pkg_control["Version"]
                if not dep.is_version_ok(version):
                    raise Error(
                        f"dependency '{dep}' incompatible with newest pool"
                        f" version ({version})"
                    )
                spec.add(dep.name, version)
                resolved.add(dep)

                new_deps |= self._get_new_deps(
                    pkg_control, resolved | unresolved | new_deps, dep.fields
                )
                provided |= self._get_provided(pkg_control)

            unresolved = new_deps - resolved
            all_missing = set(map(str, (missing | packages.missing))) - provided

        if all_missing:

            def get_origins(dep: Dependency) -> Generator[str, None, None]:
                depname: str | None = dep.name
                # trace the package origins
                while depname is not None:
                    try:
                        depname = self.packageorigins[depname][0]
                        yield depname
                    except KeyError:
                        depname = None

            brokendeps = []
            for dep in missing:
                brokendeps.append(dep.name)

            logger.debug(
                f"could not find these packages in pool: {brokendeps!r}"
            )

            return spec, brokendeps

        return spec, []
