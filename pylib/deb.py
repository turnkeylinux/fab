import os
import re
import md5

import debinfo
import debversion

class Error(Exception):
    pass

def checkversion(package, version):
    """compare package := name(relation)ver and version by relation"""
    relations = {'<<': [-1],
                 '<=': [-1,0],
                 '=':  [0],
                 '>=': [0,1],
                 '>>': [1]
                }

    #gotcha: can't use relations.keys() due to ordering
    for relation in ('>=', '>>', '<=', '<<', '='):
        if relation in package:
            name, ver = package.split(relation)
            if debversion.compare(version, ver) in relations[relation]:
                return True

            raise Error("dependency version error: ", package, version)

def get_version(package_path):
    """return version of package"""
    control = debinfo.get_control_fields(package_path)
    return control['Version']

def info(path, pool):
    deps = set()
    control_fields = debinfo.get_control_fields(path)

    if control_fields.has_key('Depends'):
        for depend in parse_depends(control_fields['Depends'].split(",")):
            if "|" in depend[0]:
                for d in parse_depends(depend[0].split("|")):
                    depname = parse_name(d[0])
                    dep = depname + d[2] + d[1]

                    # gotcha: if package exists, but not the specified version
                    # an error will be raised in checkversion
                    if pool.exists(depname):
                        break
            else:
                depname = parse_name(depend[0])
                dep = depname + depend[2] + depend[1]

            deps.add(dep)

    return deps

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

    return filename.split("_")[:2]

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

def prioritize_packages(packagedir):
    HIGH_PRIORITY = ('linux-image')
    
    high = []
    regular = []
    
    for filename in os.listdir(packagedir):
        try:
            name = parse_filename(filename)[0]
        except:
            continue
        
        if name in HIGH_PRIORITY:
            high.append(name)
        else:
            regular.append(name)
    
    return high, regular

def get_package_index(packagedir):
    def filesize(path):
        return str(os.stat(path).st_size)

    def md5sum(path):
        return str(md5.md5(open(path, 'rb').read()).hexdigest())

    index = []
    for package in os.listdir(packagedir):
        path = os.path.join(packagedir, package)
        if path.endswith('.deb'):
            control = debinfo.get_control_fields(path)
            for field in control.keys():
                index.append(field + ": " + control[field])

            index.append("Filename: " + path)
            index.append("Size: " + filesize(path))
            index.append("MD5sum: " + md5sum(path))
            index.append("")

    return index

