<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# 004 — Check for Pillow during installation

**Status**: Open
**Priority**: P2 (Medium)
**Severity**: Moderate
**Category**: Infrastructure
**Related**: [Packaging documentation](../docs/Packaging.md)

---

## 1. Problem & Motivation

Pillow is a hard runtime dependency for interactive crop and some export paths. `scripts/install.sh` checks for `python3-nautilus`, but does not check for Pillow. A user can complete installation and then encounter an `ImportError` when using those features.

The README prerequisites were updated with Pillow and per-distribution package names, but the installer check remains outstanding.

## 2. Technical Specification / Findings

- `sprite_view/ui/preview.py` and `sprite_view/ui/crop.py` import `PIL.Image` at module load time.
- Package names differ by distribution, so checking `python3 -c 'import PIL'` may be simpler and more portable than package-manager-specific queries.
- Follow the install script's existing detect, offer-to-install, or warn behavior for `python3-nautilus`.

## 3. Implementation & Verification Plan

Add an installer-time Pillow check and a clear remediation message. Verify behavior with Pillow present and absent, including the installer's existing user choice and privilege flow.
