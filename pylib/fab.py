
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

class Handled:
    def __init__(self):
        self.handled=[]
    
    def add(self, name, version):
        self.handled.append([name, version])
        
    def exists(self, name, version=None):
        for h in self.handled:
            if version:
                if h[0] == name and h[1] == version:
                    return True
            elif h[0] == name:
                return True
        return False
    
    def print_spec(self, output=None):
        for h in self.handled:
            spec = h[0] + "=" + h[1]
            if output:
                open(output, "a").write(spec + "\n")
            else:
                print spec
                

class Plan:
    def __init__(self, pool):
        self.tmpdir = os.getenv('FAB_TMPDIR')
        if not self.tmpdir:
            self.tmpdir = "/var/tmp/fab"

        if not isabs(pool):
            poolpath = os.getenv('FAB_POOL_PATH')
            if poolpath:
                pool = join(poolpath, pool)
        os.environ['POOL_DIR'] = pool
            
        self.handled = Handled()
    
    def get_package(self, package):
        #TODO: replace quiet with strict once provides/virtual supported
        system("/turnkey/projects/pool/pool-get --quiet %s %s" % (self.tmpdir, package))
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
        if not self.handled.exists(name):
            package_path = self.get_package(name)

            control = apt_inst.debExtractControl(open(package_path))
            package = apt_pkg.ParseSection(control)

            self.handled.add(name, package['Version'])
            if package.has_key('Depends'):
                for dep in apt_pkg.ParseDepends(package['Depends']):
                    print "Sub-Processing: " + dep[0][0]
                    #TODO: depends on version
                    #TODO: provides/virtual
                    if (dep[0][0] == "perlapi-5.8.7" or
                        dep[0][0] == "perlapi-5.8.8"):
                        continue
                    self.get_package_spec(dep[0][0])
    
    def resolve(self, plan, output=None):
        for name in plan:
            print "Processing: " + name
            self.get_package_spec(name)
            
        self.handled.print_spec(output)
        
        
