import os
import re
from utils import getoutput, getstatus

class Error(Exception):
    pass

def _package_exists(package):
    """return True if package exists in the pool"""
    if not os.getenv('POOL_DIR'):
        raise Error("POOL_DIR not set")
    err = getstatus("pool-exists " + package)
    if err:
        return False
    
    return True

def extract_control(path):
    return getoutput("ar -p %s control.tar.gz | zcat | tar -O -xf - ./control 2>/dev/null" % path)

def parse_control(content):
    return dict([ re.split("\s*:\s+", line, 1)
        for line in content.split("\n")
            if not line.startswith(" ") ])

def info(path):
    deps = set()
    
    control = extract_control(path)
    package = parse_control(control)

    ver = package['Version']
    if package.has_key('Depends'):
        for depend in parse_depends(package['Depends'].split(",")):
            #eg. ('initramfs-tools', '0.40ubuntu11', '>=')
            #TODO: depends on version
            if "|" in depend[0]:
                for d in parse_depends(depend[0].split("|")):
                    depname = parse_name(d[0])
                    if _package_exists(depname):
                        break
            else:
                depname = parse_name(depend[0])
            
            deps.add(depname)
    
    return ver, deps

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
    
def parse_filename(filename):
    if not filename.endswith(".deb"):
        raise Error("not a package `%s'" % filename)

    name, version = filename.split("_")[:2]

    return name, version

def parse_name(name):
    #TODO: solve the provides/virtual issue properly
    virtuals = {'awk':                       'mawk',
                'perl5':                     'perl',
                'perlapi-5.8.7':             'perl-base',
                'perlapi-5.8.8':             'perl-base',
                'mail-transport-agent':      'postfix',
                'libapt-pkg-libc6.4-6-3.53': 'apt',
                'aufs-modules':              'aufs-modules-2.6.20-15-386'
               }

    if name in virtuals:
        return virtuals[name]
    
    return name

def is_preinstall(name):
    if name.startswith("linux-image"):
        return True
    
    return False
