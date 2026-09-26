<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 007 — Left-button click selects pixels and drag starts crop

**Status**: Closed — resolved in 53d81b3
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Feature
**Related**: [006 — Improve zoom and image panning controls](006-improve-zoom-and-image-panning-controls.md), [002 — Interactive crop and save feature](002-interactive-crop-and-save-feature.md)

---

## 1. Problem & Motivation

The primary mouse button should support both common image-viewing tasks: a simple click should select the pixel and its color in the palette, while dragging should start a crop selection. This gives the left button a useful default action without sacrificing crop access.

## 2. Technical Specification / Findings

Distinguish a click from a drag using pointer movement and begin crop selection when the drag threshold is crossed. A click should continue to select the pixel under the pointer and update the palette color. Coordinate behavior should remain correct at every zoom level.

## 3. Implementation & Verification Plan

**Goal**: Make a left-button click select the pointed pixel and its palette color, and make a left-button drag start an interactive crop.

Verify that clicks select pixels without creating a crop, drags create and adjust a crop, and the behavior works across zoom levels without interfering with panning gestures.
