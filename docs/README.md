<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Sprite View - Documentation Index

Welcome to the Sprite View developer and design documentation. These are "evergreen" reference files detailing development standards, architecture choices, and platform integrations.

## Index of Evergreen Documents

| Document | Description |
| :--- | :--- |
| **Feature & Architectural Docs** | |
| [Interactive_Crop_And_Save.md](file:///home/uwe/projects/spriteview/docs/Interactive_Crop_And_Save.md) | Design and pitfalls of the CropManager, gesture handling, and Save split button. |
| [GTK4.md](file:///home/uwe/projects/spriteview/docs/GTK4.md) | GTK4/PyGObject guidelines, event gesture consolidation, and uniqueness flags. |
| [In_Place_Navigation_And_Application_Uniqueness.md](file:///home/uwe/projects/spriteview/docs/In_Place_Navigation_And_Application_Uniqueness.md) | Single-instance window reuse and Nautilus integration. |
| [Focus_Management.md](file:///home/uwe/projects/spriteview/docs/Focus_Management.md) | GTK4 window presentation and focus management rules. |
| [Window_Management.md](file:///home/uwe/projects/spriteview/docs/Window_Management.md) | GTK4 application windows construction and cleanup. |
| [Nautilus_Geometry.md](file:///home/uwe/projects/spriteview/docs/Nautilus_Geometry.md) | Coordinate layouts matching Nautilus sizing behaviors. |
| **Development & Style Guidelines** | |
| [Make.md](file:///home/uwe/projects/spriteview/docs/Make.md) | Makefile structure and phony self-documentation patterns. |
| [Bash.md](file:///home/uwe/projects/spriteview/docs/Bash.md) | Shell scripting standards and smart indents. |
| [Packaging.md](file:///home/uwe/projects/spriteview/docs/Packaging.md) | Single-file script packaging workflow. |
| [Web_Design.md](file:///home/uwe/projects/spriteview/docs/Web_Design.md) | Standardized web application styles and token guidelines. |
| **Release & Distribution** | |
| [Release.md](file:///home/uwe/projects/spriteview/docs/Release.md) | Current release architecture: `harnez release`, `version.yaml`, minisign key, published assets. |
| **Case Studies** | |
| [2026-08-28-releasing-a-pure-python-project-with-goreleaser.md](file:///home/uwe/projects/spriteview/docs/studies/2026-08-28-releasing-a-pure-python-project-with-goreleaser.md) | Retrospective on standing up the GoReleaser/minisign release pipeline and the install.sh bugs it uncovered. |
| [2026-08-29-migrating-to-harnez-release.md](file:///home/uwe/projects/spriteview/docs/studies/2026-08-29-migrating-to-harnez-release.md) | Retrospective on collapsing nine release Make targets into `harnez release` and rotating the minisign key. |
