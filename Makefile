.PHONY: ⚙️  # make all targets phony

SHELL := bash
EXTENSION_NAME := sprite_view.py
INSTALL_SCRIPT := scripts/install.sh

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

browse: ⚙️ ##  open website in browser
	open website/index.html

test: ⚙️  ## run syntax check and unit tests
	python3 -m py_compile $(EXTENSION_NAME)
	python3 -m unittest discover -s tests
	@echo "✅ Extension syntax check and unit tests passed"

pack: ⚙️  ## pack the app into a single self-contained file
	python3 scripts/pack.py

install: ⚙️ test pack  ## pack and install the extension, then restart Nautilus
	@cp dist/$(EXTENSION_NAME) "$(HOME)/.local/share/nautilus-python/extensions/$(EXTENSION_NAME)"
	@echo "✅ Packed and installed single-file version of $(EXTENSION_NAME)"

script-install: ⚙️ test  ## install the extension and restart Nautilus
	@chmod +x $(INSTALL_SCRIPT)
	@./$(INSTALL_SCRIPT)

uninstall: ⚙️  ## uninstall the extension and restart Nautilus
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/$(EXTENSION_NAME)"
	@rm -rf "$(HOME)/.local/share/nautilus-python/extensions/sprite_view"
	@rm -rf "$(HOME)/.local/share/nautilus-python/extensions/__pycache__"
	@nautilus -q || echo "failed to restart nautilus, see errors above"
	@echo "✅ Uninstalled extension and restarted Nautilus"

restart: ⚙️  ## restart Nautilus to apply changes
	@nautilus -q || true
	@echo "🔄 Nautilus restarted (it will reload on next open)"

