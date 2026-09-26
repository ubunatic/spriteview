<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 001 — Advanced export options

**Status**: Draft
**Priority**: P2 (Medium)
**Severity**: Minor
**Category**: Feature
**Related**: —

---

## 1. Problem & Motivation

Sprite View's export workflow could offer more control over output scale and color palettes for pixel art, animations, and terminal graphics.

## 2. Technical Specification / Findings

- Offer original, 2x, 4x, 8x, and custom scaling options.
- Provide nearest-neighbor and bilinear resampling choices; nearest-neighbor should remain the pixel-art-friendly default.
- Support palette reduction to common color limits from 2 through 256 colors.
- For animations, optionally derive one shared palette across all frames and quantize each frame against it.
- Consider mapping colors to the ANSI 256-color palette, independently per frame or with a shared subset.
- The existing `rgb_to_ansi` logic in `sprite_view/utils.py` may be reusable; confirm its behavior before relying on it.

## 3. Implementation & Verification Plan

Design an export options dialog and define how these options interact with supported image formats and animation export. Then implement selected options and verify scaling, palette limits, shared animation palettes, and ANSI color mapping on representative images.
