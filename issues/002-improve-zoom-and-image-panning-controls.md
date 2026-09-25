<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 002 — Improve zoom and image panning controls

**Status**: Closed — resolved in 4e065bd
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Feature
**Related**: [Interactive crop feature](interactive_crop_feature.md), implementation commit `4e065bd`

---

## 1. Problem & Motivation

Current zoom steps feel too large, making it difficult to choose a useful intermediate scale. Panning the image also needs a direct, discoverable gesture, especially for single-image viewing.

## 2. Technical Specification / Findings

- Add finer zoom increments while keeping zoom centered around the pointer where applicable.
- Support space + pointer drag to pan the image.
- Support middle-button drag and right-button drag for panning. Middle drag is the conventional canvas-pan gesture in image editors; right drag is included for stylus barrel buttons that commonly map to secondary click. Left drag remains available to crop mode.
- The pan gesture is filtered by button and space-key state, so ordinary left clicks and crop drags are not claimed by panning.

## 3. Implementation & Verification Plan

**Goal**: Let users make small zoom adjustments and pan the image with keyboard-modified or direct pointer gestures, including a pen/stylus.

Verify finer zoom increments and reliable panning without breaking existing image interactions, including cropping. The selected gestures are space + left drag, middle drag, and right drag.
