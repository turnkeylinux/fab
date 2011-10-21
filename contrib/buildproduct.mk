#!/usr/bin/make -f

ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
endif

ifndef RELEASE
$(warning RELEASE not defined - default paths for POOL and BOOTSTRAP may break)
endif

# (to disable set to empty string)
MKSQUASHFS_COMPRESS ?= yes 
MKSQUASHFS_VERBOSE ?= yes  

define MKSQUASHFS_OPTS
$(if $(MKSQUASHFS_COMPRESS),, -noD -noI -noF -no-fragments) \
$(if $(MKSQUASHFS_VERBOSE), -info)
endef

# FAB_PATH dependent infrastructural components
POOL ?= $(FAB_PATH)/pools/$(RELEASE)
BOOTSTRAP ?= $(FAB_PATH)/bootstraps/$(RELEASE)
CDROOT ?= $(FAB_PATH)/cdroots/bootsplash
FAB_PLAN_INCLUDE_PATH ?= $(FAB_PATH)/common-plans
export FAB_PLAN_INCLUDE_PATH

# default locations of product build inputs
PLAN ?= plan/main
ROOT_OVERLAY ?= overlay
CDROOT_OVERLAY ?= cdroot.overlay
REMOVELIST ?= removelist

INITRAMFS_PACKAGES ?= busybox-initramfs casper

# build output path
O ?= .

ISOLABEL ?= $(shell basename $(shell pwd))

STAMPS_DIR := $O/.stamps
$(shell mkdir -p $(STAMPS_DIR))

define remove-deck
	if deck -t $(strip $1); then \
		deck -D $(strip $1); \
	fi
endef

all: $O/product.iso

debug:
	$(foreach v, $V, $(warning $v = $($v)))
	@true

define help/main
	@echo '=== Configurable variables'
	@echo 'Resolution order:'
	@echo '1) command line (highest precedence)'
	@echo '2) product Makefile'
	@echo '3) environment variable'
	@echo '4) built-in default (lowest precedence)'
	@echo
	@echo '# Mandatory configuration variables:'
	@echo '  FAB_PATH and RELEASE       used to calculate default paths for input variables'
	@echo
	@echo '# Build configuration variables:'
	@echo '  MKSQUASHFS_COMPRESS        if not an empty string - mksquashfs uses compression'
	@echo '  MKSQUASHFS_VERBOSE         if not an empty string - mksquashfs is verbose'
	@echo
	@echo '# Build context variables    [VALUE]'
	@echo '  POOL                       $(value POOL)'
	@echo '  BOOTSTRAP                  $(value BOOTSTRAP)'
	@echo '  CDROOT                     $(value CDROOT)'
	@echo '  FAB_PLAN_INCLUDE_PATH      $(value FAB_PLAN_INCLUDE_PATH)'
	@echo
	@echo '# Product input variables    [VALUE]'  
	@echo '  PLAN                       $(value PLAN)'
	@echo '  ROOT_OVERLAY               $(value ROOT_OVERLAY)'
	@echo '  CDROOT_OVERLAY             $(value CDROOT_OVERLAY)'
	@echo '  REMOVELIST                 $(value REMOVELIST)'
	@echo
	@echo '# Product output variables   [VALUE]'
	@echo '  O                          $(value O)'
	@echo '  ISOLABEL                   $(value ISOLABEL)'
	@echo
	@echo '=== Usage'
	@echo '# remake target and the targets that depend on it'
	@echo '$$ rm $$O/.stamps/<target>'
	@echo
	@echo '# build a target (default: product.iso)'
	@echo '$$ make [target] [O=path/to/build/dir]'
	@echo '  clean         # clean all build targets'
	@echo '  bootstrap     # minimal chrootable filesystem used to bootstrap the root'
	@echo '  root.spec     # the spec from which root.build is built (I.e., resolved plan)'
	@echo '  root.build    # created by applying the root.spec to the bootstrap'
	@echo '  root.patched  # created by applying the root overlay and removelist'
	@echo '  cdroot        # created by squashing root.patched into cdroot template + overlay'
	@echo '  product.iso   # product ISO created from the cdroot'
	@echo
	@echo '# reinstall INITRAMFS_PACKAGES in root.patched and recreate product.iso'
	@echo '  update-initramfs'
endef

help:
	$(help/pre)
	$(help/main)
	$(help/post)

define clean/main
	fab-chroot-umount $O/root.build
	$(call remove-deck, $O/root.patched)
	$(call remove-deck, $O/root.build)
	$(call remove-deck, $O/bootstrap)
	-rm -rf $O/root.spec $O/cdroot $O/product.iso $(STAMPS_DIR) tmp
endef

clean:
	$(clean/pre)
	$(clean/main)
	$(clean/post)

define example/main
	echo example1
endef

