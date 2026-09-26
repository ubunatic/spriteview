<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Releasing a Pure-Python Project with GoReleaser

## 1. Header & Context

- **Date:** 2026-08-28
- **Scope:** Stand up a signed, reproducible release pipeline for SpriteView
  (a pure-Python, single-file-packed GTK4/Nautilus extension) reusing the
  `.goreleaser.yaml` pattern from sibling Go/Zig projects (`uman`,
  `emojig`), publish v0.1.0 to Codeberg, and update the website/installer to
  match.
- **Starting state:** No release tooling in the repo. `.goreleaser.yaml`
  had been copied verbatim from `../uman` (a Go project) and did not work.
  No Makefile release targets. `scripts/install.sh` had never been
  exercised against a real, isolated environment.
- **Intended goals:**
  1. Adapt GoReleaser to a project with no compiled build step.
  2. Add matching `make release-*` targets, mirroring this repo's existing
     Make/Bash conventions (`if test`, no `[[`, no `;`).
  3. Get minisign signing working and cut v0.1.0.
  4. Update `website/index.html` to document the new signed-release option.
  5. Validate the documented install path end-to-end in an isolated
     container, not just by reading the script.

## 2. Executive Summary

v0.1.0 shipped: tag, `main`, and all three release assets
(`spriteview-0.1.0.tar.gz`, `SHA256SUMS`, `SHA256SUMS.minisig`) now agree on
commit `3f882af`. The website documents the signed-tarball install path
(commit `78ccfa4`), and the corresponding page was synced to
`ubunatic.com` (commit `e0cfbbe`, not yet pushed there).

More important than the release itself: an isolated podman-based install
test caught that the project's **primary, documented install method**
(`curl | bash`) was completely broken for any new user — wrong Codeberg
org in two places, and a fallback path that fetched an unpacked Python
module that cannot run standalone. Both were real, pre-existing production
bugs, not introduced this session, and neither would have surfaced from
static review alone.

## 3. What Worked Well

- **Reusing sibling-project prior art was the right instinct**, even
  though the Go-shaped config needed real rework — the `builds:`/`archives:`/
  `checksum:`/`signs:`/`changelog:` skeleton, the minisign key sharing
  (`~/.minisign/minisign.key`, same key ID across `uman`/`emojig`/
  `spriteview`), and the Makefile target *names* all transferred cleanly.
  Only the build step itself needed to change shape.
- **`meta: true` GoReleaser archives** turned out to be the correct
  primitive for "pack arbitrary files, no compiled build" — once found,
  the rest of the pipeline (checksum, sign, changelog, publish) worked
  unmodified against a Go-oriented tool.
- **Isolated container validation caught two bugs that code review had
  already missed twice** (the org-name bug had reportedly been "fixed"
  once before per `issues/003-showcase-zoom-and-pixel-color-picker-on-the-website.md`, in the website
  copy only — it had silently regressed into `scripts/install.sh`).
  Running the actual documented one-liner against a clean podman container
  is what surfaced it, not re-reading the script.
- **AskUserQuestion before each push** kept every remote-visible action
  (tag force-move, two install.sh fixes, website docs) opt-in — no
  surprise pushes to the public Codeberg repo.
- **Matching this repo's existing Bash/Make style** (`if test`, `&&`/`||`
  chains instead of `[[`) when fixing the Makefile's broken `if/then` kept
  the fix consistent with the rest of the file instead of introducing a
  second idiom.

## 4. Honest Post-Mortem (Failures, Bugs & Near-Misses)

