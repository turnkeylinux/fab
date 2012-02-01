#!/bin/sh -e
# Copyright (c) 2011-2012 TurnKey Linux - all rights reserved

rm -f /etc/resolv.conf
rm -f /etc/hostname

apt-get clean

rm -rf /var/lib/apt/lists/
mkdir -p /var/lib/apt/lists/partial

rm -f /etc/apt/sources.list
