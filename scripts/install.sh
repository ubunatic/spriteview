#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail


pass() {
   echo "  PASS: $*" >&2
}

fail() {
   echo "  FAIL: $*" >&2
   exit 1
}

extension_name="nautilus_preview.py"
user_ext_dir="${HOME}/.local/share/nautilus-python/extensions"

if mkdir -p "$user_ext_dir"
then pass "Created target extension directory"
else fail "Could not create directory: $user_ext_dir"
fi

if test -f "$extension_name"
then if cp "$extension_name" "$user_ext_dir/$extension_name"
     then pass "Copied $extension_name to $user_ext_dir"
     else fail "Could not copy $extension_name to $user_ext_dir"
     fi
else printf 'Downloading %s from Codeberg...\n' "$extension_name" >&2
     if curl -sSL -o "$user_ext_dir/$extension_name" "https://codeberg.org/nautilus-spriteview/raw/branch/main/nautilus_preview.py"
     then pass "Downloaded and installed $extension_name"
     else fail "Could not download $extension_name from Codeberg"
     fi
fi

printf 'Restarting Nautilus...\n' >&2
nautilus -q || true
pass "Nautilus quit command sent"
