ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
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

prereq: $(BOOTSTRAP)
	@echo $<
	@echo $(BOOTSTRAP)

debug:
	$(foreach v, $V, $(warning $v = $($v)))
	@true

help:
	@echo '=== Configurable variables'
	@echo 'Resolution order:'
	@echo '1) command line (highest precedence)'
	@echo '2) product Makefile'
	@echo '3) environment variable'
	@echo '4) built-in default (lowest precedence)'
	@echo
	@echo '# Mandatory configuration variables:'
	@echo '  FAB_PATH and RELEASE	used to calculate default paths for input variables'
	@echo
	@echo '# Build configuration variables:'
	@echo '  MKSQUASHFS_COMPRESS	if not an empty string - disables mksquashfs compression'
	@echo '  MKSQUASHFS_VERBOSE	if not an empty string - mksquashfs is verbose'
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
	@echo '=== Usage:'
	@echo '# remake target and the targets that depend on it'
	@echo '$$ rm .stamps/<target>'
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

clean:
	fab-chroot-umount $O/root.build
	$(call remove-deck, $O/root.patched)
	$(call remove-deck, $O/root.build)
	$(call remove-deck, $O/bootstrap)
	-rm -rf $O/root.spec $O/cdroot $O/product.iso $(STAMPS_DIR) tmp

$(STAMPS_DIR)/bootstrap: $(BOOTSTRAP) $(BOOTSTRAP).spec
	$(call remove-deck, $O/bootstrap)
	$(call remove-deck, $(0)/root.build)
	deck $(BOOTSTRAP) $O/bootstrap
	touch $@

$(STAMPS_DIR)/root.spec: $(STAMPS_DIR)/bootstrap $(wildcard plan/*)
	fab-plan-resolve --output=$O/root.spec $(PLAN) $(POOL) $O/bootstrap
	touch $@

$(STAMPS_DIR)/root.build: $(STAMPS_DIR)/bootstrap $(STAMPS_DIR)/root.spec
	if [ -e $O/root.build ]; then fab-chroot-umount $O/root.build; fi
	if ! deck -t $O/root.build; then deck $O/bootstrap $O/root.build; fi
	fab-spec-install $O/root.spec $(POOL) $O/root.build
	touch $@

# undefine REMOVELIST if it doesn't exist
ifeq ($(wildcard $(REMOVELIST)),)
REMOVELIST =
endif

$(STAMPS_DIR)/root.patched: $(STAMPS_DIR)/root.build $(REMOVELIST)
	$(call remove-deck, $O/root.patched)
	deck $O/root.build $O/root.patched
ifdef REMOVELIST
	fab-apply-removelist $(REMOVELIST) $O/root.patched
endif
	if [ -d $(ROOT_OVERLAY) ]; then \
		fab-apply-overlay $(ROOT_OVERLAY) $O/root.patched; \
		if [ -e $(ROOT_OVERLAY)/etc/casper.conf ]; then \
			fab-chroot --mount $O/root.patched "update-initramfs -u"; \
		fi \
	fi
	fab-chroot $O/root.patched "cp /usr/share/base-files/dot.bashrc /etc/skel/.bashrc"
	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
	touch $@

$(STAMPS_DIR)/cdroot: $(STAMPS_DIR)/root.patched $(CDROOT)
	if [ -e $O/cdroot ]; then rm -rf $O/cdroot; fi
	cp -a $(CDROOT) $O/cdroot
	mkdir $O/cdroot/casper
	if [ -d $(CDROOT_OVERLAY) ]; then fab-apply-overlay $(CDROOT_OVERLAY) $O/cdroot; fi

	cp $O/root.patched/usr/lib/syslinux/isolinux.bin $O/cdroot/isolinux
	cp $O/root.patched/vmlinuz $O/cdroot/casper/vmlinuz
	cp $O/root.patched/initrd.img $O/cdroot/casper/initrd.gz

	mksquashfs $O/root.patched $O/cdroot/casper/filesystem.squashfs $(MKSQUASHFS_OPTS)
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

$O/product.iso: $(STAMPS_DIR)/cdroot
	$(run-mkisofs)

update-initramfs: $O/product.iso
	rm -rf $O/product.iso
	for package in $(INITRAMFS_PACKAGES); do \
		echo $$package | fab-spec-install - $(POOL) $O/root.patched; \
	done

	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
	cp $O/root.patched/boot/initrd.img-* $O/cdroot/casper/initrd.gz
	$(run-mkisofs)

# virtual targets that prequire $(STAMPS_DIR)/$target
_VIRT_TARGETS := bootstrap root.spec root.build root.patched cdroot
$(_VIRT_TARGETS): %: $(STAMPS_DIR)/%

.PHONY: all debug help clean update-initramfs $(_VIRT_TARGETS)
