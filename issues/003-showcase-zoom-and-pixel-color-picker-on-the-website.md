<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 003 — Showcase zoom and pixel color picker on the website

**Status**: Open
**Priority**: P3 (Low)
**Severity**: Minor
**Category**: Documentation
**Related**: —

---

## 1. Problem & Motivation

The website and README mention cursor-centered scroll zoom, keyboard zoom around the last zoom center, the pixel color picker, and image background and border settings. The website gallery and feature cards do not yet show these capabilities.

## 2. Technical Specification / Findings

- Add a gallery screenshot or short video showing zoom into a sprite and the pixel color picker reading a pixel.
- Add a feature card for the pixel picker near the existing “Palette Extractor” card.
- The old `nautilus-spriteview` Codeberg URL previously recurred in website copy and `scripts/install.sh`; commits `7926509` and `f65542e` fixed the known occurrences. Check current copy for regressions while updating the site.

## 3. Implementation & Verification Plan

Update the website gallery and feature cards with suitable, current visuals and copy. Verify the resulting page locally and check that project links use the current repository URL.
