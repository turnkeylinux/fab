from typing import IO
import os
from os.path import exists, join, isfile
import re
import shutil
import glob
from .common import fatal, warn

KNOWN_PREFIXES = {
    '~'
}

def parse_removelist(fob: IO[str]) -> list[tuple[str | None, str | None, str | None]]:
    out = []

    for line in fob:
        line = re.sub(r'#.*', '', line).strip()

        if not line:
            continue

        if '/' not in line:
            out.append((None, None, f'non-empty invalid line {line!r}'))

        prefix, path = line.split('/', 1)
        path = '/' + path
        prefix = prefix.strip()

        if prefix and prefix not in KNOWN_PREFIXES:
            out.append((None, None, f'unknown prefix {prefix!r} in line {line!r}'))

        out.append((prefix, path, None))
    return out

def remove(path: str):
    if not exists(path):
        print(f'rm {path}')
        warn(f'file or directory {path!r} not found!')
    elif isfile(path):
        print(f'rm {path}')
        os.remove(path)
    else:
        print(f'rm -r {path}')
        shutil.rmtree(path)

def apply_removelist(removelist_fob: IO[str], root_path: str) -> None:
    for (prefix, path, error) in parse_removelist(removelist_fob):
        if error or path is None:
            fatal(error)
        path = join(root_path, path.strip('/'))
        if prefix == '~':
            for path in glob.glob(path):
                remove(path)
        else:
            remove(path)
