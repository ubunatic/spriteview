<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Packaging and Distribution

This document explains our modular design and single-file packaging approach for the Nautilus Sprite View extension.

## Architecture & Goals

To keep the codebase maintainable, testable, and robust, we separate development concerns from installation and distribution requirements.

1. **Development & Modularity** (`sprite_view/` & `tests/`):
   - The application logic is written as a structured, modular Python package.
   - Separation of concerns separates pure logic (colors, file sizes, math) from GTK4 GUI widgets.
   - This allows fast, headless execution of python `unittest` tests without needing a Wayland/X11 display server.

2. **Zero-Pollution Deployment** (`dist/`):
   - Nautilus-Python extensions are loaded dynamically from single scripts placed in `~/.local/share/nautilus-python/extensions/`.
   - Instead of polluting the user's extensions folder with package subdirectories or requiring manual PYTHONPATH configuration, we build a single, self-contained distribution script `dist/sprite_view.py`.

---

## The Packing Pipeline (`scripts/pack.py`)

We use a custom, automated bundler script `scripts/pack.py` that parses our modular source files and compiles them into a single file.

### Order of Dependency Compilation

Because Python requires symbols to be defined before they are used at the module scope, `pack.py` processes files in order of their Directed Acyclic Graph (DAG):

1. `sprite_view/utils.py` (No internal dependencies)
2. `sprite_view/settings.py` (No internal dependencies)
3. `sprite_view/logo.py` (No internal dependencies)
4. `sprite_view/ui/about.py` (Depends on `logo.py`)
5. `sprite_view/ui/settings.py` (Depends on `settings.py`)
6. `sprite_view/ui/preview.py` (Depends on `utils.py`, `settings.py`, `about.py`, `settings.py`)
7. `sprite_view.py` (Main entrypoint)

### Compilation Steps
For each file in the compilation list, `pack.py`:
1. Strips local, internal package imports (e.g., `from sprite_view... import ...`).
2. Strips duplicate standard library and PyGObject imports (`import os`, `import gi`, `from gi.repository import ...`).
3. Strips headers and licensing comments (`# SPDX-...`).
4. Generates a unified, single global header with all required third-party imports and specific `gi.require_version` constraints.
5. Inlines the remaining functions and classes into the target file `dist/sprite_view.py`.

### Resilient Conditional Imports

Because the pipeline actively strips statements starting with `from gi.repository` or `gi.require_version` to prevent duplicates:
* **Gotcha**: If you write local `try/except` imports or version constraints (e.g., trying to conditionally import `Nautilus` only when running as a Nautilus extension), the compiler will strip those lines and leave empty `try` blocks, leading to `IndentationError`.
* **Resilient Pattern**: Bypass string-based line stripping by using dynamic references or `__import__`:
  ```python
  # Dynamic version demand:
  getattr(gi, 'require_version')('Nautilus', '4.0')

  # Dynamic import:
  Nautilus = __import__('gi.repository', fromlist=['Nautilus']).Nautilus
  ```

---

## Makefile Integration

The build, test, and packing steps are managed via the standard `Makefile`:

- **`make test`**: Runs syntax verification (`py_compile`) on the entrypoint and executes the `unittest` suite inside `tests/`.
- **`make pack`**: Compiles the source tree into `dist/sprite_view.py`.
- **`make install`**: Automatically triggers `test` and `pack`, copies `dist/sprite_view.py` directly into the Nautilus-Python extensions directory, and restarts Nautilus to apply changes.
- **`make uninstall`**: Removes the extension and cleans up caches.
