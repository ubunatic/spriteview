# Distribution Compatibility and Installation

This document details the support matrix, dependencies, and distribution-specific setup for Nautilus SpriteView.

## Core Requirements

SpriteView is a GTK4-based python extension for GNOME Files (Nautilus). To run, the host environment must provide:

1. **GNOME 43+** (specifically Nautilus 43 or newer), which introduced the modern model-based extension API and GTK4 rendering.
2. **PyGObject** (`gi.repository` namespaces for `Gtk`, `Gdk`, `Notify`, and `GdkPixbuf`).
3. **Nautilus Python bindings** (`python-nautilus` / `nautilus-python`).

---

## Supported Distributions

| Distribution | Version Scope | Package Name | Command |
| :--- | :--- | :--- | :--- |
| **Ubuntu** | `23.04` to `26.04 LTS` (and newer) | `python3-nautilus` | `sudo apt install python3-nautilus` |
| **Debian** | `12` (Bookworm) and newer | `python3-nautilus` | `sudo apt install python3-nautilus` |
| **Linux Mint** | `22` and newer (GNOME edition) | `python3-nautilus` | `sudo apt install python3-nautilus` |
| **Fedora** | `37` to `42` (and newer) | `nautilus-python` | `sudo dnf install nautilus-python` |
| **CentOS / RHEL** | `9.2` and newer | `nautilus-python` | `sudo dnf install nautilus-python` |
| **Arch Linux** | Rolling release | `nautilus-python` | `sudo pacman -S nautilus-python` |
| **Manjaro** | Rolling release (GNOME edition) | `nautilus-python` | `sudo pacman -S nautilus-python` |
| **openSUSE** | Tumbleweed / Leap `15.5+` | `nautilus-python` | `sudo zypper install nautilus-python` |

---

## Installation Helper Auto-Detection

The project installer script at [scripts/install.sh](file:///home/uwe/projects/nautilus/scripts/install.sh) auto-detects the host package manager to verify or install dependencies prior to placing the python extension inside the user's extensions folder (`~/.local/share/nautilus-python/extensions`).

### Detection Flow
1. Check for **Debian/Ubuntu (`dpkg-query`)**:
   Queries for `python3-nautilus` and triggers installation via `apt` if missing.
2. Check for **Fedora/RHEL (`rpm`)**:
   Queries for `nautilus-python` and triggers installation via `dnf` if missing.
3. Check for **Arch Linux (`pacman`)**:
   Queries for `nautilus-python` and triggers installation via `pacman` if missing.
4. **Fallback Warning**:
   If no known package manager is discovered, the installer assumes the bindings are installed and prompts the user to check their system manually.

---

## Distro-specific Learnings and Quirks

### openSUSE
* Uses the package name `nautilus-python`.
* Packages are installed via `zypper`. Future updates to `scripts/install.sh` should add zypper support if openSUSE usage increases.

### Flatpak / Snap sandboxing
* **Important**: If Nautilus is running as a sandboxed application (e.g., via Flatpak or Snap instead of a system package), local python extensions placed in `~/.local/share/nautilus-python/extensions` might not be loaded or executed by the sandbox. Native system installations are recommended.
