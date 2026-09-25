<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 002 — Improve zoom and image panning controls

**Status**: Open
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Feature
**Related**: [Interactive crop feature](interactive_crop_feature.md)

---

## 1. Problem & Motivation

Current zoom steps feel too large, making it difficult to choose a useful intermediate scale. Panning the image also needs a direct, discoverable gesture, especially for single-image viewing.

## 2. Technical Specification / Findings

- Add finer zoom increments while keeping zoom centered around the pointer where applicable.
- Support space + pointer drag to pan the image.
- Add a conventional mouse-button drag gesture for panning that also works with a pen/stylus.
- The mouse gesture needs a design decision: middle-click drag is a candidate; right-click drag is another. Keep left-click available for the existing or future crop interaction. Do not assume a final button mapping without checking GTK/platform conventions and crop behavior.

## 3. Implementation & Verification Plan

**Goal**: Let users make small zoom adjustments and pan the image with keyboard-modified or direct pointer gestures, including a pen/stylus.

Verify smooth zoom increments and reliable panning without breaking existing image interactions, including cropping. Record the selected mouse-button mapping and its rationale.
