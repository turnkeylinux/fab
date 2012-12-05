# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import re
import os
import shutil
from os.path import *

import cpp
import debinfo
import debversion
import executil
from pyproject.pool.pool import Pool

from temp import TempDir

class Error(Exception):
    pass

class PackageOrigins(dict):
    """class for holding package origins for dependency annotation """

    def add(self, name, origin):
        name = name.split("=")[0].strip("*")
        if not self.has_key(name):
            self[name] = []

        self[name].append(origin)

class Spec(dict):
    """class for holding a spec"""
    
    def add(self, name, version):
        """add package name and version to spec"""
        self[name] = version

    def remove(self, name):
        del self[name]

    def __iter__(self):
        """return list of packages, as name=version"""
        for name, version in self.items():
            yield "%s=%s" % (name, version)

    def __str__(self):
        return "\n".join(list(self))
        
    exists = dict.has_key

class PackageGetter(dict):
    def __new__(cls, deps, pool):
        return dict.__new__(cls)
    
    def __init__(self, deps, pool):
        def f(dep):
            if not dep.restrict or dep.restrict.relation != "=":
                return dep.name
            return "%s=%s" % (dep.name, dep.restrict.version)

        dir = TempDir()
        pool.get(dir.path, map(f, deps))
        
        deps = dict([ (d.name, d) for d in deps ])
        for fname in os.listdir(dir.path):
            if not fname.endswith(".deb"):
                continue
            
            package_name = fname.split("_")[0]
            self[deps[package_name]] = join(dir.path, fname)

        missing = set(deps) - set(self)
        for dep in missing:
            self[dep] = None
        self.missing = missing
        self.dir = dir

class Dependency:
    """This class represents a dependency.

    The restriction parameters are parsed and can be accessed
    as attributes but for now they are ignored when calculating equality.

    Whether two dependencies are equal depends only on the name.
    """
    class Restrict:
        RELATIONS = {'<<': (-1,),
                     '<=': (-1,0),
                     '=':  (0,),
                     '>=': (0,1),
                     '>>': (1,),
                     }

        def __init__(self, relation, version):
            if relation not in self.RELATIONS:
                raise Error("bad relation (%s)" % relation)

            self.relation = relation
            self.version = version

        def __hash__(self):
            return hash(self.relation) ^ hash(self.version)

        def __eq__(a, b):
            if b is None:
                return False
            
            return a.relation == b.relation and a.version == b.version

        def __contains__(self, version):
            true_results = self.RELATIONS[self.relation]

            if debversion.compare(version, self.version) in true_results:
                return True

            return False

        def __str__(self):
            return self.relation + " " + self.version

    def __init__(self, string):
        """initialize Dependency from a control file formatted dependency
        e.g.,
            libgpmg1 (>= 1.19.6-1)
        exception:
            package*  # promote recommends
            package** # promote recommends + suggests
        """
        string = string.strip()

        m = re.match(r'([a-z0-9][a-z0-9\+\-\.]+)([\*]{0,2})(?:\s+\((.*?)\))?$', string)
        if not m:
            raise Error("illegally formatted dependency (%s)" % string)

        self.name = m.group(1)
        promote = m.group(2)
        parens = m.group(3)

        self.fields = ['Pre-Depends', 'Depends']
        if promote:
            self.fields.append('Recommends')
        if len(promote) == 2:
            self.fields.append('Suggests')

        self.restrict = None
        if parens:
            m = re.match(r'([<>=]+)\s+([\w\~\-\.\+\:]+)$', parens)
            if not m:
                raise Error("illegal dependency restriction (%s)" % parens)

            relation, version = m.groups()
            self.restrict = Dependency.Restrict(relation, version)

    def __str__(self):
        if not self.restrict:
            return self.name
        
        return "%s (%s)" % (self.name, str(self.restrict))

    def __hash__(self):
        return hash(self.name)

    def __eq__(a, b):
        if type(b) == str:
            return a.name == b
        
        return a.name == b.name

    def is_version_ok(self, version):
        """compare package := name(relation)ver and version by relation"""
        if not self.restrict:
            return True

        return version in self.restrict

