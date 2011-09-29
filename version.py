import os
from os.path import *
import commands

def get_version():
    install_path = dirname(__file__)
    version_file = join(install_path, "version.txt")
    
    if lexists(version_file):
        return file(version_file).readline().strip()

    orig_cwd = os.getcwd()

    os.chdir(install_path)
    status, output = commands.getstatusoutput("autoversion HEAD")
    os.chdir(orig_cwd)
    
    if status != 0:
        return "?"

    return output
