# GTK4 Window Lifecycle and Transient Management

This document records key lessons learned about window destruction in GTK4 / PyGObject and proposes a resilient, production-ready **Window Management and Lifecycle System** to prevent orphaned windows.

---

## 1. The Orphaned Child Gotcha in GTK4

### The Problem
When launching secondary windows (like settings panels or export dialogs) in GTK4:
* Setting `self.set_transient_for(parent_win)` establishes visual grouping, placement, and modals.
* **Gotcha**: If `parent_win` is destroyed/closed, GTK4 **does not** automatically propagate the destruction to its transient windows.
* Instead, child windows remain open (orphaned), retaining references in memory, which leads to:
  * Application state inconsistencies (e.g., trying to read data from a closed parent window).
  * Ghost/stuck windows that cannot be closed or block Nautilus processes.

### Window Categorization
To solve this, windows are classified into two distinct lifecycle profiles:
1. **Dependent Windows**: Instance-specific windows (e.g., `ExportOptionsWindow`) that belong to a single preview instance and must be destroyed immediately when that parent closes.
2. **Shared Singleton Windows**: Globally unique windows (e.g., `SettingsWindow`, `AboutWindow`) that are shared across all active previews. They should survive parent closure by **re-parenting** to another active preview window (or clearing parent) until the last preview closes.

---

## 2. Centralized Window Registry System

To keep view components decoupled and make window management highly resilient, we route all secondary windows (both dependent windows and shared singletons) through a dedicated **`WindowManager`** registry.

### Architecture Diagram

```
                 ┌──────────────────┐
                 │  WindowManager   │
                 └────────┬─────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
   Register Parent  Register Child   Manage Singletons
```

### `WindowManager` Implementation

```python
class WindowManager:
    """
    Centralized registry managing window lifecycles, child dependencies,
    and automatic transient parent resolution.
    """
    _active_parents = []
    _dependent_map = {}  # parent_id -> list of dependent windows
    _singletons = {}     # type_name -> window instance

    @classmethod
    def register_parent(cls, parent_win: Gtk.Window) -> None:
        if parent_win not in cls._active_parents:
            cls._active_parents.append(parent_win)
            cls._dependent_map[id(parent_win)] = []
            parent_win.connect("destroy", cls._on_parent_destroyed)

    @classmethod
    def register_dependent(cls, parent_win: Gtk.Window, child_win: Gtk.Window) -> None:
        cls.register_parent(parent_win) # Ensure parent is tracked
        child_win.set_transient_for(parent_win)
        cls._dependent_map[id(parent_win)].append(child_win)
        child_win.connect("destroy", lambda w: cls._on_dependent_destroyed(parent_win, w))

    @classmethod
    def get_singleton(cls, singleton_class, parent_win: Gtk.Window) -> Gtk.Window:
        name = singleton_class.__name__
        if name not in cls._singletons or cls._singletons[name] is None:
            # Instantiate singleton
            win = singleton_class(parent_win)
            cls._singletons[name] = win
            win.connect("destroy", lambda w: cls._on_singleton_destroyed(name))
        else:
            win = cls._singletons[name]
            win.set_transient_for(parent_win)
        win.present()
        return win

    @classmethod
    def _on_parent_destroyed(cls, parent_win: Gtk.Window) -> None:
        parent_id = id(parent_win)
        
        # 1. Sweep and destroy all dependent child windows
        if parent_id in cls._dependent_map:
            for child in list(cls._dependent_map[parent_id]):
                try:
                    child.destroy()
                except Exception:
                    pass
            del cls._dependent_map[parent_id]
            
        # 2. Remove from active parents
        if parent_win in cls._active_parents:
            cls._active_parents.remove(parent_win)
            
        # 3. Resolve transient re-parenting or destruction for singletons
        next_parent = cls._active_parents[0] if cls._active_parents else None
        for name, win in list(cls._singletons.items()):
            if win is not None:
                if next_parent is None:
                    # No active parent windows remain; destroy the singleton.
                    try:
                        win.destroy()
                    except Exception:
                        pass
                elif win.get_transient_for() is parent_win:
                    win.set_transient_for(next_parent)

    @classmethod
    def _on_dependent_destroyed(cls, parent_win: Gtk.Window, child_win: Gtk.Window) -> None:
        parent_id = id(parent_win)
        if parent_id in cls._dependent_map and child_win in cls._dependent_map[parent_id]:
            cls._dependent_map[parent_id].remove(child_win)

    @classmethod
    def _on_singleton_destroyed(cls, name: str) -> None:
        cls._singletons[name] = None
```

---

## 3. Explicit Close-Request Handling

To prevent transient child windows from entering invalid hidden/partially-destroyed states under different desktop environments and window managers:
* All secondary windows (`AboutWindow`, `SettingsWindow`, `ExportOptionsWindow`) explicitly connect to the GTK `"close-request"` signal.
* The handler calls `self.destroy()` directly to force complete object destruction and triggers the `WindowManager` tracking cleanup.
* The handler returns `True` to inhibit standard window-manager-driven close flows that could clash with PyGObject's event loop.

---

## 4. Advantages of the Centralized Registry Architecture

1. **Decoupled Logic**: Moves memory tracking, list sweeping, and event routing out of the view classes (`ImagePreviewWindow`, `ExportOptionsWindow`).
2. **Automatic Safety Nets**: If a developer forgets to clean up a child window, the `WindowManager` automatically sweeps and destroys it when the parent terminates.
3. **Thread and ID Safety**: Uses standard object IDs (`id(parent_win)`) to safely index tracking slots even if parent window references are cleared out of sequence.
4. **Uniform Pattern**: Provides a single API (`WindowManager.get_singleton(...)` and `WindowManager.register_dependent(...)`) for creating any dialogs in the application.
