<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# scripts/install.sh: no Pillow (PIL) dependency check

**Status:** Open

`sprite_view/ui/preview.py` and `sprite_view/ui/crop.py` both have an
unconditional top-level `from PIL import Image` — Pillow is a hard runtime
dependency for interactive crop and some export paths, but until the
2026-08-29 evergreen pass it was undocumented in the README, and
`scripts/install.sh` never checks for it the way it already checks for
(and can offer to install) `python3-nautilus`.

Found during the 2026-08-28 release session while investigating why the
documented one-line installer failed in an isolated container; deliberately
left unfixed at the time as out of scope for that session.

## Fixed so far

- README's Prerequisites section now documents the Pillow requirement and
  per-distro install commands (`python3-pil` / `python3-pillow` /
  `python-pillow`).

## Still open

`scripts/install.sh` has no equivalent check/offer-to-install step for
Pillow the way it does for `python3-nautilus` (see the `has_pkg_installed`
block near the top of the script). A user without Pillow preinstalled
gets a working install and then an `ImportError` the first time they try
to crop or export — not caught until runtime, not at install time.

## Suggested fix

Add a Pillow presence check (`python3 -c "import PIL"` is simpler and more
portable than per-package-manager `dpkg-query`/`rpm`/`pacman` checks, since
Pillow's package name differs per distro) to `scripts/install.sh`,
following the same "detect → offer to install via sudo, or warn" pattern
already used for `python3-nautilus`.
