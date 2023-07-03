#!/bin/sh
set -ex

# check live tools exist
if ! command -v lb; then
    echo "lb doesn't seem to exist -- install live-tools!"
    exit 1
fi

# needs a root.patched to exist which is provided by fab

mkdir -p auto

cat >auto/config<<'EOF'
#!/bin/sh
set -e
lb config noauto \
    --distribution bookworm \
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

mkdir -p config/hooks/live
cat >config/hooks/live/turnkey.hook.binary<<'EOF'
rm -rf pool pool-udeb *sum* boot/grub/install.cfg boot/grub/install_start.cfg boot/grub/grub.cfg
rsync -avz --delete ../build/cdroot/live/ ./live/
rsync -avz --delete ../build/cdroot/isolinux/ ./isolinux/
rsync -avz ../build/cdroot/boot/grub/ ./boot/grub/
EOF

chmod +x config/hooks/live/turnkey.hook.binary

lb config
lb build

mv turnkey-amd64.hybrid.iso build/product.iso
