
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
    
    def read(self, input):
        if isfile(input):
            for line in open(input, "r").readlines():
                self.packages.add(line.strip())
        else:
            for line in input.split("\n"):
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
    def __init__(self, pool, spec):
        self.tmpdir = os.getenv('FAB_TMPDIR')
        if not self.tmpdir:
            self.tmpdir = "/var/tmp/fab"

        if not isabs(pool):
            poolpath = os.getenv('FAB_POOL_PATH')
            if poolpath:
                pool = join(poolpath, pool)
        os.environ['POOL_DIR'] = pool
        
        self.spec = spec

    @staticmethod
    def _package_exists(package):
        err = getstatus("pool-exists " + package)
        if err:
            return False
        
        return True

    def get_package(self, package):
        system("pool-get --strict %s %s" % (self.tmpdir, package))
        if "=" in package:
            name, version = package.split("=", 1)
        else:
            name = package
            version = None

        for filename in os.listdir(self.tmpdir):
            filepath = join(self.tmpdir, filename)

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
    
def plan_resolve(pool, plan, exclude, output):
    rootspec = PackagesSpec(output)
    if exclude:
        rootspec.read(exclude)
    
    p = Packages(pool, rootspec)
    for name in plan:
        p.get_package_spec(name)
    
def spec_install(pool, spec, chroot):
    rootspec = PackagesSpec()
    rootspec.read(spec)
    
    print "installing this spec:"
    rootspec.print_specs()
    print "into this chroot: " + chroot
    p = Packages(pool, rootspec)
    print "using this pool: " + os.getenv('POOL_DIR')