<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Website: showcase zoom and pixel color picker

**Status:** Open

The 2026-07 features — cursor-centered scroll zoom, keyboard zoom towards the
last zoom center, the pixel color picker, and image background/border settings —
are now mentioned in the site subtitle and README, but the website's gallery
and feature cards have no screenshots or dedicated sections for them.

Suggested:

- Add a gallery entry (screenshot or short webm) showing scroll-zoom into a
  sprite with the color picker reading a pixel.
- Add a feature card next to "Palette Extractor" for the pixel picker.
- Note: the `codeberg.org/nautilus-spriteview` → `codeberg.org/ubunatic/spriteview`
  URL bug was fixed in the website copy in the same session this note was
  first written, but it **recurred** in `scripts/install.sh` (two more
  occurrences, undetected until an isolated-container install test in the
  2026-08-28 release session). Fixed for good in commits `7926509` and
  `f65542e`. Keep an eye out for the old URL in future copy/paste — it has
  now shown up in two different files across two sessions.
