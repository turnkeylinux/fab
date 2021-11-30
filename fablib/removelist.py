from typing import IO, List, Tuple
import os
from os import mkdir
from os.path import exists, dirname, join, isfile
import re
import sys
import shutil
from tempfile import TemporaryDirectory
from .common import fatal, warn

def parse_removelist(fob: IO[str]) -> Tuple[List[str], List[str]]:
    remove = []
    restore = []

    for line in fob:
        line = re.sub(r'#.*', '', line).strip()

        if not line:
            continue

        if line.startswith('!'):
            restore.append(line[1:])
        else:
            remove.append(line)
    return remove, restore

def _move(entry: str, source_root_path: str, dest_root_path: str) -> None:
    entry = entry.strip('/')
    source_path = join(source_root_path, entry)
    dest_path = join(dest_root_path, entry)

    if not exists(source_path):
        warn('entry does not exist: ' + entry)
        return

    mkdir(dirname(dest_path))
    shutil.move(source_path, dest_path)

def apply_removelist(removelist_fob: IO[str], root_path: str) -> None:
    remove, restore = parse_removelist(removelist_fob)
    if restore:
        warn("DEPRECATED: fab-apply-removelist restore functionality is non-"
             "functional and will produce a hard error in the future")

    for entry in remove:
        path = join(root_path, entry.strip('/'))
        if not exists(path):
            print(f'rm {path}')
            warn(f'file or directory {path!r} not found!')
        elif isfile(path):
            print(f'rm {path}')
            os.remove(path)
        else:
            print(f'rm -r {path}')
            shutil.rmtree(path)
