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

            return False

    return True

def get_version(package_path):
    """return package version"""
    control = debinfo.get_control_fields(package_path)
    return control['Version']

def parse_filename(filename):
    if not filename.endswith(".deb"):
        raise Error("not a package `%s'" % filename)

    return filename.split("_")[:2]

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

