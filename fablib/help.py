# Copyright (c) TurnKey GNU/Linux - https://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import sys
from collections.abc import Callable
from typing import NoReturn


def usage(doc: str) -> Callable:
    def decor(print_syntax: Callable) -> Callable:
        def wrapper(message: str | None = None) -> NoReturn:
            if message:
                print(f"Error: {message}", file=sys.stderr)
            print_syntax()
            if doc:
                print(doc.strip(), file=sys.stderr)
            sys.exit(1)

        return wrapper

    return decor
