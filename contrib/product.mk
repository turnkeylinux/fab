#!/usr/bin/make -f

ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
endif

ifndef RELEASE
$(warning RELEASE not defined - default paths for POOL and BOOTSTRAP may break)
endif

# (to disable set to empty string)
MKSQUASHFS_COMPRESS ?= yes 
MKSQUASHFS_VERBOSE ?=

define MKSQUASHFS_OPTS
$(if $(MKSQUASHFS_COMPRESS),, -noD -noI -noF -no-fragments) \
$(if $(MKSQUASHFS_VERBOSE), -info)
endef

# FAB_PATH dependent infrastructural components
POOL ?= $(FAB_PATH)/pools/$(RELEASE)
BOOTSTRAP ?= $(FAB_PATH)/bootstraps/$(RELEASE)
CDROOT ?= $(FAB_PATH)/cdroots/bootsplash
FAB_PLAN_INCLUDE_PATH ?= $(FAB_PATH)/common-plans
FAB_TMPDIR ?= $(FAB_PATH)/tmp

export FAB_POOL_PATH = $(POOL)
export FAB_PLAN_INCLUDE_PATH
export FAB_TMPDIR

# default locations of product build inputs
PLAN ?= plan/main
ROOT_OVERLAY ?= overlay
CDROOT_OVERLAY ?= cdroot.overlay
REMOVELIST ?= removelist

INITRAMFS_PACKAGES ?= busybox-initramfs casper

# build output path
O ?= .

ISOLABEL ?= $(shell basename $(shell pwd))

STAMPS_DIR = $O/stamps

define remove-deck
	@if deck --isdeck $1; then \
		if [ "$$(basename $1)" = "root.tmp" ] && deck --isdirty $1; then \
			echo "error: root.tmp is dirty with manual changes. To continue: deck -D $(strip $1)"; \
			exit 1; \
		fi; \
		echo deck -D $1; \
		deck -D $1; \
	fi
endef

all: $O/product.iso

_redeck = if deck --isdeck $1; then deck $1; fi
redeck:
	$(call _redeck, $O/bootstrap)
	$(call _redeck, $O/root.build)
	$(call _redeck, $O/root.patched)

debug:
	$(foreach v, $V, $(warning $v = $($v)))
	@true

define help/body
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
	@echo '  FAB_TMPDIR                 $(value FAB_TMPDIR)'
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
	@echo '$$ rm $(value STAMPS_DIR)/<target>'
	@echo
	@echo '# build a target (default: product.iso)'
	@echo '$$ make [target] [O=path/to/build/dir]'
	@echo '  clean         # clean all build targets'
	@echo '  bootstrap     # minimal chrootable filesystem used to bootstrap the root'
	@echo '  root.spec     # the spec from which root.build is built (I.e., resolved plan)'
	@echo '  root.build    # created by applying the root.spec to the bootstrap'
	@echo '  root.patched  # deck root.build and apply the root overlay and removelist'
	@echo '  root.tmp      # temporary changes here are squashed into a separate layer'
	@echo '  cdroot        # created by squashing root.patched into cdroot template + overlay'
	@echo '  product.iso   # product ISO created from the cdroot'
	@echo
	@echo '  updated-initramfs # rebuild product with updated initramfs'
	@echo '  updated-root-tmp  # rebuild product with updated root tmp'
endef

help:
	$(help/pre)
	$(help/body)
	$(help/post)

define clean/body
	$(call remove-deck, $O/root.tmp)
	$(call remove-deck, $O/root.patched)
	$(call remove-deck, $O/root.build)
	$(call remove-deck, $O/bootstrap)
	-rm -rf $O/root.spec $O/cdroot $O/product.iso $(STAMPS_DIR)
endef

clean:
	$(clean/pre)
	$(clean/body)
	$(clean/post)

### STAMPED_TARGETS

# target: bootstrap
bootstrap/deps ?= $(BOOTSTRAP) $(BOOTSTRAP).spec
define bootstrap/body
	$(call remove-deck, $O/bootstrap)
	$(call remove-deck, $O/root.build)
	deck $(BOOTSTRAP) $O/bootstrap
endef

