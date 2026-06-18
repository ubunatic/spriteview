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

if cp "$extension_name" "$user_ext_dir/$extension_name"
then pass "Copied $extension_name to $user_ext_dir"
else fail "Could not copy $extension_name to $user_ext_dir"
fi

printf 'Restarting Nautilus...\n' >&2
nautilus -q || true
pass "Nautilus quit command sent"
