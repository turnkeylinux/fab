#!/bin/sh
# Copyright (c) 2011-2012 TurnKey Linux - all rights reserved

apt-get clean

rm -rf /var/lib/apt/lists/
mkdir -p /var/lib/apt/lists/partial

rm -f /etc/apt/sources.list
