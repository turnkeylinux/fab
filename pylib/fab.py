
import os
import apt_pkg
import apt_inst
from os.path import *

from utils import *


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
   
    else:
        return name
        
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
                if name in p:
                    return True
        return False

    def print_spec(self, spec):
        if self.output:
            open(self.output, "a").write(spec + "\n")
        else:
            print spec
    
    def print_specs(self):
        for p in self.packages:
            self.print_spec(p)
    

class Packages:
    def __init__(self, pool, spec, outdir=None):
        self.tmpdir = os.getenv('FAB_TMPDIR')
        if not self.tmpdir:
            self.tmpdir = "/var/tmp/fab"

        if outdir:
            self.outdir = outdir
        else:
            self.outdir = self.tmpdir

        for dir in [self.outdir, self.tmpdir]:
            if not isdir(dir):
                mkdir_parents(dir)
                
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
        umount('devpts-chroot')
        umount('proc-chroot')

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

    def system_chroot(self, command):
        env = "/usr/bin/env -i HOME=/root TERM=${TERM} LC_ALL=C " \
              "PATH=/usr/sbin:/usr/bin:/sbin:/bin DEBIAN_PRIORITY=critical"
        
        system("chroot %s %s %s" % (self.path, env, command))

    def install_packagedir(self, dir):
        self._insert_fakestartstop()
        self.system_chroot("dpkg --install --recursive " + dir)
        self._remove_fakestartstop()

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

    pkgdir = "fab"
    chroot_path = realpath(chroot_path)
    pkgdir_path = join(chroot_path, pkgdir)
    
    p = Packages(pool, spec, pkgdir_path)
    p.get_all_packages()

    c = Chroot(chroot_path)
    c.mountpoints()
    c.install_packagedir(pkgdir)
    c.umountpoints()

    #system("rm -rf " + pkgdir_path)


