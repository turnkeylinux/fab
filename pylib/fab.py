
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


def is_mounted(dir):
    mounts = file("/proc/mounts").read()
    if mounts.find(dir) != -1:
        return True
    return False

def mount(device, mountp, options=None):
    if not is_mounted(device):
        print "mounting: " + device
        if options:
            executil.system("mount", device, mountp, options)
        else:
            executil.system("mount", device, mountp)

def umount(device):
    if is_mounted(device):
        print "umounting: " + device
        executil.system("umount", "-f", device)

class Error(Exception):
    pass

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
        
class Chroot:
    """class for interacting with a fab chroot"""
    def __init__(self, path):
        if os.getuid() != 0:
            raise Error("root privileges required for chroot")

        self.path = path
    
    def mountpoints(self):
        """mount proc and dev/pts into chroot"""
        mount('proc-chroot',   join(self.path, 'proc'),    '-tproc')
        mount('devpts-chroot', join(self.path, 'dev/pts'), '-tdevpts')

    def umountpoints(self):
        """umount proc and dev/pts from chroot"""
        umount(join(self.path, 'dev/pts'))
        umount(join(self.path, 'proc'))

    def system_chroot(self, command, get_stdout=False):
        """execute system command in chroot"""
        args = ['/usr/bin/env', '-i', 'HOME=/root', 'TERM=${TERM}', 'LC_ALL=C',
                'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                'DEBIAN_FRONTEND=noninteractive',
                'DEBIAN_PRIORITY=critical']
        command = " ".join(args) + " " + command
        chroot_args = (self.path, 'sh', '-c', command)

        if get_stdout:
            return executil.getoutput("chroot", *chroot_args)
        else:
            executil.system("chroot", *chroot_args)

    def _insert_fakestartstop(self):
        """insert fake start-stop-daemon into chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        if isfile('%s.REAL' % daemon): #already created
            return
        
        executil.system("mv %s %s.REAL" % (daemon, daemon))
        
        fake = "#!/bin/sh\n" \
               "echo\n" \
               "echo \"Warning: Fake start-stop-daemon called, doing nothing\"\n"
        
        open(daemon, "w").write(fake)
        os.chmod(daemon, 0755)

    def _remove_fakestartstop(self):
        """remove fake start-stop daemon from chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        executil.system("mv %s.REAL %s" % (daemon, daemon))

    def _apt_indexpath(self):
        """return package index path"""
        return join(self.path,
                    "var/lib/apt/lists",
                    "_dists_local_debs_binary-i386_Packages")

    def _apt_sourcelist(self):
        """configure apt for local index generation and package installation"""
        source = "deb file:/// local debs"
        path = join(self.path, "etc/apt/sources.list")
        file(path, "w").write(source)
    
    def _apt_refresh(self, pkgdir_path):
        """generate index cache of packages in pkgdir_path"""
        self._apt_sourcelist()       
        
        print "generating package index..."
        executil.system("apt-ftparchive packages %s > %s" % (pkgdir_path, 
                                                    self._apt_indexpath()))
        self.system_chroot("apt-cache gencaches")
        
    def apt_install(self, pkgdir_path):
        """install pkgdir_path/*.deb packages into chroot"""
        self._apt_refresh(pkgdir_path)
        
        pkgnames = []
        pre_pkgnames = []
        for filename in os.listdir(pkgdir_path):
            if filename.endswith(".deb"):
                name, version = filename.split("_")[:2]
                if deb.is_preinstall(name):
                    pre_pkgnames.append(name)
                else:
                    pkgnames.append(name)
        
        self._insert_fakestartstop()
        
        for pkglist in [pre_pkgnames, pkgnames]:
            pkglist.sort()
            self.system_chroot("apt-get install -y --allow-unauthenticated %s" %
                               " ".join(pkglist))

        self._remove_fakestartstop()

    def apt_clean(self):
        """clean apt cache in chroot"""
        self.system_chroot("apt-get clean")
        executil.system("rm -f " + self._apt_indexpath())


def spec_get(pool_path, spec_fh, outdir):
    if isfile(spec_fh):
        spec_lines = open(spec_fh, "r").readlines()
    else:
        spec_lines = spec_fh.splitlines()

    packages = set()
    for package in spec_lines:
        packages.add(package)

    pool = Pool(pool_path)
    pool.get(packages, outdir)

def spec_install(pool, spec_fh, chroot_path):
    chroot_path = realpath(chroot_path)
    pkgdir_path = join(chroot_path, "var/cache/apt/archives")

    spec_get(pool, spec_fh, pkgdir_path)

    c = Chroot(chroot_path)
    c.mountpoints()
    c.apt_install(pkgdir_path)
    c.apt_clean()
    c.umountpoints()

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


