#!/bin/sh
set -ex
# needs a build/cdroot/10root.squashfs to exist which is provided by fab (make cdroot)
# also check that live tools exist

for cmd in rsync lb apt-ftparchive; do
    if ! command -v "$cmd"; then
        echo "$cmd doesn't seem to exist -- install it!"
        exit 1
    fi
done

APP="$(basename $(pwd))"
rsync -avz /usr/share/fab/lb-overlay/ ./
lb config
lb build
mv "turnkey-$APP-amd64.hybrid.iso" build/product.iso
