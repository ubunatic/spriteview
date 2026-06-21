.PHONY: ⚙️  # make all targets phony

EXTENSION_NAME := sprite_view.py
INSTALL_SCRIPT := scripts/install.sh

help: ⚙️  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

open: ⚙️  ## open sprites dir using "open"
	open sprites

nautilus: ⚙️  ## open sprites dir using "nautilus" directly
	@orig_size=$$(gsettings get org.gnome.nautilus.window-state initial-size) && \
	gsettings set org.gnome.nautilus.window-state initial-size '(600, 400)' && \
	nautilus --no-desktop sprites & \
	sleep 1.5 && \
	gsettings set org.gnome.nautilus.window-state initial-size "$$orig_size"

dev: ⚙️test install nautilus

browse: ⚙️ ##  open website in browser
	open website/index.html

test: ⚙️  ## run syntax check on the Python extension
	python3 -m py_compile $(EXTENSION_NAME)
	@echo "✅ Extension syntax check passed"

install: ⚙️ test  ## install the extension and restart Nautilus
	@cp $(EXTENSION_NAME) "$(HOME)/.local/share/nautilus-python/extensions/$(EXTENSION_NAME)"
	@echo "✅ Installed local version of $(EXTENSION_NAME)"

script-install: ⚙️ test  ## install the extension and restart Nautilus
	@chmod +x $(INSTALL_SCRIPT)
	@./$(INSTALL_SCRIPT)

uninstall: ⚙️  ## uninstall the extension and restart Nautilus
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/$(EXTENSION_NAME)"
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/__pycache__/sprite_view."*
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/nautilus_preview.py"
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/__pycache__/nautilus_preview."*
	@nautilus -q || echo "failed to restart nautilus, see errors above"
	@echo "✅ Uninstalled extension and restarted Nautilus"

restart: ⚙️  ## restart Nautilus to apply changes
	@nautilus -q || true
	@echo "🔄 Nautilus restarted (it will reload on next open)"

