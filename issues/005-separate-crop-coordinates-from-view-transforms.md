<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 005 — Separate crop coordinates from view transforms

**Status**: Open
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Architecture
**Related**: [004 — Crop coordinates follow zoom and pan](004-crop-coordinates-follow-zoom-and-pan.md), [Interactive crop feature](interactive_crop_feature.md)

---

## 1. Problem & Motivation

Crop state and view geometry are currently coupled through scale factors and canvas/widget coordinates in several parts of the preview and crop code. This makes zoomed cropping fragile: the overlay can appear correct while the selected source pixels or committed crop are wrong, and changes to the zoom or pan model require scattered coordinate fixes.

The source image at natural resolution must remain the source of truth. Crop bounds should stay attached to those source pixels regardless of how the image is currently displayed. The UI should translate between source-image coordinates and view coordinates only when it receives pointer input or draws the image and crop overlay. This should also let users zoom or pan while retaining a stable crop selection.

## 2. Technical Specification / Findings

- Keep crop selection and crop operations in natural-resolution source-image coordinates.
- Define a clear transform boundary between source-image coordinates and the displayed view. It must account for zoom, pan, fit-to-view scaling, and any upscaled display texture.
- Convert pointer locations and gestures from view coordinates into source coordinates before changing crop state.
- Convert the source crop bounds into view coordinates only for drawing the overlay, handles, and size label.
- Zooming and panning change the view transform, not the stored crop bounds. Cropping always reads the original-resolution image data.

## 3. Implementation & Verification Plan

**Goal**: Make crop selection independent of canvas and widget geometry by keeping its state in source-image coordinates and routing all UI interaction and rendering through explicit coordinate transforms.

### M1 — Establish the coordinate model

Identify the source-image, display-texture, preview-widget, and viewport coordinate spaces. Define one reusable forward and inverse transform boundary for the view, including how texture upscaling and fit-to-view are represented. Keep crop state expressed only in source-image coordinates.

### M2 — Route crop UI through the transform

Update crop pointer start/update, move/resize handles, overlay drawing, bounds, and size labels to use the shared transforms. Keep crop commit operating on original-resolution pixel data. Ensure zooming or panning does not rewrite crop state, and define how active gestures behave if the view transform changes mid-gesture.

### M3 — Verify view-independent crop behavior

Cover auto/fit view and manual zoom, fractional zoom, panning in both axes, display-texture upscaling, and zoom/pan after a selection. Verify source crop bounds and the resulting image dimensions and pixels, not just the visible rectangle. Add an interactive smoke check for selection, zooming into the selection, repositioning it, and committing the crop.

Keep [issue 004](004-crop-coordinates-follow-zoom-and-pan.md) focused on the immediate manual-zoom correctness bug; close it only after its acceptance criteria pass. This issue covers the broader coordinate-model cleanup and separation of concerns.
