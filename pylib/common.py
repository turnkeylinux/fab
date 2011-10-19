
import os
import tempfile

def mkdir(path):
    path = str(path)
    if not os.path.exists(path):
        os.makedirs(path)

def get_tmpdir():
    """return unique temporary directory path"""
    tmpdir = os.environ.get('FAB_TMPDIR', '/var/tmp')
    mkdir(tmpdir)
    return tempfile.mkdtemp(prefix="fab", dir=tmpdir)
