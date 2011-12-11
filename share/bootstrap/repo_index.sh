#!/bin/bash
# Copyright (c) 2011-2012 TurnKey Linux - all rights reserved

if [ $# -eq "3" ]; then
    RELEASE=$1
    COMPONENT=$2
    REPO=$3
else
    echo "Syntax: ${0} <release> <component> <repo>"
    exit 1
fi

mkdir -p ${REPO}/dists/${RELEASE}/${COMPONENT}/binary-i386

cd ${REPO} && \
    apt-ftparchive packages pool/${COMPONENT} > \
    dists/${RELEASE}/${COMPONENT}/binary-i386/Packages

