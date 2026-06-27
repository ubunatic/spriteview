# Sibling Navigation, In-Place Reloading, and Gtk Application Uniqueness

This document details the architectural updates and session learnings regarding flicker-free folder navigation, PyGObject window reload lifecycle, and Gtk.Application uniqueness gotchas under DBus.

---

## 1. Sibling Folder Navigation and Flicker-Free Sequence Reloading

### Sibling Folder Navigation
To allow users to browse all sprite sheets or static images in a folder without manual file-opening dialogs:
* The custom `Gtk.HeaderBar` is equipped with previous (`go-previous-symbolic` / **Page Up**) and next (`go-next-symbolic` / **Page Down**) buttons.
- Sibling images in the current directory are located, sorted alphabetically, and filtered by supported extensions (`.png`, `.gif`, `.bmp`, `.jpg`, `.jpeg`, `.webp`).
- **Sequence Skipping**: If the currently active image is part of an animation sequence (e.g. `walk_01.png`, `walk_02.png`), clicking next/prev skips all other frames of the active sequence to jump directly to the next distinct sequence or standalone image.

### Flicker-Free In-Place Switch
- **The Problem**: Swapping the viewed image by destroying the old window and creating a new one causes the window manager to trigger exit/entry animations, resulting in visual flicker, resizing lag, and window positioning shift.
- **The Solution**: 
  1. The window layout, settings controls, sidebar rows, and menu buttons are created **statically once** in `ImagePreviewWindow.__init__`.
  2. Sequence loading, frame decoding, texture building, and animation controls visibility are handled **dynamically** in a custom `_load_sequence(self, file_paths, selected_file_path)` method.
  3. When folder navigation triggers or the user opens a new image via the file chooser, the window updates itself in-place via `_load_sequence()`, allowing the window to resize gracefully if needed while preserving the window session.

---

## 2. Gtk.Application Uniqueness Gotcha (DBus Swallow)

### The Problem
By default, Gtk.Application is instantiated with:
```python
app = Gtk.Application(application_id="com.ubunatic.spriteview", flags=Gio.ApplicationFlags.FLAGS_NONE)
```
- `FLAGS_NONE` enforces single-instance behavior (uniqueness) via DBus session registration.
- When `spriteview some_file.png` is run, if an instance of `com.ubunatic.spriteview` is already registered (such as a zombie background process, or the Nautilus extension process), the second CLI process connects to the primary instance, signals `activate`, and exits with code 0.
- Because `FLAGS_NONE` does **not** transfer command-line arguments to the primary instance (which requires `HANDLES_OPEN` or `HANDLES_COMMAND_LINE`), the file path `some_file.png` is completely swallowed and ignored, causing secondary launches to do nothing.

### The Fix
To ensure every terminal CLI launch opens its own window and loads the requested file:
- Changed Gtk.Application's flags to `Gio.ApplicationFlags.NON_UNIQUE`:
```python
app = Gtk.Application(application_id="com.ubunatic.spriteview", flags=Gio.ApplicationFlags.NON_UNIQUE)
```
This bypasses DBus single-instance synchronization, ensuring secondary processes run locally, parse their own CLI arguments, and successfully present their own windows.

---

## 3. Startup Smoke Testing (Liveness Integration Probe)

To guarantee that code changes, packaging changes, or Gtk refactorings do not render the application unusable on startup (which could easily happen due to Python's dynamic lookup causing runtime `AttributeError`s or missing imports during initialization):
- **Integration Test (`test_integration.py`)**: A dedicated startup integration test launches the compiled `dist/sprite_view.py` under `xvfb-run` with a timeout:
```python
xvfb-run timeout 2 python3 dist/sprite_view.py --about
```
- If the application crashes with a Python traceback or fails to initialize, the test fails immediately.
- If the application starts successfully, opens the window, and blocks in the Gtk event loop (until killed by the `timeout` utility with exit code 124), the smoke test passes. This ensures the app is fully functional at runtime before deployment.
