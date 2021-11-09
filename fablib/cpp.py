# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
import subprocess
from typing import Tuple, List, Optional

CPP_ARGS = ("-I", "-D", "-U")


class Error(Exception):
    pass


def cpp(cpp_input: str, cpp_opts: Optional[List[Tuple[str, str]]]=None) -> str:
    """preprocess <input> through cpp -> preprocessed output
       input may be path/to/file or iterable data type
    """
    cpp_input = os.fspath(cpp_input)
    if cpp_opts is None:
        cpp_opts = []
    args = ["-Ulinux"]

    for opt, val in cpp_opts:
        args.append(opt + val)

    include_path = os.environ.get("FAB_PLAN_INCLUDE_PATH")
    if include_path:
        for path in include_path.split(":"):
            args.append("-I" + path)

    command = ["cpp", cpp_input]
    if args:
        command += args

    c = subprocess.run(command, text=True, capture_output=True)

    if c.returncode != 0:
        raise Error(" ".join(command), c.returncode, c.stderr)
    return c.stdout
