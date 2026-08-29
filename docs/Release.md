<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Release Architecture

How SpriteView releases work today. For the history of how we got here —
including bugs found and fixed along the way — see `docs/studies/`:
`2026-08-28-releasing-a-pure-python-project-with-goreleaser.md` (the
original GoReleaser/minisign setup and the `scripts/install.sh` bugs it
uncovered) and `2026-08-29-migrating-to-harnez-release.md` (collapsing
that setup into `harnez release`).

## The one command

```bash
make release
```

which is:

```makefile
release: test ⚙️  ## release the project using harnez
	harnez release
```

`harnez` (a sibling CLI, `codeberg.org/ubunatic/harnez`) owns the entire
release lifecycle. SpriteView contributes no release-specific Make targets
beyond this one recipe and `clean` (purges `dist/` and `.goreleaser-src/`).
Do not add `release-*`, `deps`, `info`, or similar targets back — that's
exactly the sprawl this setup replaced. If `harnez release` can't do
something SpriteView needs, extend `harnez`, don't route around it here.

Full reference for what `harnez release` does and how to set it up in a
new repo: `docs/practices/GoRelease.md` in the `harnez` repo (bundled here
optionally via `harnez init --docs gorelease`, not currently checked into
this repo's `docs/`).

## Source of truth: `version.yaml`

```yaml
# yaml-language-server: $schema=spec/schemas/version.schema.json
version: 0.1.1
```

Committed at the repo root. `harnez release` reads it, bumps it
(`--bump patch|minor|major|<semver>`, default `patch`), and would sync the
new version into a language-native version file if one existed — it
doesn't here. SpriteView has no version constant anywhere in
`sprite_view.py` or the packed script; `version.yaml` plus the git tag it
produces (`vX.Y.Z`) are the only version records. Don't add a Python
`__version__` unless something actually needs to read it at runtime — it
would just be a second thing to keep in sync with `version.yaml`.

`version.yaml` is REUSE-annotated in `REUSE.toml` like every other
non-`.py` root file — `reuse lint` (run by `make test`, which `release`
depends on) fails otherwise.

## Build step: `.goreleaser.yaml`

SpriteView has no compiled build. `.goreleaser.yaml` uses `builds: [{skip:
true}]` (GoReleaser OSS has no "prebuilt binary" builder) plus a `meta:
true` archive that packs arbitrary files without a build step. A
`before.hooks` block runs `make pack` (the same packer `make install`
uses), stages the packed `dist/sprite_view.py` to `.goreleaser-src/spriteview`
(outside `dist/`, which GoReleaser requires empty when it starts), then
clears `dist/`. `harnez release` invokes this with
`goreleaser release --clean --skip=publish --skip=sign` — the same
artifact-build step Go/Zig/Rust sibling projects use, just against a
config that skips compiling.

There is deliberately **no `signs:` block** in `.goreleaser.yaml`. Signing
is `harnez release`'s job (next section); a `signs:` block here would be
dead config that could confuse someone into thinking GoReleaser handles
signing.

## Signing: a dedicated, passwordless minisign key

`harnez release` signs `dist/SHA256SUMS` directly (not via GoReleaser)
using `~/.minisign/spriteview.key` — a key generated specifically for this
project with `minisign -G -W -f -p ~/.minisign/spriteview.pub -s
~/.minisign/spriteview.key` (`-W` = no password, required because
`harnez release` signs non-interactively). This is **not** the shared
`~/.minisign/minisign.key` used by `uman`/`emojig` — that key is
password-protected and can't sign non-interactively, and rotating to a
per-project key was a deliberate, one-time choice made when adopting
`harnez release` (see the 2026-08-29 study for the full rationale).

The repo's committed `minisign.pub` holds this project-specific key's
public half. **Consequence:** `v0.1.0`'s release assets — signed under the
old shared key before the rotation — are no longer verifiable against the
`minisign.pub` in this repo. Every release from `v0.1.1` onward verifies
against the current `minisign.pub`. If the key is ever rotated again,
note it here and in a dated study doc, the same way.

## What gets published

Three assets per release, attached via `fj release create` to a Codeberg
release tagged `vX.Y.Z`:

- `spriteview-X.Y.Z.tar.gz` — packed `spriteview` script, `LICENSES/*`,
  `README.md`, `spriteview.desktop`
- `SHA256SUMS`
- `SHA256SUMS.minisig`

Verify a downloaded release:

```bash
minisign -V -p minisign.pub -m SHA256SUMS
sha256sum -c SHA256SUMS
```

`website/index.html`'s install section documents this as the alternative
to the `curl | bash` one-liner (see "Install SpriteView" under
Installation Steps) — it references `minisign.pub` by file, not by
fingerprint, so a future key rotation needs no website wording change,
just the file content swap described above.

## If a release fails partway

Don't force-move or delete the tag. Use `harnez release --continue` to
resume without re-bumping the version or re-tagging. Only cut a fresh
patch release (`harnez release` again, which defaults to `--bump patch`)
if the failure was caused by a real bug in SpriteView's own config (fix
it, commit, then release again) rather than a transient network/forge
error.
