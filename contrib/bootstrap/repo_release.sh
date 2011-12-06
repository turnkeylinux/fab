#!/bin/bash

if [ $# -eq "3" ]; then
    RELEASE=$1
    COMPONENT=$2
    REPO_PATH=$3
else
    echo "Syntax: ${0} <release> <component> <repo_path>"
    exit 1
fi

REPO_RELEASE=${REPO_PATH}/dists/${RELEASE}

cat << EOF > ${REPO_RELEASE}/${COMPONENT}/binary-i386/Release
Archive: ${RELEASE}
Version: 0.1
Component: ${COMPONENT}
Origin: TurnKey
Label: TurnKey
EOF

OUT="${REPO_RELEASE}/Release"
TMPOUT="${REPO_PATH}/release.tmp"

cat << EOF > ${TMPOUT}
Origin: TurnKey
Label: TurnKey
Suite: ${RELEASE}
Version: 0.1
Codename: ${RELEASE}
Architectures: i386
Components: ${COMPONENT}
Description: TurnKey ${RELEASE} 0.1
EOF

cd ${REPO_PATH} && \
	rm -rf ${OUT}* && \
	apt-ftparchive release dists/${RELEASE} >> ${TMPOUT}

mv ${TMPOUT} ${OUT}

