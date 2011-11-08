
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

class TempPackageDir(dict):
    def __new__(cls, dir):
        return dict.__new__(cls)
    
    def __init__(self, dir):
        for fname in os.listdir(dir):
            if not fname.endswith(".deb"):
                continue
            
            package_name = fname.split("_")[0]
            self[package_name] = join(dir, fname)

        self.dir = dir

    def __del__(self):
        shutil.rmtree(self.dir)

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

    @staticmethod
    def _handle_virtual_names(name):
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

    def __init__(self, string):
        """initialize Dependency from a control file formatted dependency
        e.g.,
            libgpmg1 (>= 1.19.6-1)
        """
        string = string.strip()

        m = re.match(r'([a-z0-9][a-z0-9\+\-\.]+)(?:\s+\((.*?)\))?$', string)
        if not m:
            raise Error("illegally formatted dependency (%s)" % string)

        self.name = self._handle_virtual_names(m.group(1))
        parens = m.group(2)

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

    def _get_new_deps(self, pkg_control, old_deps):
        def parse_depends(val):
            if val is None or val.strip() == "":
                return []

            return re.split("\s*,\s*", val.strip())

        new_deps = set()
        
        raw_depends = []
        for field_name in ('Pre-Depends', 'Depends'):
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

        return new_deps
    
    def resolve(self):
        """resolve plan dependencies recursively -> return spec"""
        spec = Spec()
        
        resolved = set()
        unresolved = set([ Dependency(pkg) for pkg in self ])

        while unresolved:
            # get newest package versions of unresolved dependencies from the pool
            # and pray they don't conflict with our dependency restrictions
            pkgdir = TempPackageDir(self.pool.get([ d.name for d in unresolved ]))
            
            new_deps = set()
            for dep in unresolved:
                pkg_control = debinfo.get_control_fields(pkgdir[dep.name])

                version = pkg_control['Version']
                if not dep.is_version_ok(version):
                    raise Error("dependency '%s' incompatible with newest pool version (%s)" % (dep, version))
                spec.add(dep.name, version)
                resolved.add(dep)
                
                new_deps |= self._get_new_deps(pkg_control, resolved | unresolved)

            unresolved = new_deps - resolved
            
        return spec
