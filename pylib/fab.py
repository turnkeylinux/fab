
import re
import os
import shutil
from os.path import *

import cpp
import deb
import executil
from pool import Pool
from common import *

from cli_common import warn # what is cli code doing in fab?

class Spec(dict):
    """class for holding a spec"""
    
    def add(self, name, version):
        """add package name and version to spec"""
        self.__setitem__(name, version)

    def list(self, sep="="):
        """return list of packages, as name(sep)version"""
        packages = []
        for item in self.items():
            packages.append(item[0] + sep + item[1])
        
        return packages

    exists = dict.has_key

class Plan:
    def __init__(self, pool_path):
        self.pool = Pool(pool_path)
        self.packages = set()
    
    @staticmethod
    def _parse_package_dir(package_dir):
        """return dict of packages: key=pkgname, value=pkgpath"""
        package_paths = {}

        for filename in os.listdir(package_dir):
            if filename.endswith(".deb"):
                name = deb.parse_filename(filename)[0]
                package_paths[name] = join(package_dir, filename)

        return package_paths

    @staticmethod
    def _parse_processed_plan(processed_plan):
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

    def add(self, package):
        """add package to plan"""
        self.packages.add(package)

    def remove(self, package):
        """remove package from plan """
        self.packages.remove(package)

    def process(self, plan_path, cpp_opts):
        """process plan through cpp, then parse it and add packages to plan """
        processed_plan = cpp.cpp(plan_path, cpp_opts)
        packages = self._parse_processed_plan(processed_plan)
        
        for package in packages:
            self.packages.add(package)

    def resolve_to_spec(self):
        """resolve plan and its dependencies recursively, return spec"""
        spec = Spec()
        
        resolved = set()
        toresolve = self.packages.copy()

        while toresolve:
            package_dir = self.pool.get(toresolve)
            package_paths = self._parse_package_dir(package_dir)
            
            depends = set()
            for pkg in toresolve:
                name = pkg
                for relation in ('>=', '>>', '<=', '<<', '='):
                    if relation in pkg:
                        name = pkg.split(relation)[0]
                        break

                version, deps = deb.info(package_paths[name], self.pool)
                deb.checkversion(pkg, version)  # raise error on mismatch
                spec.add(name, version)

                resolved.add(pkg)
                resolved.add(name)
                resolved.add(name + "=" + version)

                depends.update(deps)

            toresolve = depends
            toresolve.difference_update(resolved)
            
            shutil.rmtree(package_dir)
        
        return spec
        
def chroot_execute(chroot_path, command, mountpoints=False, get_stdout=False):
    c = Chroot(chroot_path)
    if mountpoints:
        c.mountpoints()
    
    out = c.system_chroot(command, get_stdout)

    if mountpoints:
        c.umountpoints()

    return out

def apply_removelist(rmlist, srcpath, dstpath=None):
    def _move(entry, srcpath, dstpath):
        entry = re.sub("^/","", entry)
        src = join(srcpath, entry)
        dst = join(dstpath, dirname(entry))
    
        if exists(src):
            mkdir(dst)
            if isdir(src):
                executil.system("mv -f %s/* %s/" % (dirname(src), dst))
            else:
                executil.system("mv -f %s %s/" % (src, dst))
        else:
            warn("entry does not exist: " + entry)

    if not dstpath:
        dstpath = get_tmpdir()

    # move entries out of srcpath
    for entry in rmlist['yes']:
        _move(entry, srcpath, dstpath)

    # move entries back into srcpath
    for entry in rmlist['no']:
        _move(entry, dstpath, srcpath)

def apply_overlay(overlay, dstpath, preserve=False):
    opts = "-dR"
    if preserve:
        opts += "p"
    executil.system("cp %s %s/* %s/" % (opts, overlay, dstpath))


