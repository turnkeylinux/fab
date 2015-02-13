#!/usr/bin/python
# Copyright (c) 2011-2013 TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""
Configuration environment variables:
    FAB_POOL_PATH           Path to the package pool
    FAB_PLAN_INCLUDE_PATH   Global include path for plan preprocessing
"""

from os.path import *
import pyproject

class CliWrapper(pyproject.CliWrapper):
    DESCRIPTION = __doc__
    
    INSTALL_PATH = dirname(__file__)

    COMMANDS_USAGE_ORDER = ['cpp', 'chroot', 
                            '',
                            'plan-annotate', 'plan-resolve',
                            '',
                            'install',
                            '',
                            'apply-removelist', 'apply-overlay']
    
if __name__ == '__main__':
    CliWrapper.main()
