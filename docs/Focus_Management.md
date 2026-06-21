# GTK4 Focus Management and Label Selection

This document outlines the learnings, conventions, and architectural patterns established for managing widget focus, text selection, and window dismissal in the Nautilus Sprite View application.

---

## 1. The Selectable Label Focus Gotcha

### The Problem
In GTK4, enabling text selection on a label (`Gtk.Label.set_selectable(True)`) so that users can copy values automatically alters its keyboard focus properties:
* Making a label selectable sets its `focusable` (or `can-focus`) property to `True` by default.
* Upon presenting a new window, GTK4 automatically searches the widget tree for the first focusable widget to receive keyboard focus.
* If a selectable label is the first focusable element (common on simple views or static previews where navigation/action buttons are absent), it grabs focus on startup.
* In GTK4, when a selectable label gains focus, its default behavior is to select/highlight all of its text content. This causes critical text fields (like file names) to start in an active, highlighted selection state on open.

---

## 2. Solution: The `SelectableLabel` Pattern

Instead of post-presentation cleanup callbacks (which leave an ugly flashing or inactive gray highlight), the issue is resolved at the widget definition level using a dedicated subclass:

```python
class SelectableLabel(Gtk.Label):
    """
    A custom Gtk.Label subclass that is selectable via mouse (allowing copy-paste),
    but excluded from the keyboard focus tree to prevent unwanted startup selection highlights.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_selectable(True)
        self.set_focusable(False)
```

### Architectural Benefits:
1. **Encapsulation**: Encapsulates the select-yet-don't-focus behavior into a semantic, reusable class.
2. **Declarative**: Keeps layout code clean by instantiating `SelectableLabel` for dynamic values (filenames, hex codes, color names) while using standard `Gtk.Label` for static labels.
3. **No Hacky Cleanups**: Eliminates the need for post-presentation idle handlers (`GLib.idle_add`) or traversing children to manually deselect regions.

---

## 3. Explicit Window Focus Routing

When a window is presented, it is best practice to explicitly declare which element should handle keyboard focus, rather than letting GTK4 guess:

```python
    def present(self) -> None:
        super().present()
        # Ensure correct initial focus is requested on presentation
        GLib.idle_add(self._set_initial_focus)

    def _set_initial_focus(self) -> bool:
        if len(self.textures) > 1 and hasattr(self, "btn_play_pause") and self.btn_play_pause:
            self.set_focus(self.btn_play_pause)
        else:
            self.set_focus(None)  # Focus on nothing (or top-level window)
        return False
```

* **Animation Sequences**: Focus is explicitly routed to the **Play/Pause button** for immediate key accessibility.
* **Static Images & Modals**: Focus is explicitly cleared (`self.set_focus(None)`) so the window starts in a pristine, clean state.

---

## 4. Universal Window Dismissal (ESC to Close)

For standard desktop usability, popups, settings pages, and preview dialogs must support keyboard dismissal. In GTK4, this is achieved cleanly using event controllers without overriding key-press methods:

```python
        # Attach Escape key controller during initialization
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
```

```python
    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True  # Stop further event propagation
        return False
```

This pattern is applied uniformly to:
* `ImagePreviewWindow` (main animation/static viewer)
* `SettingsWindow` (configuration popover)
* `AboutWindow` (general information/credits modal)
