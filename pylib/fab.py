
import os
import apt_pkg
import apt_inst
from os.path import *
from datetime import datetime

from utils import *

def get_datetime():
    return datetime.now().strftime("%Y%m%d.%H%M%S")

def get_tmpdir():
    tmpdir = os.getenv('FAB_TMPDIR')
    if not tmpdir:
        tmpdir = "/var/tmp"

    tmpdir = join(tmpdir, "fab-" + get_datetime())
    return realpath(tmpdir)
            
def parse_deb_filename(filename):
    """Parses package filename -> (name, version)"""

    if not filename.endswith(".deb"):
        raise Error("not a package `%s'" % filename)

    name, version = filename.split("_")[:2]

    return name, version

def parse_package_name(name):
    #TODO: solve the provides/virtual issue properly
    if (name == "perlapi-5.8.7" or
        name == "perlapi-5.8.8"):
        return "perl-base"
    
    elif (name == "perl5"):
        return "perl"

    elif (name == "aufs-modules"):
        return "aufs-modules-2.6.20-15-386"
    
    elif (name == "mail-transport-agent"):
        return "postfix"

    elif (name == "libapt-pkg-libc6.4-6-3.53"):
        return "apt"

    elif (name == "awk"):
        return "mawk"
    
    else:
        return name

def preinstall_package(name):
    if name.startswith("linux-image"):
        return True
    
    return False
    
class PackagesSpec:
    def __init__(self, output=None):
        self.packages = set()
        self.output = output
        
    def add(self, name, version, quiet=True):
        spec = name + "=" + version
        self.packages.add(spec)
        if not quiet:
            self.print_spec(spec)
    
    def get(self):
        return self.packages
    
    def read(self, input):
        if isfile(input):
            for line in open(input, "r").readlines():
                if line:
                    self.packages.add(line.strip())
        else:
            for line in input.split("\n"):
                if line:
                    self.packages.add(line.strip())
    
    def exists(self, name, version=None):
        if version:
            if name + "=" + version in self.packages:
                return True
        else:
            for p in self.packages:
                if p.startswith(name + "="):
                    return True
        return False

    def print_spec(self, spec):
        if self.output:
            open(self.output, "a").write(spec + "\n")
        
        print spec
    
    def print_specs(self):
        for p in self.packages:
            self.print_spec(p)
    

class Packages:
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
    def _package_exists(package):
        err = getstatus("pool-exists " + package)
        if err:
            return False
        
        return True

    @staticmethod
    def _get(package, outdir):
        if ":" in package:
            name, version = package.split("=")
            version = re.sub('.:', '', version)
            package = name + "=" + version
        system("pool-get --strict %s %s" % (outdir, package))
        
    def get_all_packages(self):
        for package in self.spec.get():
            print "getting: " + package
            self._get(package, self.outdir)
    
    def get_package(self, package):
        self._get(package, self.outdir)
        if "=" in package:
            name, version = package.split("=", 1)
        else:
            name = package
            version = None

        for filename in os.listdir(self.outdir):
            filepath = join(self.outdir, filename)

            if not isfile(filepath) or not filename.endswith(".deb"):
                continue

            cached_name, cached_version = parse_deb_filename(filename)
            if name == cached_name and (version is None or version == cached_version):
                return filepath

        return None

    def get_package_spec(self, name):
        name = parse_package_name(name)
        if not self.spec.exists(name):
            package_path = self.get_package(name)

            control = apt_inst.debExtractControl(open(package_path))
            package = apt_pkg.ParseSection(control)

            self.spec.add(name, package['Version'], quiet=False)
            if package.has_key('Depends'):
                for dep in apt_pkg.ParseDepends(package['Depends']):
                    # eg. [('initramfs-tools', '0.40ubuntu11', '>='),(...),
                    #TODO: depends on version
                    if len(dep) > 1:
                        for d in dep:
                            depname = parse_package_name(d[0])
                            if self._package_exists(depname):
                                break
                    else:
                        depname = parse_package_name(dep[0][0])
                    
                    self.get_package_spec(depname)

