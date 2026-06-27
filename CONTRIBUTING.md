<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Contributing

This project is maintained in spare time. Contributions are welcome in the form of
**issues** — not direct code PRs. Please read this guide before opening anything.

## Philosophy

This app has a focused scope and must stay lightweight. Feature requests that add
complexity, dependencies, or maintenance burden without clear benefit to the core
use case will not be accepted. When in doubt: less is more.

## How to File an Issue

Issues are tracked as Markdown files in [`issues/`](issues/). There is no external
issue tracker. This keeps context, proposals, and discussion portable and
agent-friendly.

**Process:**

1. Ask your agent to check [`issues/`](issues/) and [`issues/archive/`](issues/archive/) — your idea
   may already exist or have been resolved.
2. Fork the repository.
3. Create `issues/<short-kebab-name>.md` using the template below.
4. Open a pull request containing **only that file**.
5. Discussion happens in the PR. If the issue is accepted, it stays open in
   `issues/`. If implemented or rejected, it moves to `issues/archive/`.

I do not promise to review issues or PRs on any schedule. If I find the time and
the issue fits the project's scope, I will act on it.

## Issue File Template

```markdown
<!-- SPDX-FileCopyrightText: <year> <Your Name> -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Issue: <Short Title>

## Summary
One or two sentences describing the problem or missing capability.

## Motivation
Why does this matter? Who benefits? What is the current workaround, if any?

## Proposed Solution
What should change? Keep it concrete. UI mockups, CLI flags, or pseudocode are welcome.

## Alternatives Considered
What else was considered and why it was ruled out.
```

## Coding Conventions

All code in this project follows documented conventions. Read them before submitting
anything that touches code.

- **Bash / Shell** — [`docs/Bash.md`](docs/Bash.md)
- **Make / Makefile** — [`docs/Make.md`](docs/Make.md)
- **GTK4 / GObject / Python** — [`AGENTS.md`](AGENTS.md)

Key rules to know upfront:
- Bash: always `if test`, never `[ ]` or `[[ ]]`; no semicolons; `then`/`else`/`do` on their own line
- Make: phony sentinel `⚙️`, self-documenting help, build dependency pattern
- GTK4: use `NON_UNIQUE` application flags; no blocking main loops; run integration smoke tests

## License

All contributions must be licensed under `AGPL-3.0-or-later` and include
`SPDX-FileCopyrightText` and `SPDX-License-Identifier` headers. Run `reuse lint`
to verify before submitting.

