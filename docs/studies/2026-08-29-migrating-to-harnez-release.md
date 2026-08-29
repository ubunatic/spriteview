<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Migrating to `harnez release` and Rotating the Signing Key

## 1. Header & Context

- **Date:** 2026-08-29
- **Scope:** Replace SpriteView's hand-rolled release Make targets with the
  workspace-wide `harnez release` convention, and cut v0.1.1 through it.
- **Starting state:** The v0.1.0 pipeline described in
  `2026-08-28-releasing-a-pure-python-project-with-goreleaser.md` — nine
  release-related Make targets (`deps`, `test-minisign`, `release-build`,
  `release-snapshot`, `info`, `release-diff`, `release-publish`, `release`,
  `release-full`), signing via GoReleaser's `signs:` block against the
  shared `~/.minisign/minisign.key`, publishing via a hand-written `fj`
  invocation, and manual `git tag -a vX.Y.Z` with no version file at all.
- **Goal:** One thin target, no duplicated release logic, same three signed
  assets on Codeberg.

## 2. What Changed

```makefile
release: test ⚙️  ## release the project using harnez
	harnez release
```

That recipe replaced all nine targets. `harnez release` bumps `version.yaml`,
syncs language version files (none here — SpriteView carries no version
constant, so `version.yaml` alone is the source of truth), commits, tags,
runs GoReleaser, signs, pushes, and publishes.

Two smaller cleanups fell out of it:

- **`.goreleaser.yaml`'s `signs:` block was dead config.** `harnez` invokes
  `goreleaser release --clean --skip=publish --skip=sign` and then signs
  `dist/SHA256SUMS` itself. The block had been silently unused from the
  moment harnez took over; deleting it removed the misleading
  `MINISIGN_PASSWORD` fallback branch along with it.
- **`version.yaml` was committed up front**, even though `harnez` creates it
  on first run. Creating it mid-release would have left an unannotated file
  in a repo whose `make test` runs `reuse lint`, so the *next* release would
  have failed on license compliance. It is annotated in `REUSE.toml`
  alongside `minisign.pub`.

The rest of `.goreleaser.yaml` — `builds: [{skip: true}]`, the `meta: true`
tar.gz archive, the `before.hooks` that stage `make pack`'s output into
`.goreleaser-src/` — carried over untouched. The pure-Python packaging
pattern needed no adaptation to run under harnez.

## 3. The Key Rotation

The one genuine blocker. `harnez release` verifies the signing key by
signing a scratch file **non-interactively** — it pipes no password. The
shared `~/.minisign/minisign.key` (used by `uman` and `emojig`, and used to
sign v0.1.0) is password-protected, so that check fails outright with
"Wrong password for that key".

The fix is a dedicated passwordless key, which harnez resolves automatically
by project directory name:

```bash
minisign -G -W -f -p ~/.minisign/spriteview.pub -s ~/.minisign/spriteview.key
```

Resolution order is `--sign-key` → `~/.minisign/<project>.key` → a
repo-local key file → `~/.minisign/minisign.key`. Dropping the new key in
the second slot was the whole of the configuration.

`minisign.pub` in the repo root was then replaced with the new public half:
`1C74BCC980A2790A` → `3A6C8E023E9F31B1`.

**The consequence is worth stating plainly:** v0.1.0's published assets stay
verifiable only with the old shared key, which is no longer the one in this
repo. From v0.1.1 on, the committed `minisign.pub` verifies releases. This
is a one-time cost of moving off a shared key, and it is invisible to the
documented install flow only because the website's instructions reference
`minisign.pub` *as a file* (fetched from the main branch) rather than
pinning a fingerprint — so they needed no change. Had they quoted the key
ID, the rotation would have been a website change too.

## 4. Result

`harnez release --dry-run` previewed correctly, and the real run completed
in one pass with no `--continue` recovery needed:

- Tag: [v0.1.1](https://codeberg.org/ubunatic/spriteview/releases/tag/v0.1.1)
- Assets: `spriteview-0.1.1.tar.gz`, `SHA256SUMS`, `SHA256SUMS.minisig`

Verified against the pubkey fetched from the repo's main branch — i.e. the
exact URL the website tells users to use:

```
minisign -V -p minisign.pub -m SHA256SUMS
→ Signature and comment signature verified
  Trusted comment: spriteview 0.1.1
```

## 5. Takeaways

1. **Non-interactivity is a key *property*, not a key *setting*.** A
   password-protected key cannot be retrofitted into an automated pipeline
   without either storing the password or rotating. Generating release keys
   with `-W` from the start avoids the migration entirely.
2. **Per-project keys beat one shared key** for exactly this reason: rotating
   one project's key should not touch another's, and harnez's
   `~/.minisign/<project>.key` lookup makes the per-project key the path of
   least resistance.
3. **Reference keys by file, not by fingerprint, in install docs.** It cost
   nothing here and saved a documentation change during rotation.
4. **A shared tool absorbing a pattern is a chance to delete, not to
   wrap.** The temptation was to keep `info`/`release-diff` as conveniences.
   They went; `harnez release --dry-run` and `git log` cover them, and the
   Makefile is now ~60 lines shorter with one release target instead of nine.