class Plan(set):
    @staticmethod
    def _parse_plan_file(path, cpp_opts=[]):
        """process plan through cpp, then parse it and add packages to plan """
        processed_plan = cpp.cpp(path, cpp_opts)
        packages = set()
        for expr in processed_plan.splitlines():
            expr = re.sub(r'#.*', '', expr)
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
    def init_from_file(cls, plan_file_path, cpp_opts=[], pool_path=None):
        return cls(cls._parse_plan_file(plan_file_path, cpp_opts), pool_path)

    def __new__(cls, iterable=(), pool_path=None):
        return set.__new__(cls, iterable)
    
    def __init__(self, iterable=(), pool_path=None):
        set.__init__(self, iterable)
        self.pool = Pool(pool_path)
        self.packageorigins = PackageOrigins()

    def _get_new_deps(self, pkg_control, old_deps, depend_fields):
        def parse_depends(val):
            if val is None or val.strip() == "":
                return []

            return re.split("\s*,\s*", val.strip())

        new_deps = set()
        
        raw_depends = []
        for field_name in depend_fields:
            raw_depends += parse_depends(pkg_control.get(field_name))

        for raw_depend in raw_depends:
            if "|" not in raw_depend:
                new_deps.add(Dependency(raw_depend))
                continue

            alternatives = [ Dependency(alt) for alt in raw_depend.split("|") ]

            # continue if any of the alternatives are already in resolved or unresolved sets
            if set(alternatives) & old_deps:
                continue

            # add the first alternative that exists in the pool to set of new dependencies
            for alternative in alternatives:
                if self.pool.exists(alternative.name):
                    new_deps.add(alternative)
                    break

        for dep in new_deps:
            self.packageorigins.add(dep.name, pkg_control.get('Package'))

        return new_deps
    
    @staticmethod
    def _get_provided(pkg_control):
        raw_provided = pkg_control.get('Provides')
        if raw_provided is None or raw_provided.strip() == "":
            return set()

        return set(re.split("\s*,\s*", raw_provided.strip()))

    def dctrls(self):
        """return plan dependencies control file info"""
        toquery = set([ Dependency(pkg) for pkg in self ])
        packages = PackageGetter(toquery, self.pool)

        dctrls = {}
        for dep in toquery:
            package_path = packages[dep]
            if package_path is None:
                raise Error('could not find package', dep.name)
            dctrls[dep] = debinfo.get_control_fields(package_path)
            dctrls[dep]['Filename'] = basename(package_path)

        return dctrls

    def resolve(self):
        """resolve plan dependencies recursively -> return spec"""
        spec = Spec()
        
        resolved = set()
        missing = set()
        provided = set()

        def reformat2dep(pkg):
            if '=' not in pkg:
                return pkg

            name, version = pkg.split("=", 1)
            return "%s (= %s)" % (name, version)

        unresolved = set([ Dependency(reformat2dep(pkg)) for pkg in self ])
        while unresolved:
            # get newest package versions of unresolved dependencies from the pool
            # and pray they don't conflict with our dependency restrictions
            packages = PackageGetter(unresolved, self.pool)
            new_deps = set()
            for dep in unresolved:
                package_path = packages[dep]
                if not package_path:
                    continue

                pkg_control = debinfo.get_control_fields(package_path)

                version = pkg_control['Version']
                if not dep.is_version_ok(version):
                    raise Error("dependency '%s' incompatible with newest pool version (%s)" % (dep, version))
                spec.add(dep.name, version)
                resolved.add(dep)

                new_deps |= self._get_new_deps(pkg_control, resolved | unresolved | new_deps, dep.fields)
                provided |= self._get_provided(pkg_control)

            unresolved = new_deps - resolved
            missing = (missing | packages.missing) - provided

        if missing:
            def get_origins(dep):
                # trace the package origins
                origins = []
                while dep:
                    try:
                        dep = self.packageorigins[dep][0]
                        origins.append(dep)
                    except KeyError:
                        dep = None

                return origins

            brokendeps = []
            for dep in missing:
                brokendeps.append("%s (%s)" % (dep, " -> ".join(get_origins(dep))))

            raise Error("broken dependencies: " + "\n".join(brokendeps))

        return spec