- **GoReleaser OSS has no `prebuilt` builder.** The first `.goreleaser.yaml`
  draft assumed one existed (it's Pro-only). Caught by
  `goreleaser jsonschema` rejecting the config
  (`field prebuilt not found in type config.Build`). Fixed by using
  `builds: [{skip: true}]` plus a `meta: true` archive instead.
- **`builds: []` (empty list) is not "no build."** It silently falls back
  to GoReleaser's Go build defaults and failed with
  `build for spriteview does not contain a main function` for a
  `windows_arm64_v8.0` target — a confusing error for a Python project with
  no Go anywhere in it. Fixed with an explicit `builds: [{skip: true}]`.
  **This is a sharp edge worth remembering**: an empty list and "skip" are
  not equivalent in GoReleaser's schema.
- **GoReleaser requires `dist/` to be empty after `before.hooks` run.**
  The pack step naturally wants to leave its output in `dist/`, which then
  collided with GoReleaser's own dist management
  (`error=dist is not empty, remove it before running goreleaser`). Fixed
  by staging the packed file to a separate `.goreleaser-src/` directory and
  `rm -rf dist` at the end of the hook, letting GoReleaser own `dist/`
  exclusively.
- **Makefile `if/then/else` broke across backslash-continued recipe
  lines.** A naive port of a multi-line confirmation prompt produced a real
  shell syntax error (`unexpected end of file from 'if' command`) because
  backslash-newline continuation strips the newline that POSIX shell
  grammar needs between `if ...` and `then`. Reproduced in a throwaway
  `/tmp` Makefile before fixing; the fix was to restructure as an
  `&&`/`||` chain, matching this repo's own established Bash-convention
  style rather than reaching for `[[`.
- **`$(wildcard ...)` caches a stale directory listing.** `_dist_files`
  used `$(wildcard dist/*.tar.gz ...)`, which GNU Make expands once and
  caches from *before* the release recipe runs — so a file created mid-recipe
  (`SHA256SUMS.minisig`, produced by the `minisign` step) was silently
  missing from the list passed to `fj release create --attach`. This
  shipped a real, incomplete first release: the published v0.1.0 release
  was missing its `.minisig` asset. Root-caused by tracing Make's
  expansion-time semantics, fixed with `$(shell ls ...)` (commit
  `3f882af`), and the missing asset was patched onto the already-published
  release out-of-band via `fj release asset create`.
- **Tag pointed at the wrong commit.** `make release-publish` failed with
  `tag v0.1.0 was not made against commit ...`. Root cause was manual
  tagging done before the last fixup commit landed. Resolved via
  `git tag -f -a v0.1.0 -m "spriteview v0.1.0" <commit>` after explicit
  user confirmation (AskUserQuestion) since force-moving a tag is a
  destructive, non-default action.
- **Codeberg/Forgejo does not support GitHub's `/releases/latest/download/<file>`
  URL shape.** It 404s. The Makefile's `VERSION_PUBLISHED` lookup and
  `scripts/install.sh`'s tarball fetch both had to go through
  `/repos/{owner}/{repo}/releases/latest` (JSON) or the explicit
  `/releases/download/{tag}/{file}` form instead.
- **The documented one-line installer was broken for every new user**,
  found only via isolated podman testing, not static review:
  - `scripts/install.sh` pointed at `codeberg.org/nautilus-spriteview/...`
    instead of `codeberg.org/ubunatic/spriteview/...` in two places, and
    its `curl -sSL` calls lacked `-f`, so an HTTP error page got silently
    written to disk and treated as success. Fixed in `7926509`.
  - Even after that fix, the curl fallback path (the one always taken by
    `curl | bash`, since there's no local `dist/` or checked-out repo)
    downloaded the **raw, unpacked** `sprite_view.py` — a file with no
    shebang that imports from a sibling `sprite_view/` package that was
    never fetched. It could not run standalone. This was only caught
    because I ran `spriteview --help` inside the container *after*
    applying the first fix and it failed — a background fork agent's
    fix-validation pass had not gone that deep. Fixed in `f65542e` by
    resolving the latest release via the Codeberg API and extracting the
    packed, self-contained `spriteview` script from the release tarball
    instead.
  - `issues/003-showcase-zoom-and-pixel-color-picker-on-the-website.md` had already recorded the
    org-name bug as fixed once — in the website copy only. It quietly
    regressed into `scripts/install.sh` and was not caught until this
    session. **That issue file still needs updating** to reflect the
    actual fix commits (`7926509`, `f65542e`) — flagged, not yet done.
- **Near-miss, not a bug:** Pillow (`python3-pil`) is a hard, unconditional
  runtime import (`sprite_view/ui/preview.py`, `sprite_view/ui/crop.py`)
  but is undocumented in the README's Prerequisites section. Noticed
  during install-script investigation, deliberately left unfixed as
  out-of-scope for this session.
- **Process near-miss, not a bug:** minisign signing requires an
  interactive password prompt, which cannot run inside a non-interactive
  tool call. The user's "maybe the password is empty" theory was tested
  directly (`printf '\n' | minisign -S ...` → "Wrong password for that
  key") and disproven rather than assumed, avoiding a wasted retry loop.

## 5. Quality & Invariants Audit

| Dimension | Assessment |
| :--- | :--- |
| Architecture & module separation | GoReleaser build step cleanly separated from the pack step via `.goreleaser-src/` staging; release Makefile targets (`release-build`, `release-snapshot`, `release-publish`, `release`, `release-full`) compose rather than duplicate logic. |
| Idempotency | `make release-publish` is not safely re-runnable against an existing tag/release without manual cleanup (Forgejo `fj release create` has no documented upsert) — not exercised twice this session, worth verifying before v0.1.1. |
| Backward compatibility | No prior release existed, so no compatibility surface was broken. `scripts/install.sh` fixes are net-additive/corrective, not behavior changes for anyone relying on the old (broken) behavior. |
| Test coverage & verification | `make test` (py_compile + unittest + `reuse lint`) passed throughout. Release pipeline verified via `goreleaser release --snapshot --clean --skip=sign,publish` before any real publish. Install path verified live via podman (bind-mount blocked by SELinux; worked around with `podman cp` + `podman exec`), both by a fork agent and by direct follow-up testing after the agent's report turned out to be incomplete. All 4 external links added to `website/index.html` verified HTTP 200; HTML tags verified balanced. |

## 6. Efficiency & Velocity Assessment

- The GoReleaser adaptation took multiple iterations (prebuilt builder →
  empty builds fallback → dist-not-empty → meta archive format) before
  converging — each failure was a distinct, non-obvious GoReleaser schema
  edge case rather than a repeated mistake, so iteration count reflects
  genuine unfamiliarity with GoReleaser's OSS/Pro feature boundary rather
  than thrashing.
  The `$(wildcard)` Make bug and the backslash/if-then Make bug were both
  reproduced in isolation (`/tmp` scratch Makefiles) before being fixed in
  place — cheap to verify, avoided guessing.
- Delegating the isolated-container install test to a background fork
  agent parallelized well: it ran independently while other release work
  continued, and its report directly identified one real bug (org name).
  Its validation depth was shallower than a full run (it didn't get as far
  as actually invoking `spriteview --help`), so a second, direct pass was
  still needed — worth noting as a limit on how far to trust a single
  agent's "fix validated" claim for multi-stage install flows.
- **User-reported friction:** too many individual `git push` confirmations
  were requested in quick succession (tag fix, org-name fix, deeper
  install.sh fix, website docs — 4 separate AskUserQuestion gates). Given
  each was a low-risk push to an already-authorized-for-this-session
  remote, and the user had already said "yes" to the same class of action
  repeatedly, batching these into fewer confirmation points (or trusting
  the established pattern after the first explicit yes) would have been
  less disruptive without meaningfully increasing risk.

## 7. Key Learnings & Evergreen Upstream

Candidates for `docs/Make.md`, a future `docs/Release.md`, or `AGENTS.md`:

1. **GoReleaser: `builds: [{skip: true}]`, never `builds: []`**, for
   non-compiled/meta-only releases — the empty list silently falls back to
   Go build defaults and fails on an unrelated target.
2. **GoReleaser: stage packed artifacts outside `dist/`** (e.g.
   `.goreleaser-src/`) in `before.hooks`, then clear `dist/` — GoReleaser
   owns that directory exclusively and errors if it's non-empty when it
   starts.
3. **Make: never use `$(wildcard ...)` for files a recipe creates in the
   same run** — it caches the directory listing at expansion time, before
   the recipe body executes. Use `$(shell ls ... 2>/dev/null)` for
   freshly-generated files.
4. **Make: don't spread `if/then/else` across backslash-continued recipe
   lines** — continuation strips the newline POSIX shell needs before
   `then`. Use `&&`/`||` chains instead, consistent with this repo's
   existing `if test` convention.
5. **Codeberg/Forgejo release URLs have no `/latest/download/<file>`
   alias** (unlike GitHub) — resolve the latest tag via the JSON API
   (`/repos/{owner}/{repo}/releases/latest`) first, then build an explicit
   `/releases/download/{tag}/{file}` URL.
6. **A packed/single-file distribution needs its own explicit
   "unpacked source cannot run standalone" fallback-of-last-resort
   guard** in installer scripts — a raw source fetch that "looks like it
   should work" (same filename, right repo) can still be silently
   non-functional if it depends on sibling files or a shebang that only
   exist in the packed build.
7. **Validate documented install instructions in a genuinely isolated
   environment before publishing them**, not just by reading the script —
   this is the one check that actually caught the release-blocking bugs
   here, and a prior "fix" recorded in `issues/` had already regressed
   silently once without that check.
8. **Batch or reduce push-confirmation prompts once a pattern of approval
   is established within a session** — repeated low-risk pushes to the
   same already-authorized remote don't each need a fresh gate.

## 8. File & Diff Summary

Commits on `spriteview` `main`, oldest to newest (`869b1ad..78ccfa4`):

| Commit | Summary | Files |
| :--- | :--- | :--- |
| `869b1ad` | build: add GoReleaser config and release Makefile targets | `.goreleaser.yaml` (new), `Makefile`, `.gitignore` |
| `effcaa0` | add release sign | `REUSE.toml`, `minisign.pub` (new) |
| `3f882af` | fix(release): use `$(shell ls)` instead of `$(wildcard)` for `_dist_files` | `Makefile` (+4/-1) |
| `7926509` | fix(install): correct wrong Codeberg org and add `curl -f` to install.sh | `scripts/install.sh` (+4/-4) |
| `f65542e` | fix(install): fetch the packed release script, not raw unpacked source | `scripts/install.sh` (+21/-4) |
| `78ccfa4` | docs(website): document the signed release tarball as an install option | `website/index.html` (+12) |

Also, in `~/projects/ubunatic.com` (separate repo, synced via
`uman website sync spriteview`):

| Commit | Summary | Files | Status |
| :--- | :--- | :--- | :--- |
| `e0cfbbe` | chore: sync website — spriteview signed-release install docs | `spriteview/index.html` (+12) | committed, **not pushed** |

Release artifacts published to Codeberg (`v0.1.0`, commit `3f882af`):
`spriteview-0.1.0.tar.gz`, `SHA256SUMS`, `SHA256SUMS.minisig`.

**Not yet done, carried forward:**
- Update `issues/003-showcase-zoom-and-pixel-color-picker-on-the-website.md` to reflect that the
  org-name bug recurred in `scripts/install.sh` and was fixed in
  `7926509`/`f65542e`.
- Decide on documenting/enforcing the undocumented Pillow dependency.
- Push `e0cfbbe` in `ubunatic.com` (pending user go-ahead); unrelated
  pre-existing uncommitted `experiments/traffic-sim/*` changes in that repo
  were left untouched throughout.
- Consider whether `main`'s post-release install.sh fixes (`78ccfa4`)
  warrant a v0.1.1 tag, even though the existing v0.1.0 release *assets*
  themselves are unaffected by the installer-script bugs.
