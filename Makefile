.PHONY: ⚙️  # make all targets phony

EXTENSION_NAME := nautilus_preview.py
SCRIPTS_DIR    := scripts
INSTALL_SCRIPT := $(SCRIPTS_DIR)/install.sh

help: ⚙️  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

open:
	# open real project
	open ~/projects/emojig/spec/art/about/

browse: ⚙️ ## open website in browser
	open website/index.html

test: ⚙️  ## run syntax check on the Python extension
	python3 -m py_compile $(EXTENSION_NAME)
	@echo "✅ Extension syntax check passed"

test-sprites: ⚙️  ## generate test sprite files (sprites/sprite_0001.png to sprites/sprite_0004.png)
	@mkdir -p sprites
	python3 -c "import gi; gi.require_version('GdkPixbuf', '2.0'); from gi.repository import GdkPixbuf; \
	[ (p.fill(c), p.savev(f'sprites/sprite_{i+1:04d}.png', 'png', [], [])) for i, c in enumerate([0xff0000ff, 0x00ff00ff, 0x0000ffff, 0xffff00ff]) for p in [GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 16, 16)] ]"
	@echo "✅ Generated test sprite files: sprites/sprite_0001.png to sprites/sprite_0004.png"

install: ⚙️ test  ## install the extension and restart Nautilus
	@chmod +x $(INSTALL_SCRIPT)
	@./$(INSTALL_SCRIPT)

uninstall: ⚙️  ## uninstall the extension and restart Nautilus
	@rm -f "$(HOME)/.local/share/nautilus-python/extensions/$(EXTENSION_NAME)"
	@nautilus -q || true
	@echo "✅ Uninstalled extension and restarted Nautilus"

restart: ⚙️  ## restart Nautilus to apply changes
	@nautilus -q || true
	@echo "🔄 Nautilus restarted (it will reload on next open)"
