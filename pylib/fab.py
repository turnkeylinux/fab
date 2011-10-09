
import re
import os
from os.path import *
from datetime import datetime

import deb
from utils import *

def get_datetime():
    """return unique string created by current data and time"""
    return datetime.now().strftime("%Y%m%d.%H%M%S")

def get_tmpdir():
    """return unique temporary directory path"""
    tmpdir = os.getenv('FAB_TMPDIR')
    if not tmpdir:
        tmpdir = "/var/tmp"

    tmpdir = join(tmpdir, "fab-" + get_datetime())
    return realpath(tmpdir)

def rm_epoch(package):
    if ":" in package:
        name, version = package.split("=")
        version = re.sub('.:', '', version)
        package = name + "=" + version

    return package

class PackagesSpec:
    """class for creating and controlling a packages spec"""
    def __init__(self, output=None):
        self.packages = set()
        self.output = output
    
    def add(self, name, version, quiet=True):
        """add package name=version to spec"""
        package = name + "=" + version
        self.packages.add(package)
        if not quiet:
            self.print_package(package)
    
    def get(self):
        """return packages set"""
        return self.packages
    
    def getstr(self, delimeter="\n"):
        """return packages as delimeted string"""
        spec = ""
        for package in self.packages:
            spec += package + delimeter
        
        return spec.strip()
    
    def read(self, input):
        """add packages to spec from input
        input := file | string (packages seperated by newlines)
        """
        if isfile(input):
            entries = open(input, "r").readlines()
        else:
            entries = input.split("\n")
        
        for entry in entries:
            entry = re.sub(r'#.*', '', entry)
            entry = entry.strip()
            if entry:
                entry = rm_epoch(entry)
                self.packages.add(entry)
            
    def exists(self, name, version=None):
        """return True/False if package exists in spec"""
        if version:
            if name + "=" + version in self.packages:
                return True
        else:
            for p in self.packages:
                if p.startswith(name + "="):
                    return True
        return False

    def print_package(self, package):
        """print package to stdout and append to output file (if specified)"""
        if self.output:
            open(self.output, "a").write(package + "\n")
        
        print package
    
    def print_packages(self):
        """print all packages in the spec"""
        for p in self.packages:
            self.print_package(p)
    

class Packages:
    """class for getting packages from pool according to a spec"""
    def __init__(self, pool, spec, outdir=None):
        if outdir:
            self.outdir = outdir
        else:
            self.outdir = get_tmpdir()

        if not isdir(self.outdir):
            mkdir_parents(self.outdir)
        
        if not isabs(pool):
            poolpath = os.getenv('FAB_POOL_PATH')
            if poolpath:
                pool = join(poolpath, pool)
        
        if isdir(join(pool, ".pool")):
            os.environ['POOL_DIR'] = pool
        else:
            fatal("pool does not exist" + pool)
        
        self.spec = spec

    @staticmethod
    def _package_in_pool(package):
        """return True/False if package exists in the pool"""
        err = getstatus("pool-exists " + package)
        if err:
            return False
        
        return True

    def dump_all_packages(self):
        self.packages = {}
        system("pool-get %s" % self.outdir)
        for filename in os.listdir(self.outdir):
            filepath = join(self.outdir, filename)
            
            if isfile(filepath) and filename.endswith(".deb"):
                pkgname, pkgver = deb.parse_filename(filename)
                self.packages[pkgname] = filepath
        
    def get_spec_packages(self):
        cmd = ["pool-get", "--strict", "-i-", self.outdir]
        out, err = system_pipe(cmd, self.spec.getstr(delimeter="\n"))
        if err:
            raise Error("pool-get returned error: " + err, out)

    def resolve(self, name):
        """resolve package and its dependencies recursively, update spec"""
        name = deb.parse_name(name)
        if not self.spec.exists(name):
            if not self.packages.has_key(name):
                raise Error("package `%s' not available in dump" % name)
            
            control = deb.extract_control(self.packages[name])
            package = deb.parse_control(control)

            self.spec.add(name, package['Version'], quiet=False)
            if package.has_key('Depends'):
                for depend in deb.parse_depends(package['Depends']):
                    #eg. ('initramfs-tools', '0.40ubuntu11', '>=')
                    #TODO: depends on version
                    if "|" in depend[0]:
                        for d in deb.parse_depends(depend[0], "|"):
                            depname = deb.parse_name(d[0])
                            if self._package_in_pool(depname):
                                break
                    else:
                        depname = deb.parse_name(depend[0])
                    
                    self.resolve(depname)

class Chroot:
    """class for interacting with a fab chroot"""
    def __init__(self, path):
        if os.getuid() != 0:
            fatal("root privileges required for chroot")

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
        env = "/usr/bin/env -i HOME=/root TERM=${TERM} LC_ALL=C " \
              "PATH=/usr/sbin:/usr/bin:/sbin:/bin " \
              "DEBIAN_FRONTEND=noninteractive " \
              "DEBIAN_PRIORITY=critical"
        
        cmd = "chroot %s %s %s" % (self.path, env, command)
        if get_stdout:
            return getoutput(cmd)
        
        system(cmd)

    def _insert_fakestartstop(self):
        """insert fake start-stop-daemon into chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        if isfile('%s.REAL' % daemon): #already created
            return
        
        system("mv %s %s.REAL" % (daemon, daemon))
        
        fake = "#!/bin/sh\n" \
               "echo\n" \
               "echo \"Warning: Fake start-stop-daemon called, doing nothing\"\n"
        
        open(daemon, "w").write(fake)
        os.chmod(daemon, 0755)

    def _remove_fakestartstop(self):
        """remove fake start-stop daemon from chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        system("mv %s.REAL %s" % (daemon, daemon))

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
        system("apt-ftparchive packages %s > %s" % (pkgdir_path, 
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
        system("rm -f " + self._apt_indexpath())
        
def plan_resolve(pool, plan, output):
    spec = PackagesSpec(output)
    
    p = Packages(pool, spec)
    p.dump_all_packages()
    
    for name in plan:
        p.resolve(name)

def spec_get(pool, specinfo, outdir):
    spec = PackagesSpec()
    spec.read(specinfo)
    
    p = Packages(pool, spec, outdir)
    p.get_spec_packages()
    
def spec_install(pool, specinfo, chroot_path):
    chroot_path = realpath(chroot_path)
    pkgdir_path = join(chroot_path, "var/cache/apt/archives")
    
    spec_get(pool, specinfo, pkgdir_path)
    
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
            mkdir_parents(dst)
            if isdir(src):
                system("mv -f %s/* %s/" % (dirname(src), dst))
            else:
                system("mv -f %s %s/" % (src, dst))
        else:
            warning("entry does not exist: " + entry)

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
    system("cp %s %s/* %s/" % (opts, overlay, dstpath))


