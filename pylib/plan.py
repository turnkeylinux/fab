
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

class _PackagesTempDir(dict):
    def __new__(cls, dir):
        return dict.__new__(cls)
    
    def __init__(self, dir):
        for fname in os.listdir(dir):
            try:
                package_name = deb.parse_filename(fname)[0]
                self[package_name] = join(dir, fname)
            except deb.Error:
                continue

        self.dir = dir

    def __del__(self):
        shutil.rmtree(self.dir)

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
        """resolve plan dependencies recursively -> return spec"""
        spec = Spec()
        
        resolved = set()
        unresolved = self.copy()

        while unresolved:
            pkgs_tmpdir = _PackagesTempDir(self.pool.get(unresolved))
            
            depends = set()
            for pkg in unresolved:
                name = pkg
                for relation in ('>=', '>>', '<=', '<<', '='):
                    if relation in pkg:
                        name = pkg.split(relation)[0]
                        break

                version = deb.get_version(pkgs_tmpdir[name])

                if not deb.checkversion(pkg, version):
                    raise Error("dependency version error", pkg, version)

                spec.add(name, version)

                resolved.add(pkg)
                resolved.add(name)
                resolved.add(name + "=" + version)

                depends |= deb.get_depends(pkgs_tmpdir[name], self.pool)

            unresolved = depends - resolved
            
        return spec
