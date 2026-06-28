<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Issue: Interactive Crop and Save Feature

- **Status**: Closed
- **Type**: Feature Request
- **Created**: 2026-06-28
- **Resolved**: 2026-06-29

## Context and Requirements

The user requested an interactive crop feature in the Sprite View preview tool:
1. **Interactive Crop**:
   - Drag to adjust crop box, or toggle via Titlebar Crop Button.
   - Snapped to source image pixels.
   - Display crop dimensions indicator pill.
   - Press `Esc` or click outside the image to reset/cancel crop mode.
   - Click "Crop" overlay button or press `Enter` to crop in-memory.
   - 8-way resize handles (12px visual size, 18px grab targets).
   - Dragging inside the crop helper translates the crop box.
2. **Titlebar Save Upgrades**:
   - Save button uses a disk icon (`💾` / `document-save-symbolic`).
   - Clicking it saves instantly with metadata preservation (PNG, JPG, GIF).
   - Dropdown arrow (`↓` / `pan-down-symbolic`) reveals options: "Save" and "Save as...".
3. **Modularity**:
   - Keep code modular. Avoid putting large blocks of code in the main application logic class.

---

## Resolution

- **Modularity**: Extracted all crop controller state, drawing methods, and drag/grab handlers to a separate [CropManager](file:///home/uwe/projects/spriteview/sprite_view/ui/crop.py) class in a new module.
- **Split Save Button**: Packaged the save action and dropdown menus in a linked horizontal box, utilizing GNOME actions (`save-instant`, `save-as`) and a native `Gtk.FileDialog`.
- **Tests**: Added tests for crop coordinate calculations and in-memory execution in [tests/test_preview.py](file:///home/uwe/projects/spriteview/tests/test_preview.py). All 39 test cases pass.
