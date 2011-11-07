
import re
import os
import shutil
from os.path import *

import cpp
import debinfo
import debversion
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
                package_name = parse_filename(fname)[0]
                self[package_name] = join(dir, fname)
            except Error:
                continue

        self.dir = dir

    def __del__(self):
        shutil.rmtree(self.dir)

def get_version(package_path):
    """return package version"""
    control = debinfo.get_control_fields(package_path)
    return control['Version']

def parse_filename(filename):
    if not filename.endswith(".deb"):
        raise Error("not a package `%s'" % filename)

    return filename.split("_")[:2]

def checkversion(package, version):
    """compare package := name(relation)ver and version by relation"""
    relations = {'<<': [-1],
                 '<=': [-1,0],
                 '=':  [0],
                 '>=': [0,1],
                 '>>': [1]
                }

    #gotcha: can't use relations.keys() due to ordering
    for relation in ('>=', '>>', '<=', '<<', '='):
        if relation in package:
            name, ver = package.split(relation)
            if debversion.compare(version, ver) in relations[relation]:
                return True

            return False

    return True

def parse_depends(content):
    """content := array (eg. stuff.split(','))"""
    depends = []
    for d in content:
        m = re.match("(.*) \((.*) (.*)\)", d.strip())
        if m:
            depends.append((m.group(1), m.group(3), m.group(2)))
        else:
            depends.append((d.strip(), '', ''))
    
    return depends
    
def parse_name(name):
    #TODO: solve the provides/virtual issue properly
    virtuals = {'awk':                       'mawk',
                'perl5':                     'perl',
                'perlapi-5.8.7':             'perl-base',
                'perlapi-5.8.8':             'perl-base',
                'mail-transport-agent':      'postfix',
                'libapt-pkg-libc6.4-6-3.53': 'apt',
                'libapt-inst-libc6.4-6-1.1': 'apt-utils',
                'aufs-modules':              'aufs-modules-2.6.20-15-386'
               }

    if name in virtuals:
        return virtuals[name]
    
    return name

def get_depends(package_path, pool):
    """return package dependencies"""
    deps = set()
    control = debinfo.get_control_fields(package_path)

    if control.has_key('Depends'):
        for depend in parse_depends(control['Depends'].split(",")):
            if "|" in depend[0]:
                for d in parse_depends(depend[0].split("|")):
                    depname = parse_name(d[0])
                    dep = depname + d[2] + d[1]

                    # gotcha: if package exists, but not the specified version
                    # an error will be raised in checkversion
                    if pool.exists(depname):
                        break
            else:
                depname = parse_name(depend[0])
                dep = depname + depend[2] + depend[1]

            deps.add(dep)

    return deps

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

                version = get_version(pkgs_tmpdir[name])

                if not checkversion(pkg, version):
                    raise Error("dependency version error", pkg, version)

                spec.add(name, version)

                resolved.add(pkg)
                resolved.add(name)
                resolved.add(name + "=" + version)

                depends |= get_depends(pkgs_tmpdir[name], self.pool)

            unresolved = depends - resolved
            
        return spec
