
import re
import os
import shutil
from os.path import *

import cpp
import deb
import executil
from pool import Pool

class Error(Exception):
    pass

class Spec(dict):
    """class for holding a spec"""
    
    def add(self, name, version):
        """add package name and version to spec"""
        self[name] = version

    def remove(self, name):
        del self[name]

    def __iter__(self):
        """return list of packages, as name(sep)version"""
        for name, version in self.items():
            yield "%s=%s" % (name, version)

    def __str__(self):
        return "\n".join(list(self))
        
    exists = dict.has_key

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

    def resolve(self):
        """resolve plan and its dependencies recursively -> return spec"""
        spec = Spec()
        
        resolved = set()
        unresolved = self.copy()

        def _parse_package_dir(package_dir):
            """return dict of packages: key=pkgname, value=pkgpath"""
            package_paths = {}

            for filename in os.listdir(package_dir):
                if filename.endswith(".deb"):
                    name = deb.parse_filename(filename)[0]
                    package_paths[name] = join(package_dir, filename)

            return package_paths

        while unresolved:
            package_dir = self.pool.get(unresolved)
            package_paths = _parse_package_dir(package_dir)
            
            depends = set()
            for pkg in unresolved:
                name = pkg
                for relation in ('>=', '>>', '<=', '<<', '='):
                    if relation in pkg:
                        name = pkg.split(relation)[0]
                        break

                version = deb.get_version(package_paths[name])
                deps = deb.get_depends(package_paths[name], self.pool)

                if not deb.checkversion(pkg, version):
                    raise Error("dependency version error", pkg, version)

                spec.add(name, version)

                resolved.add(pkg)
                resolved.add(name)
                resolved.add(name + "=" + version)

                depends.update(deps)

            unresolved = depends
            unresolved.difference_update(resolved)
            
            shutil.rmtree(package_dir)
        
        return spec
