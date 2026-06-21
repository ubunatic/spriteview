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

has_pkg_installed="false"

if command -v dpkg-query >/dev/null 2>&1
then
   if dpkg-query -W -f='${Status}' python3-nautilus 2>/dev/null | grep -q "ok installed"
   then
      has_pkg_installed="true"
      pass "python3-nautilus is installed"
   fi
elif command -v rpm >/dev/null 2>&1
then
   if rpm -q nautilus-python >/dev/null 2>&1
   then
      has_pkg_installed="true"
      pass "nautilus-python is installed"
   fi
elif command -v pacman >/dev/null 2>&1
then
   if pacman -Qi nautilus-python >/dev/null 2>&1
   then
      has_pkg_installed="true"
      pass "nautilus-python is installed"
   fi
else
   # If we cannot verify, assume it might be installed rather than failing.
   has_pkg_installed="true"
   printf 'Could not auto-detect package manager. Assuming nautilus-python is installed.\n' >&2
fi

if test "$has_pkg_installed" = "false"
then
   if command -v apt-get >/dev/null 2>&1
   then
      printf 'python3-nautilus is required but not installed.\n' >&2
      printf 'Would you like to install it now using sudo apt install? [y/N]: ' >&2
      read -r response
      if test "$response" = "y" ||
         test "$response" = "Y"
      then
         printf 'Running: sudo apt update && sudo apt install -y python3-nautilus...\n' >&2
         if sudo apt update &&
            sudo apt install -y python3-nautilus
         then
            pass "Successfully installed python3-nautilus"
         else
            fail "Failed to install python3-nautilus"
         fi
      else
         fail "python3-nautilus is required to run the extension. Installation aborted."
      fi
   elif command -v dnf >/dev/null 2>&1
   then
      printf 'nautilus-python is required but not installed.\n' >&2
      printf 'Would you like to install it now using sudo dnf install? [y/N]: ' >&2
      read -r response
      if test "$response" = "y" ||
         test "$response" = "Y"
      then
         printf 'Running: sudo dnf install -y nautilus-python...\n' >&2
         if sudo dnf install -y nautilus-python
         then
            pass "Successfully installed nautilus-python"
         else
            fail "Failed to install nautilus-python"
         fi
      else
         fail "nautilus-python is required to run the extension. Installation aborted."
      fi
   elif command -v pacman >/dev/null 2>&1
   then
      printf 'nautilus-python is required but not installed.\n' >&2
      printf 'Would you like to install it now using sudo pacman -S? [y/N]: ' >&2
      read -r response
      if test "$response" = "y" ||
         test "$response" = "Y"
      then
         printf 'Running: sudo pacman -S --noconfirm nautilus-python...\n' >&2
         if sudo pacman -S --noconfirm nautilus-python
         then
            pass "Successfully installed nautilus-python"
         else
            fail "Failed to install nautilus-python"
         fi
      else
         fail "nautilus-python is required to run the extension. Installation aborted."
      fi
   else
      fail "nautilus-python is required to run the extension. Please install it manually."
   fi
fi

if mkdir -p "$user_ext_dir"
then pass "Created target extension directory"
else fail "Could not create directory: $user_ext_dir"
fi

if test -f "dist/$extension_name"
then
   if cp "dist/$extension_name" "$user_ext_dir/$extension_name"
   then
      pass "Copied packed dist/$extension_name to $user_ext_dir"
   else
      fail "Could not copy dist/$extension_name to $user_ext_dir"
   fi
   mkdir -p "${HOME}/.local/bin"
   if cp "dist/$extension_name" "${HOME}/.local/bin/spriteview"
   then
      chmod +x "${HOME}/.local/bin/spriteview"
      pass "Installed spriteview CLI to ${HOME}/.local/bin/spriteview"
   else
      fail "Could not copy dist/$extension_name to ${HOME}/.local/bin/spriteview"
   fi
elif test -f "$extension_name"
then
   if cp "$extension_name" "$user_ext_dir/$extension_name"
   then
      pass "Copied $extension_name to $user_ext_dir"
   else
      fail "Could not copy $extension_name to $user_ext_dir"
   fi
   mkdir -p "${HOME}/.local/bin"
   if cp "$extension_name" "${HOME}/.local/bin/spriteview"
   then
      chmod +x "${HOME}/.local/bin/spriteview"
      pass "Installed spriteview CLI to ${HOME}/.local/bin/spriteview"
   else
      fail "Could not copy $extension_name to ${HOME}/.local/bin/spriteview"
   fi
   if test -d "sprite_view"
   then
      mkdir -p "$user_ext_dir/sprite_view"
      if cp -r sprite_view/* "$user_ext_dir/sprite_view/"
      then
         pass "Copied sprite_view package to $user_ext_dir/sprite_view"
      else
         fail "Could not copy sprite_view package to $user_ext_dir/sprite_view"
      fi
   fi
else
   printf 'Downloading %s from Codeberg...\n' "$extension_name" >&2
   if curl -sSL -o "$user_ext_dir/$extension_name" "https://codeberg.org/nautilus-spriteview/raw/branch/main/sprite_view.py"
   then
      pass "Downloaded and installed $extension_name"
   else
      fail "Could not download $extension_name from Codeberg"
   fi
   mkdir -p "${HOME}/.local/bin"
   if cp "$user_ext_dir/$extension_name" "${HOME}/.local/bin/spriteview"
   then
      chmod +x "${HOME}/.local/bin/spriteview"
      pass "Installed spriteview CLI to ${HOME}/.local/bin/spriteview"
   else
      fail "Could not install spriteview CLI to ${HOME}/.local/bin/spriteview"
   fi
fi

printf 'Restarting Nautilus...\n' >&2
nautilus -q || true
pass "Nautilus quit command sent"
