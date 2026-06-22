.PHONY: ⚙️  # make all targets phony

SHELL := bash
EXTENSION_NAME := sprite_view.py
INSTALL_SCRIPT := scripts/install.sh

MP4_SOURCES := $(wildcard website/assets/*.mp4)
WEBM_TARGETS := $(MP4_SOURCES:.mp4=.webm)

SHARE := $(HOME)/.local/share/

_sleep := s(){ for t in $$(seq $$1); do sleep 1; echo -n "."; done; echo; }; s

help: ⚙️  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

open: ⚙️  ## open sprites dir using "open"
	open sprites

nautilus: ⚙️  ## open sprites dir using "nautilus" directly
	@./scripts/nautilus-open

dev: ⚙️ test install
	@echo -n "waiting for nautilus restart"
	@$(_sleep) 3
	$(MAKE) open

webm: ⚙️ $(WEBM_TARGETS)  ## convert all mp4 screencasts to optimized webm (skips up-to-date files)

%.webm: %.mp4
	ffmpeg -y -i $< -c:v libvpx-vp9 -r 30 -crf 36 -b:v 0 -pix_fmt yuv420p -an $@

browse: ⚙️ ##  open website in browser
	open website/index.html

test: ⚙️  ## run syntax check and unit tests
	python3 -m py_compile $(EXTENSION_NAME)
	python3 -m unittest discover -s tests
	@echo "✅ Extension syntax check and unit tests passed"

pack: ⚙️  ## pack the app into a single self-contained file
	python3 scripts/pack.py

install: ⚙️ test pack  ## pack and install the extension and CLI, then restart Nautilus
	@cp dist/$(EXTENSION_NAME) "$(SHARE)/nautilus-python/extensions/$(EXTENSION_NAME)"
	@mkdir -p "$(HOME)/.local/bin"
	@cp dist/$(EXTENSION_NAME) "$(HOME)/.local/bin/spriteview"
	@chmod +x "$(HOME)/.local/bin/spriteview"
	@mkdir -p "$(SHARE)/applications"
	@cp spriteview.desktop "$(SHARE)/applications/com.ubunatic.spriteview.desktop"
	@mkdir -p "$(SHARE)/icons/hicolor/128x128/apps"
	@cp sprites/banner-8x.png "$(SHARE)/icons/hicolor/128x128/apps/com.ubunatic.spriteview.png"
	@mkdir -p "$(SHARE)/icons/hicolor/256x256/apps"
	@cp sprites/banner-8x.png "$(SHARE)/icons/hicolor/256x256/apps/com.ubunatic.spriteview.png"
	@desktop-file-validate "$(SHARE)/applications/com.ubunatic.spriteview.desktop"
	@gtk-update-icon-cache -f -t "$(SHARE)/icons/hicolor" 2>/dev/null || true
	@update-desktop-database "$(SHARE)/applications" 2>/dev/null || true
	@echo "✅ Packed and installed single-file version of $(EXTENSION_NAME)"
	@echo "✅ Installed spriteview CLI to $(HOME)/.local/bin/spriteview"
	@echo "✅ Installed desktop entry and icon"
	$(MAKE) restart

check-install: ⚙️  ## check installed files
	@find $(SHARE) -name '*com.ubunatic.spriteview*' 2>/dev/null || true

script-install: ⚙️ test  ## install the extension and restart Nautilus
	@chmod +x $(INSTALL_SCRIPT)
	@./$(INSTALL_SCRIPT)

uninstall: ⚙️  ## uninstall the extension and CLI, then restart Nautilus
	@rm -f "$(SHARE)/nautilus-python/extensions/$(EXTENSION_NAME)"
	@rm -rf "$(SHARE)/nautilus-python/extensions/sprite_view"
	@rm -rf "$(SHARE)/nautilus-python/extensions/__pycache__"
	@rm -f "$(HOME)/.local/bin/spriteview"
	@rm -f "$(SHARE)/applications/com.ubunatic.spriteview.desktop"
	@rm -f "$(SHARE)/icons/hicolor/128x128/apps/com.ubunatic.spriteview.png"
	@rm -f "$(SHARE)/icons/hicolor/256x256/apps/com.ubunatic.spriteview.png"
	@gtk-update-icon-cache -f -t "$(SHARE)/icons/hicolor" 2>/dev/null || true
	@update-desktop-database "$(SHARE)/applications" 2>/dev/null || true
	@nautilus -q || echo "failed to restart nautilus, see errors above"
	@echo "✅ Uninstalled extension and restarted Nautilus"

restart: ⚙️  ## restart Nautilus to apply changes
	@nautilus -q || true
	@echo "🔄 Nautilus restarted (it will reload on next open)"

