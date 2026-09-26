<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 005 — Hide side panel for standalone PNGs

**Status**: Closed — resolved in 1475fef
**Priority**: P2 (Medium)
**Severity**: Minor
**Category**: Feature
**Related**: `1475fef` — implementation

---

## 1. Problem & Motivation

When Sprite View opens a static PNG and finds no neighboring sprite frames, the side panel still takes space even though the frame navigation and related controls are not useful. The panel also needs a way to collapse when a user wants more room for the image.

## 2. Technical Specification / Findings

- Hide the side panel by default when the opened PNG has no detected neighboring frames.
- Make the side panel collapsible so users can show or hide it manually.
- Preserve the panel for detected sprite sequences.

## 3. Implementation & Verification Plan

**Goal**: Give standalone PNGs the full preview area by default while allowing users to collapse or reopen the side panel.

Verify behavior for a standalone PNG, a PNG with detected neighboring frames, and manual collapse/reopen.
