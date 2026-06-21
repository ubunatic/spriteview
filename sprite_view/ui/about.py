# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from sprite_view.logo import get_embedded_banner

class AboutWindow(Gtk.AboutDialog):
    def __init__(self, parent_win) -> None:
        super().__init__()
        self.set_transient_for(parent_win)

        self.set_program_name("Nautilus Sprite View")
        self.set_version("1.0.0")
        self.set_comments("A lightweight sprite sheet and animation frame previewer for Nautilus.")
        self.set_website("https://github.com/ubunatic/nautilus")
        self.set_copyright("© 2026 Uwe Jugel")
        self.set_license_type(Gtk.License.AGPL_3_0_ONLY)
        
        # Set the logo to show the embedded banner.png
        banner_texture = get_embedded_banner()
        if banner_texture:
            self.set_logo(banner_texture)

        # Prevent plain text labels and links from being automatically focused/text-selected on open
        def prevent_label_selection(widget):
            if isinstance(widget, Gtk.Label):
                text = widget.get_text()
                if text in ["Nautilus Sprite View", "1.0.0", "© 2026 Uwe Jugel", "Website", "https://github.com/ubunatic/nautilus"] or "lightweight sprite" in text:
                    widget.set_selectable(False)
                    widget.set_focusable(False)
            child = widget.get_first_child()
            while child:
                prevent_label_selection(child)
                child = child.get_next_sibling()
        
        prevent_label_selection(self)

        # Connect explicit close-request to direct destroy call
        self.connect("close-request", self._on_close_request)

        # Close window when ESC key is pressed
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_close_request(self, window) -> bool:
        self.destroy()
        return True

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def present(self) -> None:
        super().present()
        # Schedule clearing focus to the next idle cycle to ensure no widget remains highlighted
        GLib.idle_add(self._clear_focus)

    def _clear_focus(self) -> bool:
        self.set_focus(None)
        return False