class Chroot:
    def __init__(self, path):
        if os.getuid() != 0:
            fatal("root privileges required for chroot")

        self.path = path
    
    def mountpoints(self):
        mount('proc-chroot',   '%s/proc'    % self.path, '-tproc')
        mount('devpts-chroot', '%s/dev/pts' % self.path, '-tdevpts')

    def umountpoints(self):
        umount(join(self.path, 'dev/pts'))
        umount(join(self.path, 'proc'))

    def system_chroot(self, command):
        env = "/usr/bin/env -i HOME=/root TERM=${TERM} LC_ALL=C " \
              "PATH=/usr/sbin:/usr/bin:/sbin:/bin DEBIAN_PRIORITY=critical"
        
        system("chroot %s %s %s" % (self.path, env, command))

    def _insert_fakestartstop(self):
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
        daemon = join(self.path, 'sbin/start-stop-daemon')
        system("mv %s.REAL %s" % (daemon, daemon))

    def _apt_indexpath(self):
        return join(self.path,
                    "var/lib/apt/lists",
                    "_dists_local_debs_binary-i386_Packages")

    def _apt_sourcelist(self):
        source = "deb file:/// local debs"
        path = join(self.path, "etc/apt/sources.list")
        file(path, "w").write(source)
    
    def _apt_refresh(self, pkgdir_path):
        self._apt_sourcelist()       
        
        print "generating package index..."
        system("apt-ftparchive packages %s > %s" % (pkgdir_path, 
                                                    self._apt_indexpath()))
        self.system_chroot("apt-cache gencaches")
        
    def apt_install(self, pkgdir_path):
        self._apt_refresh(pkgdir_path)
        
        pkgnames = []
        pre_pkgnames = []
        for filename in os.listdir(pkgdir_path):
            if filename.endswith(".deb"):
                name, version = filename.split("_")[:2]
                if preinstall_package(name):
                    pre_pkgnames.append(name)
                else:
                    pkgnames.append(name)
        
        self._insert_fakestartstop()
        
        for pkglist in [pre_pkgnames, pkgnames]:
            pkglist.sort()
            self.system_chroot("apt-get install -y --allow-unauthenticated %s" %
                               list2str(pkglist))
        
        self._remove_fakestartstop()
    
    def apt_clean(self):
        self.system_chroot("apt-get clean")
        system("rm -f " + self._apt_indexpath())
        
def plan_resolve(pool, plan, exclude, output):
    spec = PackagesSpec(output)
    if exclude:
        spec.read(exclude)
    
    p = Packages(pool, spec)
    for name in plan:
        p.get_package_spec(name)
    
def spec_install(pool, specinfo, chroot_path):
    spec = PackagesSpec()
    spec.read(specinfo)

    chroot_path = realpath(chroot_path)
    pkgdir_path = join(chroot_path, "var/cache/apt/archives")
    
    p = Packages(pool, spec, pkgdir_path)
    p.get_all_packages()
    
    c = Chroot(chroot_path)
    c.mountpoints()
    c.apt_install(pkgdir_path)
    c.apt_clean()
    c.umountpoints()

def chroot_execute(chroot_path, command, mountpoints=True):
    c = Chroot(chroot_path)
    if mountpoints:
        c.mountpoints()
    
    c.system_chroot(command)
    
    if mountpoints:
        c.umountpoints()

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

    """move entries out of srcpath"""
    for entry in rmlist['yes']:
        _move(entry, srcpath, dstpath)

    """move entries back into srcpath"""
    for entry in rmlist['no']:
        _move(entry, dstpath, srcpath)

def apply_overlay(overlay, dstpath):
    system("cp -a %s/* %s/" % (overlay, dstpath))


