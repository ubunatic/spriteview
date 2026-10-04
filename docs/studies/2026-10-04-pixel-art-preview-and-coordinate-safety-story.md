<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Making Pixel-Art Preview Safer to Use

## Context

SpriteView is a small Linux desktop image viewer for pixel artists and developers. The problem it takes on is practical: inspecting sprite sheets and image sequences needs more than opening a file. People need crisp zoom, frame playback, pixel-color inspection, and a way to crop without losing track of which source pixels they selected. SpriteView combines those tasks in a GTK4 application that can also be launched from the terminal or GNOME Files.

From 25 to 26 September 2026, the project focused on the preview interaction. The visible feature work came in a tight sequence: hide the side panel for standalone PNGs, improve zoom and panning, let a click sample a pixel while a drag begins a crop, then fix how crop geometry maps through the view. The repository records 30 commits in the six weeks through 4 October, including documentation, release maintenance, and this feature sequence. The latest release tag is v0.1.2.

## The hard part was keeping coordinates honest

Zoom makes an image easier to inspect, but it also makes pointer positions harder to interpret. A crop rectangle is meaningful in the original image’s pixel coordinates; the picture on screen may be zoomed, panned, fitted to the window, or represented by an upscaled display texture. Treating these coordinate spaces as interchangeable makes a crop look right while selecting the wrong pixels.

The project approached the problem incrementally. Commit `4e065bd` improved zoom and panning and added preview tests. Commit `53d81b3` made a left click select a pixel and a drag start a crop, with tests for both interactions. The first crop fix, `1a1b756`, handled manual zoom and pan for the ordinary scale-factor case. A follow-up review then identified a less common case: small images whose display texture had been upscaled.

That led to a useful design correction in `641c0a2`. CropManager now calculates a canvas-to-texture scale based on the active view mode: automatic view accounts for the display texture’s scale factor, while manual zoom works from the original source image and uses a scale of 1 at that boundary. Pointer input and overlay drawing use the same mapping. The test was expanded to exercise scale factors 1 and 4 at two zoom values, with pan offsets, and to check that the crop overlay dimensions still match the drag. This is a concrete example of a UI bug that a screenshot alone would miss: the rectangle can appear plausible while its source-pixel bounds are wrong.

## How the work was organized

The recent history shows a compact issues-as-tickets loop. Issues 001 and 002 were filed, implemented, and closed alongside the sidebar and zoom changes. Issues 003 and 004 tracked the click-versus-drag behavior and the first crop mapping fix. The tracker was later renumbered and standardized in `25cdfbe`; the current records 008 and 009 distinguish an immediate transform concern from a broader coordinate-model cleanup.

The project also documents its wider harnez practices: issue metadata and generated indexes, a five-phase agentic sprint loop, release automation, and engineering studies. A previous study records a delegated container install check during release work, including a follow-up that caught an incomplete validation. The current crop commit history proves issue-driven implementation and regression coverage; it does not identify which coding steps were performed by agents, so this story does not attribute the feature to a particular agent workflow.

## What this shows

Agentic development is most useful here as a way to sustain small, connected steps: make an interaction change, encode the expected behavior in tests, and leave a trail that makes follow-up problems specific. The tests do not establish every real desktop behavior—for example, the tracker still asks what should happen if zoom changes during an active crop drag—but they give the coordinate conversion a repeatable boundary to defend. Keeping that unresolved question visible is part of the engineering result, too.

For a solo developer, the scope is plausible: a focused GTK application, a few hundred lines of crop logic, and a compact test suite. The compelling evidence is not that one person could not build it. It is that thirty recent commits combine feature work, issue bookkeeping, packaging, and documentation, while 54 test methods across six test modules protect the Python project’s behavior. That volume makes careful ticket and test discipline valuable whether the implementation is written by one person or assisted by agents.

## Facts

| Item | Verified detail |
|---|---|
| Stack | Python, GTK4/PyGObject, Pillow, unittest; Linux/GNOME and Nautilus integration |
| Repository size | 4,951 lines across `sprite_view/` and `tests/`; 570 lines in preview tests |
| Test inventory | 54 `test_` methods across six test modules; tests not run for this review |
| Recent activity | 30 commits in the six weeks through 2026-10-04 |
| Interaction milestones | 2026-09-25 zoom/crop work; 2026-09-26 coordinate-transform fix |
| Release | v0.1.2 tag; the tag commit is dated 2026-09-28 |
