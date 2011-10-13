
import re
import os
import tempfile
from os.path import *

import deb
from cli_common import warn # what is cli code doing in fab?
import executil

import subprocess

def mkdir(path):
    path = str(path)
    if not exists(path):
        os.makedirs(path)

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

def get_tmpdir():
    """return unique temporary directory path"""
    tmpdir = os.environ.get('FAB_TMPDIR', '/var/tmp')
    mkdir(tmpdir)
    return tempfile.mkdtemp(prefix="fab", dir=tmpdir)

def system_pipe(command, pipein, quiet=False):
    if quiet:
        p = subprocess.Popen(command,
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             #stderr = subprocess.PIPE,
                             close_fds = True)
    else:
        p = subprocess.Popen(command,
                             stdin = subprocess.PIPE,
                             close_fds = True)
        
    out, err =  p.communicate(pipein)
    if p.returncode != 0:
        raise Error("failed command: " + " ".join(command))
    
    return out, err

class Error(Exception):
    pass

class PackagesSpec:
    """class for creating and controlling a packages spec
       package:
           key: name
           value: name=version
    """
    
    def __init__(self, output=None):
        self.packages = {}
        self.output = output
    
    def add(self, name, version):
        """add package name=version to spec"""
        package = name + "=" + version
        self.packages[name] = package
    
    def get(self):
        return self.packages.values()
    
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
                try:
                    name, version = entry.split("=")
                except ValueError:
                    name = entry
                self.packages[name] = entry
            
    def exists(self, name):
        """return True if package `name' exists in spec"""
        if name in self.packages.keys():
            return True
        
        return False

    def print_spec(self):
        """print spec to stdout (and output file if specified"""
        spec = "\n".join(self.packages.values())
        print spec

        if self.output:
            open(self.output, "w").write(spec)
        
class Packages:
    """class for getting packages from pool according to a spec"""
    def __init__(self, pool, spec, outdir=None):
        if outdir:
            self.outdir = outdir
        else:
            self.outdir = get_tmpdir()

        if not isabs(pool):
            poolpath = os.getenv('FAB_POOL_PATH')
            if poolpath:
                pool = join(poolpath, pool)
        
        if isdir(join(pool, ".pool")):
            os.environ['POOL_DIR'] = pool
        else:
            raise Error("pool does not exist" + pool)
        
        self.spec = spec
        self.packages = {}

    def get_packages(self, packages):
        """get list of packages from pool"""
        if not isdir(self.outdir):
            mkdir(self.outdir)

        toget = []
        for pkg in packages:
            name = pkg
            for relation in ('>>', '>=', '<=', '<<'):
                if relation in pkg:
                    name, version = pkg.split(relation)
                    break

            toget.append(name)

        cmd = ["pool-get", "--strict", "-i-", self.outdir]
        out, err = system_pipe(cmd, "\n".join(toget))
        if err:
            raise Error("error: " + err, cmd, out)

    def _read_packages(self):
        """get paths of all packages in outdir, update packages dictionary
           package:
               key: name
               value: path
        """
        for filename in os.listdir(self.outdir):
            filepath = join(self.outdir, filename)
            
            if isfile(filepath) and filename.endswith(".deb"):
                pkgname, pkgver = deb.parse_filename(filename)
                self.packages[pkgname] = filepath

    def resolve_plan(self, plan):
        """resolve plan and its dependencies recursively, update spec"""
        resolved = set()
        toresolve = plan
        while toresolve:
            self.outdir = get_tmpdir()
            self.get_packages(toresolve)
            self._read_packages()
            depends = set()
            for pkg in toresolve:
                name = pkg
                for relation in ('>=', '>>', '<=', '<<', '='):
                    if relation in pkg:
                        name, v = pkg.split(relation)
                        break

                ver, deps = deb.info(self.packages[name])
                deb.checkversion(pkg, ver)
                self.spec.add(name, ver)

                resolved.add(pkg)
                resolved.add(name)
                resolved.add(name + "=" + ver)

                depends.update(deps)

            toresolve = depends
            toresolve.difference_update(resolved)

    def get_spec_packages(self):
        """get packages according to spec"""
        self.get_packages(self.spec.get())


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
        env = "/usr/bin/env -i HOME=/root TERM=${TERM} LC_ALL=C " \
              "PATH=/usr/sbin:/usr/bin:/sbin:/bin " \
              "DEBIAN_FRONTEND=noninteractive " \
              "DEBIAN_PRIORITY=critical"
        
        cmd = "chroot %s %s %s" % (self.path, env, command)
        if get_stdout:
            try:
                return executil.getoutput(cmd)
            except executil.ExecError, e:
                return e.output

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
        
def plan_resolve(pool, plan, output):
    spec = PackagesSpec(output)
    p = Packages(pool, spec)
    
    p.resolve_plan(plan)
    p.spec.print_spec()

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


