<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 002 — Interactive crop and save feature

**Status**: Closed — resolved in e272ca1
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Feature
**Related**: [Crop and save architecture](../docs/Interactive_Crop_And_Save.md), `e272ca1`

---

## 1. Problem & Motivation

Users needed an interactive way to select and adjust an image crop in the preview, apply it in memory, and save images with metadata preserved.

## 2. Technical Specification / Findings

- Support crop selection snapped to source pixels, with a dimensions indicator, resize handles, and moving the crop box by dragging inside it.
- Allow crop mode to be cancelled with Escape or a click outside the image, and applied with Enter or a crop action.
- Keep crop state, drawing, and pointer handling modular rather than adding large blocks to the main application class.
- Provide a direct save action and a menu for Save and Save as.

## 3. Implementation & Verification Plan

The crop controller was extracted to `sprite_view/ui/crop.py`. The titlebar save control provides an immediate save action and a Save as menu using `Gtk.FileDialog`. Crop coordinate and in-memory behavior tests were added; the original implementation record reported all 39 tests passing.
