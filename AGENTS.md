<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- claudeconfig:begin Language Conventions -->
Adhere to the following conventions.

- Bash/Shell @docs/Bash.md,
  No ";", break before then/else/docs
  No "if [[]]", No "if []", Use "if test"
  smart indent!
- Make/Makefile @docs/Make.md,
  ⚙️ phony sentinel, self-doc help, build dependency pattern
- GTK4 / GObject UI
  - Use NON_UNIQUE application flags to prevent background instances from swallowing CLI files.
  - Run integration smoke tests (test_integration.py) to catch Gtk startup crashes/AttributeErrors.
<!-- claudeconfig:end Language Conventions -->