# target: root.spec
root.spec/deps ?= $(STAMPS_DIR)/bootstrap $(wildcard plan/*)
define root.spec/body
	fab-plan-resolve --output=$O/root.spec $(PLAN) $O/bootstrap
endef

# target: root.build
root.build/deps ?= $(STAMPS_DIR)/bootstrap $(STAMPS_DIR)/root.spec
define root.build/body
	if ! deck --isdeck $O/root.build; then deck $O/bootstrap $O/root.build; fi
	fab-install --no-deps $O/root.build $O/root.spec
endef

# target: root.patched
# undefine REMOVELIST if the file doesn't exist
ifeq ($(wildcard $(REMOVELIST)),)
REMOVELIST =
endif

root.patched/deps ?= $(STAMPS_DIR)/root.build $(REMOVELIST)
define root.patched/body
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

root.tmp/deps ?= $(STAMPS_DIR)/root.patched
define root.tmp/body
	$(call remove-deck, $O/root.tmp)
	deck $O/root.patched $O/root.tmp
endef

# target: cdroot
cdroot/deps ?= $(STAMPS_DIR)/root.patched $(CDROOT)
define cdroot/body
	if [ -e $O/cdroot ]; then rm -rf $O/cdroot; fi
	cp -a $(CDROOT) $O/cdroot
	mkdir $O/cdroot/casper
	if [ -d $(CDROOT_OVERLAY) ]; then fab-apply-overlay $(CDROOT_OVERLAY) $O/cdroot; fi

	cp $O/root.patched/usr/lib/syslinux/isolinux.bin $O/cdroot/isolinux

	cp $O/root.patched/boot/$(shell basename $(shell readlink $O/root.patched/vmlinuz)) $O/cdroot/casper/vmlinuz
	cp $O/root.patched/boot/$(shell basename $(shell readlink $O/root.patched/initrd.img)) $O/cdroot/casper/initrd.gz

	mksquashfs $O/root.patched $O/cdroot/casper/10root.squashfs $(MKSQUASHFS_OPTS)
endef

# construct target rules
define _stamped_target
$1: $(STAMPS_DIR)/$1

$(STAMPS_DIR)/$1: $$($1/deps) $$($1/deps/extra)
	@mkdir -p $(STAMPS_DIR)
	$$($1/pre)
	$$($1/body)
	$$($1/post)
	touch $$@
endef

STAMPED_TARGETS := bootstrap root.spec root.build root.patched root.tmp cdroot
$(foreach target,$(STAMPED_TARGETS),$(eval $(call _stamped_target,$(target))))

define run-genisoimage
	genisoimage -o $O/product.iso -r -J -l \
		-V ${ISOLABEL} \
		-b isolinux/isolinux.bin \
		-c isolinux/boot.cat \
		-no-emul-boot \
		-boot-load-size 4 \
		-boot-info-table $O/cdroot/
endef

# target: product.iso
define product.iso/body
	rm -f $O/cdroot/casper/20tmp.squashfs
	@if deck --isdirty $O/root.tmp; then \
		get_last_level="deck --get-level=last $O/root.tmp"; \
		output=$O/cdroot/casper/20tmp.squashfs; \
		echo "mksquashfs \$$($$get_last_level) $$output $(MKSQUASHFS_OPTS)"; \
		\
		last_level=$$($$get_last_level); \
		mksquashfs $$last_level $$output $(MKSQUASHFS_OPTS); \
	fi;
	$(run-genisoimage)
endef
product.iso/deps ?= $(STAMPS_DIR)/cdroot $(STAMPS_DIR)/root.tmp
$O/product.iso: $(product.iso/deps) $(product.iso/deps/extra)
	$(product.iso/pre)
	$(product.iso/body)
	$(product.iso/post)

# target: updated-root-tmp
define updated-root-tmp/body
	$(product.iso/body)
endef

updated-root-tmp:
	$(updated-root-tmp/pre)
	$(updated-root-tmp/body)
	$(updated-root-tmp/post)

# target: updated-initramfs
define updated-initramfs/body
	rm -rf $O/product.iso
	$(root.patched/body)
	fab-install $O/root.patched $(INITRAMFS_PACKAGES)
	cp $O/root.patched/boot/$(shell basename $(shell readlink $O/root.patched/initrd.img)) $O/cdroot/casper/initrd.gz
	$(run-genisoimage)
endef


updated-initramfs/deps ?= $O/product.iso
updated-initramfs: $(update-initramfs/deps) $(updated-initramfs/deps/extra)
	$(updated-initramfs/pre)
	$(updated-initramfs/body)
	$(updated-initramfs/post)

.PHONY: all debug redeck help clean updated-initramfs updated-root-tmp $(STAMPED_TARGETS)
