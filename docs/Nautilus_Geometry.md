<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
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

## Important Caveat: Persistence on Close

While the GSettings override pattern successfully controls the startup size of a newly opened window, **Nautilus automatically persists its window size to GSettings when the window is closed**. 

If the overridden window (e.g., sized at `600x400`) is closed, Nautilus will write `(600, 400)` back into the `initial-size` key upon exit, overwriting the restored value.

### Resetting to Defaults

If your Nautilus window size becomes stuck at a small size, you can reset it to the GNOME system defaults with the following command:

```bash
gsettings reset org.gnome.nautilus.window-state initial-size
```

Because of this built-in persistence behavior, it is generally recommended **not to force window geometry programmatically** in development scripts or Makefiles, but rather to allow the user's manual resizing preferences to dictate the layout naturally.
