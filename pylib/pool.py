
import os
import shutil
from os.path import *

import executil
from common import get_tmpdir, mkdir

class Error(Exception):
    pass

def chdir(method):
    def wrapper(self, *args, **kws):
        orig_cwd = os.getcwd()
        os.chdir(self.path)

        try:
            ret = method(self, *args, **kws)
        finally:
            os.chdir(orig_cwd)

        return ret

    return wrapper

class Pool:
    def __init__(self, path=None):
        if path is None:
            path = os.environ.get('FAB_POOL_PATH')
            if path is None:
                raise Error('FAB_POOL_PATH not set in environment')

        self.path = realpath(path)
        if not isdir(join(self.path, ".pool")):
            raise Error("pool does not exist", path)

    @chdir
    def get(self, packages, outdir=None, strict=True):
        """get packages (iterable object) from pool, return output dir"""
        if outdir is None:
            outdir = get_tmpdir()

        mkdir(outdir)

        command = "pool-get --quiet "
        if strict:
            command += " --strict"
            
        executil.system(command, outdir, *packages)
        return outdir

    @chdir
    def exists(self, package):
        try:
            executil.getoutput("pool-exists", package)
        except executil.ExecError:
            return False

        return True


