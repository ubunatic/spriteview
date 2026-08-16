<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- harnez:begin Language Conventions -->
Adhere to the following conventions.

Docs in `./docs/` are managed by harnez. <!-- harnez:bundled -->

- Bash/Shell @docs/Bash.md,
  No ";", break before then/else/docs
  No "if [[]]", No "if []", Use "if test"
  smart indent!
- Make/Makefile @docs/Make.md,
  ⚙️ phony sentinel, self-doc help, build dependency pattern
- Markdown @docs/Markdown.md,
  PascalCase for evergreens, kebab-case for ephemeral docs
- Git @docs/Git.md,
  conventional commits, work on the default branch, don't push unless asked
- Canary-first development @docs/Canary.md,
  probe external mechanisms before building features on them
- Spec system @docs/Spec.md,
  YAML spec files as single source of truth; Go code must not duplicate spec values
<!-- harnez:end Language Conventions -->
