#!/bin/sh
set -ex

# needs a root.patched to exist

mkdir -p auto

cat >auto/config<<'EOF'
#!/bin/sh
set -e
lb config noauto \
    --apt-indices false \
    --apt-recommends false \
    --binary-image iso-hybrid \
    --cache true \
    --cache-indices true \
    --cache-packages true \
    --cache-stages 'bootstrap chroot' \
    --checksums 'sha512' \
    --chroot-filesystem squashfs \
    --clean \
    --compression xz \
    --debian-installer live \
    --debian-installer-gui false \
    --debootstrap-options '--variant=minbase --include="initramfs-tools,gpg,gpg-agent,ca-certificates"' \
    --memtest none \
    --gzip-options '--best' \
    --hdd-label TURNKEY \
    --image-name turnkey \
    --iso-application 'TurnKey Linux' \
    --iso-publisher 'TurnKey Linux; https://turnkeylinux.org' \
    --iso-volume 'TurnKey_Linux' \
    --loadlin false \
    --uefi-secure-boot enable \
    --zsync false \
    --win32-loader false \
    --verbose \
    --debug \
    "${@}"
EOF

cat >auto/build<<'EOF'
#!/bin/sh
set -e
lb build noauto "${@}" 2>&1 | tee lb-build.log
EOF

cat >auto/clean<<'EOF'
#!/bin/sh
set -e
lb clean noauto "${@}"
rm -f config/binary config/bootstrap config/chroot config/common config/source lb-build.log
EOF

chmod +x auto/*

lb config
lb build

rm -f binary/live/filesystem.squashfs turnkey-amd64.hybrid.iso .build/binary_iso
cp build/cdroot/live/10root.squashfs binary/live/filesystem.squashfs

sed -i 's/initrd.gz/initrd.img/g' build/cdroot/isolinux/menu.cfg
cp build/cdroot/isolinux/* binary/isolinux/

lb binary

mv turnkey-amd64.hybrid.iso build/product.iso
