from os.path import *
import commands

def get_version():
    install_path = dirname(__file__)
    version_file = join(install_path, "version.txt")
    
    if lexists(version_file):
        return file(version_file).readline().strip()

    version_script = join(install_path, "scripts", "version.sh")
    status, output = commands.getstatusoutput(version_script)
    if status != 0:
        return "?"

    return output.strip().split('\n')[0]

