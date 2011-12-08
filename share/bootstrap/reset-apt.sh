#!/bin/sh

apt-get clean

rm -rf /var/lib/apt/lists/
mkdir -p /var/lib/apt/lists/partial

rm -f /etc/apt/sources.list
