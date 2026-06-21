# Nautilus Window Geometry on Wayland

Modern GNOME desktop environments running on Wayland utilize GTK4, which has removed support for the legacy `--geometry` command-line option. Additionally, Wayland's security model prevents traditional X11 automation tools like `xdotool` or `wmctrl` from querying or resizing native windows.

To programmatically open a Nautilus window with a specific size (without permanently altering user preferences), you can temporarily override Nautilus's window-state GSettings before launch.

## The GSettings Override Pattern

This script captures the current `initial-size` setting, applies the target width and height, launches Nautilus, and immediately restores the user's original preferences after the application has read the configurations.

```bash
#!/usr/bin/env bash
# Open Nautilus with a custom window size on Wayland

set -euo pipefail

# 1. Save the user's current window size
orig_size=$(gsettings get org.gnome.nautilus.window-state initial-size)

# 2. Set the target size (e.g., 600x400)
gsettings set org.gnome.nautilus.window-state initial-size '(600, 400)'

# 3. Launch Nautilus in the background
nautilus --no-desktop sprites &

# 4. Sleep briefly to ensure Nautilus reads the configuration on startup
sleep 1.5

# 5. Restore the original size
gsettings set org.gnome.nautilus.window-state initial-size "$orig_size"
```

## Integrating with Make

You can also integrate this pattern directly into a `Makefile`:

```makefile
GEOMETRY_WIDTH  := 600
GEOMETRY_HEIGHT := 400

nautilus: ⚙️  ## open sprites dir in a small Nautilus window
	@orig_size=$$(gsettings get org.gnome.nautilus.window-state initial-size) && \
	gsettings set org.gnome.nautilus.window-state initial-size '($(GEOMETRY_WIDTH), $(GEOMETRY_HEIGHT))' && \
	nautilus --no-desktop sprites & \
	sleep 1.5 && \
	gsettings set org.gnome.nautilus.window-state initial-size "$$orig_size"
```
