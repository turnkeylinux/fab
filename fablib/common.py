# Copyright (c) TurnKey GNU/Linux - https://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
import sys
from typing import NoReturn


def mkdir(path: os.PathLike) -> None:
    path = os.fspath(path)
    if not os.path.exists(path):
        os.makedirs(path)


## cli common
def fatal(message: str) -> NoReturn:
    print(f"Fatal error: {message}", file=sys.stderr)
    sys.exit(1)


def error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)
