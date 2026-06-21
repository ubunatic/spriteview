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

extension_name="sprite_view.py"
user_ext_dir="${HOME}/.local/share/nautilus-python/extensions"

if dpkg-query -W -f='${Status}' python3-nautilus 2>/dev/null | grep -q "ok installed"
then pass "python3-nautilus is installed"
else printf 'python3-nautilus is required but not installed.\n' >&2
     printf 'Would you like to install it now using sudo apt install? [y/N]: ' >&2
     read -r response
     if test "$response" = "y" ||
        test "$response" = "Y"
     then printf 'Running: sudo apt update && sudo apt install -y python3-nautilus...\n' >&2
          if sudo apt update &&
             sudo apt install -y python3-nautilus
          then pass "Successfully installed python3-nautilus"
          else fail "Failed to install python3-nautilus"
          fi
     else fail "python3-nautilus is required to run the extension. Installation aborted."
     fi
fi

if mkdir -p "$user_ext_dir"
then pass "Created target extension directory"
else fail "Could not create directory: $user_ext_dir"
fi

if test -f "dist/$extension_name"
then if cp "dist/$extension_name" "$user_ext_dir/$extension_name"
     then pass "Copied packed dist/$extension_name to $user_ext_dir"
     else fail "Could not copy dist/$extension_name to $user_ext_dir"
     fi
elif test -f "$extension_name"
then if cp "$extension_name" "$user_ext_dir/$extension_name"
     then pass "Copied $extension_name to $user_ext_dir"
     else fail "Could not copy $extension_name to $user_ext_dir"
     fi
     if test -d "sprite_view"
     then mkdir -p "$user_ext_dir/sprite_view"
          if cp -r sprite_view/* "$user_ext_dir/sprite_view/"
          then pass "Copied sprite_view package to $user_ext_dir/sprite_view"
          else fail "Could not copy sprite_view package to $user_ext_dir/sprite_view"
          fi
     fi
else printf 'Downloading %s from Codeberg...\n' "$extension_name" >&2
     if curl -sSL -o "$user_ext_dir/$extension_name" "https://codeberg.org/nautilus-spriteview/raw/branch/main/sprite_view.py"
     then pass "Downloaded and installed $extension_name"
     else fail "Could not download $extension_name from Codeberg"
     fi
fi

printf 'Restarting Nautilus...\n' >&2
nautilus -q || true
pass "Nautilus quit command sent"