define bootstrap/main
	$(call remove-deck, $O/bootstrap)
	$(call remove-deck, $(0)/root.build)
	deck $(BOOTSTRAP) $O/bootstrap
endef

bootstrap/deps = $(BOOTSTRAP) $(BOOTSTRAP).spec
$(STAMPS_DIR)/bootstrap: $(bootstrap/deps)
	$(bootstrap/pre)
	$(bootstrap/main)
	$(bootstrap/post)
	touch $@

define root.spec/main
	fab-plan-resolve --output=$O/root.spec $(PLAN) $(POOL) $O/bootstrap
endef

root.spec/deps = $(STAMPS_DIR)/bootstrap $(wildcard plan/*)
$(STAMPS_DIR)/root.spec: $(root.spec/deps)
	$(root.spec/pre)
	$(root.spec/main)
	$(root.spec/post)
	touch $@

define root.build/main
	if [ -e $O/root.build ]; then fab-chroot-umount $O/root.build; fi
	if ! deck -t $O/root.build; then deck $O/bootstrap $O/root.build; fi
	fab-spec-install $O/root.spec $(POOL) $O/root.build
endef

root.build/deps = $(STAMPS_DIR)/bootstrap $(STAMPS_DIR)/root.spec
$(STAMPS_DIR)/root.build: $(root.build/deps)
	$(root.build/pre)
	$(root.build/main)
	$(root.build/post)
	touch $@

# undefine REMOVELIST if it doesn't exist
ifeq ($(wildcard $(REMOVELIST)),)
REMOVELIST =
endif

define root.patched/main
	$(call remove-deck, $O/root.patched)
	deck $O/root.build $O/root.patched
	$(if $(REMOVELIST),fab-apply-removelist $(REMOVELIST) $O/root.patched)
	if [ -d $(ROOT_OVERLAY) ]; then \
		fab-apply-overlay $(ROOT_OVERLAY) $O/root.patched; \
		if [ -e $(ROOT_OVERLAY)/etc/casper.conf ]; then \
			fab-chroot --mount $O/root.patched "update-initramfs -u"; \
		fi \
	fi
	fab-chroot $O/root.patched "cp /usr/share/base-files/dot.bashrc /etc/skel/.bashrc"
	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
endef

root.patched/deps = $(STAMPS_DIR)/root.build $(REMOVELIST)
$(STAMPS_DIR)/root.patched: $(root.patched/deps)
	$(root.patched/pre)
	$(root.patched/main)
	$(root.patched/post)
	touch $@

define cdroot/main
	if [ -e $O/cdroot ]; then rm -rf $O/cdroot; fi
	cp -a $(CDROOT) $O/cdroot
	mkdir $O/cdroot/casper
	if [ -d $(CDROOT_OVERLAY) ]; then fab-apply-overlay $(CDROOT_OVERLAY) $O/cdroot; fi

	cp $O/root.patched/usr/lib/syslinux/isolinux.bin $O/cdroot/isolinux
	cp $O/root.patched/vmlinuz $O/cdroot/casper/vmlinuz
	cp $O/root.patched/initrd.img $O/cdroot/casper/initrd.gz

	mksquashfs $O/root.patched $O/cdroot/casper/filesystem.squashfs $(MKSQUASHFS_OPTS)
endef

cdroot/deps = $(STAMPS_DIR)/root.patched $(CDROOT)
$(STAMPS_DIR)/cdroot: $(cdroot/deps)
	$(cdroot/pre)
	$(cdroot/main)
	$(cdroot/post)
	touch $@

define run-mkisofs
	mkisofs -o $O/product.iso -r -J -l \
		-V ${ISOLABEL} \
		-b isolinux/isolinux.bin \
		-c isolinux/boot.cat \
		-no-emul-boot \
		-boot-load-size 4 \
		-boot-info-table $O/cdroot/
endef

define product.iso/main
	$(run-mkisofs)
endef

$O/product.iso: $(STAMPS_DIR)/cdroot
	$(product.iso/pre)
	$(product.iso/main)
	$(product.iso/post)

define update-initramfs/main
	rm -rf $O/product.iso
	for package in $(INITRAMFS_PACKAGES); do \
		echo $$package | fab-spec-install - $(POOL) $O/root.patched; \
	done

	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
	cp $O/root.patched/boot/initrd.img-* $O/cdroot/casper/initrd.gz
	$(run-mkisofs)
endef

update-initramfs: $O/product.iso
	$(update-initramfs/pre)
	$(update-initramfs/main)
	$(update-initramfs/post)

# virtual targets that prequire $(STAMPS_DIR)/$target
_VIRT_TARGETS := bootstrap root.spec root.build root.patched cdroot
$(_VIRT_TARGETS): %: $(STAMPS_DIR)/%

.PHONY: all debug help clean update-initramfs $(_VIRT_TARGETS)
