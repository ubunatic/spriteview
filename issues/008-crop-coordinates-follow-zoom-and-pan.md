<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 008 — Crop coordinates follow zoom and pan

**Status**: Open — manual zoom is incorrect when `scale_factor > 1`
**Priority**: P1 (High)
**Severity**: Major
**Category**: Bug
**Related**: [006 — Improve zoom and image panning controls](006-improve-zoom-and-image-panning-controls.md), [002 — Interactive crop and save feature](002-interactive-crop-and-save-feature.md), implementation commit `1a1b756`

---

## 1. Problem & Motivation

The crop tool must follow the visible image across zoom and pan states. Manual zoom worked incorrectly for the ordinary `scale_factor = 1` case until `1a1b756`; that commit corrected its selected zoom scale and added pan coverage. A separate current-HEAD review found that the same mapping remains wrong for small images whose display texture has `scale_factor > 1`.

## 2. Technical Specification / Findings

- Crop boxes are source-canvas coordinates.
- Auto zoom displays `textures[current_frame]`, whose dimensions include `scale_factor`; manual zoom instead creates a texture from the source pixbuf at `source_dimension * _zoom`.
- Therefore manual source-to-widget scale is `_zoom`. Where the crop code maps through texture coordinates, its texture-to-widget scale must be `_zoom / scale_factor`, not `_zoom`.
- Current manual-zoom code uses `_zoom` as that texture scale while both crop overlay rendering and pointer-to-canvas conversion also apply `scale_factor`. With `scale_factor > 1`, the overlay and resulting crop coordinates are incorrect.
- `test_crop_drag_coordinates_follow_zoom_and_pan` covers 1x and 2.5x zoom plus horizontal/vertical pan, but fixes `scale_factor = 1`; it proves the resolved case only.
- Zoom changes during an active crop drag are also unverified. Drag offsets originate at the gesture's initial zoom and are converted using freshly read bounds, so a supported mid-drag zoom needs an explicit rebase policy and regression coverage before it can be claimed correct.

## 3. Implementation & Verification Plan

**Goal**: Use a transform that consistently converts source canvas, display texture, and widget coordinates in both auto and manual zoom modes.

1. Correct the manual-zoom transform for `scale_factor > 1` without changing source-coordinate crop storage.
2. Add regression cases at `scale_factor > 1` for a non-integer manual zoom and horizontal/vertical pan; assert both pointer-derived source bounds and rendered overlay coordinates.
3. Define and test the behavior when zoom changes during a crop interaction, or explicitly prevent that transition while a drag is active.
4. Run `make test`, `git diff --check`, and a GTK smoke test on a small PNG before closing and archiving this issue.
