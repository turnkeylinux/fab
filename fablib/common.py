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
from typing import Any, NoReturn

def mkdir(path: os.PathLike) -> None:
    path = os.fspath(path)
    if not os.path.exists(path):
        os.makedirs(path)

## cli common
def fatal(s: Any) -> NoReturn:
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)

def error(s: Any) -> None:
    print("error: " + str(s), file=sys.stderr)

def warn(s: Any) -> None:
    print("warning: " + str(s), file=sys.stderr)
