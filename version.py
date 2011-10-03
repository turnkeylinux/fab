import os
from os.path import *
import commands

class ExecError(Exception):
    pass

def _getoutput(command):
    status, output = commands.getstatusoutput(command)
    if status != 0:
        raise ExecError()
    return output
    
def get_version():
    install_path = dirname(abspath(__file__))
    version_file = join(install_path, "version.txt")
    
    if lexists(version_file):
        return file(version_file).readline().strip()

    orig_cwd = os.getcwd()

    os.chdir(install_path)
    try:
        if not exists("debian/changelog"):
            output = _getoutput("autoversion HEAD")
            version = output
        else:
            output = _getoutput("dpkg-parsechangelog")
            version = [ line.split(" ")[1]
                        for line in output.split("\n")
                        if line.startswith("Version:") ][0]
    except ExecError:
        os.chdir(orig_cwd)
        return "?"
        
    os.chdir(orig_cwd)
    return version

def test():
    print get_version()

if __name__ == "__main__":
    test()
