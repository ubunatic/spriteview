<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 010 — Correct stale crop issue status and index

**Status**: Open
**Priority**: P2 (Medium)
**Severity**: Minor
**Category**: Documentation
**Related**: [008 — Crop coordinates follow zoom and pan](008-crop-coordinates-follow-zoom-and-pan.md), [009 — Separate crop coordinates from view transforms](009-separate-crop-coordinates-from-view-transforms.md), commits `641c0a2` and `25cdfbe`

---

## 1. Problem & Motivation

Issue 008 and the issue index still say manual-zoom crop coordinates are incorrect for `scale_factor > 1`. Commit `641c0a2` changed the transform and added tests for scale factors 1 and 4, so this description and its P1 priority no longer match current code. Issue 008 also includes an unverified mid-drag zoom concern, which may remain relevant. The index does not include the exact nuance of the issue body and makes the stale claim appear current.

## 2. Technical Specification / Findings

- `sprite_view/ui/crop.py` now sets `canvas_to_texture_scale` to `1.0` in manual zoom and `win.scale_factor` in auto zoom.
- `tests/test_preview.py::test_crop_drag_coordinates_follow_zoom_and_pan` exercises scale factors 1 and 4 with zoom and panning, and checks crop overlay dimensions.
- Commit `641c0a2` introduced that implementation and coverage. Commit `25cdfbe` created the currently numbered issue record with the old claim that this defect persists.
- Issue 009 tracks broader separation of crop coordinates from view transforms and should remain open independently.

## 3. Implementation & Verification Plan

Update issue 008's status, priority, findings, and verification plan to reflect the fix in `641c0a2`; keep any still-valid mid-gesture zoom question distinct and open until verified. Regenerate `issues/README.md` with `harnez index`, then check the index against all issue headers and linked statuses.
