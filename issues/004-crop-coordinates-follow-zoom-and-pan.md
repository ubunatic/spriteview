<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 004 — Crop coordinates follow zoom and pan

**Status**: Open
**Priority**: P1 (High)
**Severity**: Major
**Category**: Bug
**Related**: [002 — Improve zoom and image panning controls](002-improve-zoom-and-image-panning-controls.md), [Interactive crop feature](interactive_crop_feature.md)

---

## 1. Problem & Motivation

The crop tool does not correctly follow the image when the preview is zoomed. Its selection coordinates appear offset or constrained to a fixed area, especially after zooming, so users cannot reliably crop the visible image region.

## 2. Technical Specification / Findings

Crop pointer positions, selection bounds, and image coordinates must use the same zoom and pan transform as the displayed image. Keep crop selection aligned when zoom changes and when the image has been panned.

## 3. Implementation & Verification Plan

**Goal**: Make crop selection track the displayed image correctly at all zoom levels and after zooming or panning.

Verify crop bounds against source-image coordinates at multiple zoom levels and pan offsets, including changing zoom before and during a crop interaction where supported.
