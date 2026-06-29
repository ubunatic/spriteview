# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from sprite_view.settings import save_settings, load_settings

class SettingsWindow(Gtk.Window):
    def __init__(self, parent_win) -> None:
        super().__init__(title="Settings")
        self.set_transient_for(parent_win)
        self.set_icon_name("com.ubunatic.spriteview")
        self.set_default_size(450, -1)
        self.parent_win = parent_win
        self.settings = parent_win.settings if parent_win else load_settings()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        self.set_child(box)

        # 1. Default FPS Row
        default_fps_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        df_lbl = Gtk.Label(label="Default FPS:")
        df_lbl.set_halign(Gtk.Align.START)
        df_lbl.set_hexpand(True)
        default_fps_row.append(df_lbl)

        df_adj = Gtk.Adjustment(value=self.settings.get("default_fps", 15.0), lower=1.0, upper=60.0, step_increment=1.0)
        self.df_spin = Gtk.SpinButton(adjustment=df_adj, climb_rate=1.0, digits=0)
        self.df_spin.connect("value-changed", self._on_default_fps_changed)
        default_fps_row.append(self.df_spin)
        box.append(default_fps_row)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep)

        # 2. Remember FPS CheckButton
        self.remember_check = Gtk.CheckButton(label="Remember FPS")
        self.remember_check.set_active(self.settings.get("remember_fps", True))
        self.remember_check.connect("toggled", self._on_remember_changed)
        box.append(self.remember_check)

        # 3. Remember Scope Row
        scope_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        sc_lbl = Gtk.Label(label="Scope:")
        sc_lbl.set_halign(Gtk.Align.START)
        sc_lbl.set_hexpand(True)
        scope_row.append(sc_lbl)

        self.scope_dropdown = Gtk.DropDown.new_from_strings(["Per Sheet", "Per Directory"])
        current_scope = self.settings.get("remember_scope", "sheet")
        self.scope_dropdown.set_selected(0 if current_scope == "sheet" else 1)
        self.scope_dropdown.set_sensitive(self.settings.get("remember_fps", True))
        self.scope_dropdown.connect("notify::selected", self._on_remember_scope_changed)
        scope_row.append(self.scope_dropdown)
        box.append(scope_row)

        sep_mode = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep_mode)

        # 4. Default Mode Row
        default_mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dm_lbl = Gtk.Label(label="Default Mode:")
        dm_lbl.set_halign(Gtk.Align.START)
        dm_lbl.set_hexpand(True)
        default_mode_row.append(dm_lbl)

        self.default_mode_dropdown = Gtk.DropDown.new_from_strings(["Loop", "Ping-Pong", "Once"])
        self.default_mode_dropdown.set_selected(self.settings.get("default_mode", 0))
        self.default_mode_dropdown.connect("notify::selected", self._on_default_mode_changed)
        default_mode_row.append(self.default_mode_dropdown)
        box.append(default_mode_row)

        sep_display = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep_display)

        # 5. Display Settings
        display_lbl = Gtk.Label(label="Display:")
        display_lbl.set_halign(Gtk.Align.START)
        box.append(display_lbl)

        # 5a. Image background color row
        bg_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.bg_check = Gtk.CheckButton(label="Custom background")
        self.bg_check.set_active(self.settings.get("image_bg_color", "none") != "none")
        self.bg_check.connect("toggled", self._on_bg_toggled)
        bg_row.append(self.bg_check)
        self.bg_color_btn = Gtk.ColorButton()
        try:
            rgba = Gdk.RGBA()
            rgba.parse(self.settings.get("image_bg_color", "#3d3d3d"))
        except Exception:
            rgba = Gdk.RGBA(0.24, 0.24, 0.24, 1.0)
        self.bg_color_btn.set_rgba(rgba)
        self.bg_color_btn.set_sensitive(self.bg_check.get_active())
        self.bg_color_btn.connect("notify::rgba", self._on_bg_color_changed)
        bg_row.append(self.bg_color_btn)
        box.append(bg_row)

        # 5b. Image border toggle
        border_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.border_check = Gtk.CheckButton(label="Show image border")
        self.border_check.set_active(self.settings.get("show_image_border", False))
        self.border_check.connect("toggled", self._on_border_toggled)
        border_row.append(self.border_check)
        box.append(border_row)

        sep_seps = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep_seps)

        # 5. Sequence Separators
        seps_lbl = Gtk.Label(label="Sequence Separators:")
        seps_lbl.set_halign(Gtk.Align.START)
        box.append(seps_lbl)

        self.sep_chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.sep_chips_box.set_halign(Gtk.Align.START)
        box.append(self.sep_chips_box)
        self._rebuild_sep_chips()

        sep_add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sep_add_row.set_halign(Gtk.Align.START)
        self.sep_entry = Gtk.Entry()
        self.sep_entry.add_css_class("monospace")
        self.sep_entry.set_max_length(8)
        self.sep_entry.set_placeholder_text("new…")
        self.sep_entry.set_width_chars(8)
        self.sep_entry.connect("activate", self._on_sep_add)
        sep_add_row.append(self.sep_entry)
        sep_add_btn = Gtk.Button(label="+")
        sep_add_btn.connect("clicked", self._on_sep_add)
        sep_add_row.append(sep_add_btn)
        box.append(sep_add_row)

        sep_pats = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep_pats)

        # 6. Sequence Patterns
        pats_lbl = Gtk.Label(label="Sequence Patterns:")
        pats_lbl.set_halign(Gtk.Align.START)
        box.append(pats_lbl)

        self.pat_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.pat_list_box.set_halign(Gtk.Align.FILL)
        box.append(self.pat_list_box)
        self._rebuild_pat_list()

        pat_add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pat_add_row.set_halign(Gtk.Align.FILL)
        self.pat_entry = Gtk.Entry()
        self.pat_entry.add_css_class("monospace")
        self.pat_entry.set_placeholder_text("e.g. {prefix}_{number}…")
        self.pat_entry.set_hexpand(True)
        self.pat_entry.connect("activate", self._on_pat_add)
        pat_add_row.append(self.pat_entry)
        pat_add_btn = Gtk.Button(label="+")
        pat_add_btn.connect("clicked", self._on_pat_add)
        pat_add_row.append(pat_add_btn)
        box.append(pat_add_row)

        # Explicitly handle close-request so destroy() is always called, which
        # triggers the WindowManager singleton tracking cleanup.  Scheduling via
        # idle_add avoids calling destroy() synchronously inside the signal (GTK4
        # re-entrancy issue that caused the first-close regression).
        self.connect("close-request", self._on_close_request)

        # Close window when ESC key is pressed
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_close_request(self, window) -> bool:
        GLib.idle_add(self.destroy)
        return True  # suppress GTK's own close path; destroy() handles cleanup

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()  # emits close-request → _on_close_request → destroy
            return True
        return False

    def _on_default_fps_changed(self, spin_button) -> None:
        self.settings["default_fps"] = spin_button.get_value()
        save_settings(self.settings)

    def _on_remember_changed(self, check_button) -> None:
        active = check_button.get_active()
        self.settings["remember_fps"] = active
        self.scope_dropdown.set_sensitive(active)
        
        if active and hasattr(self.parent_win, "fps_spin") and self.parent_win.first_frame_path:
            current_fps = self.parent_win.fps_spin.get_value()
            scope = self.settings.get("remember_scope", "sheet")
            key = f"sheet:{self.parent_win.first_frame_path}" if scope == "sheet" else f"dir:{self.parent_win.dir_path}"
            self.settings.setdefault("saved_fps", {})[key] = current_fps
            
        save_settings(self.settings)

    def _on_remember_scope_changed(self, dropdown, pspec) -> None:
        selected_idx = dropdown.get_selected()
        scope = "sheet" if selected_idx == 0 else "dir"
        self.settings["remember_scope"] = scope
        
        if self.settings.get("remember_fps", True) and hasattr(self.parent_win, "fps_spin") and self.parent_win.first_frame_path:
            current_fps = self.parent_win.fps_spin.get_value()
            key = f"sheet:{self.parent_win.first_frame_path}" if scope == "sheet" else f"dir:{self.parent_win.dir_path}"
            self.settings.setdefault("saved_fps", {})[key] = current_fps
            
        save_settings(self.settings)

    def _on_default_mode_changed(self, dropdown, pspec) -> None:
        self.settings["default_mode"] = dropdown.get_selected()
        save_settings(self.settings)

    def _on_bg_toggled(self, check) -> None:
        active = check.get_active()
        self.bg_color_btn.set_sensitive(active)
        if active:
            rgba = self.bg_color_btn.get_rgba()
            color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
        else:
            color = "none"
        self.settings["image_bg_color"] = color
        if hasattr(self.parent_win, "_apply_image_bg_color"):
            self.parent_win._apply_image_bg_color(color)
        save_settings(self.settings)

    def _on_bg_color_changed(self, btn, pspec) -> None:
        if not self.bg_check.get_active():
            return
        rgba = btn.get_rgba()
        color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
        self.settings["image_bg_color"] = color
        if hasattr(self.parent_win, "_apply_image_bg_color"):
            self.parent_win._apply_image_bg_color(color)
        save_settings(self.settings)

    def _on_border_toggled(self, check) -> None:
        visible = check.get_active()
        self.settings["show_image_border"] = visible
        if hasattr(self.parent_win, "_apply_image_border_visibility"):
            self.parent_win._apply_image_border_visibility(visible)
        save_settings(self.settings)

    def _rebuild_sep_chips(self) -> None:
        child = self.sep_chips_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.sep_chips_box.remove(child)
            child = nxt
        for sep in self.settings.get("sequence_separators", ["_", "-"]):
            chip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            chip.add_css_class("sep-chip")
            lbl = Gtk.Label(label=sep)
            lbl.add_css_class("monospace")
            chip.append(lbl)
            rm = Gtk.Button(label="×")
            rm.set_has_frame(False)
            rm.connect("clicked", self._on_sep_remove, sep)
            chip.append(rm)
            self.sep_chips_box.append(chip)

    def _on_sep_add(self, widget) -> None:
        text = self.sep_entry.get_text()
        if not text:
            return
        seps = list(self.settings.get("sequence_separators", ["_", "-"]))
        if text not in seps:
            seps.append(text)
            self.settings["sequence_separators"] = seps
            save_settings(self.settings)
            self._rebuild_sep_chips()
        self.sep_entry.set_text("")

    def _on_sep_remove(self, btn, sep) -> None:
        seps = list(self.settings.get("sequence_separators", ["_", "-"]))
        if sep in seps:
            seps.remove(sep)
            self.settings["sequence_separators"] = seps
            save_settings(self.settings)
            self._rebuild_sep_chips()

    def _rebuild_pat_list(self) -> None:
        child = self.pat_list_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.pat_list_box.remove(child)
            child = nxt
        for pat in self.settings.get("sequence_patterns", []):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.set_hexpand(True)
            
            lbl = Gtk.Label(label=pat)
            lbl.add_css_class("monospace")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_tooltip_text(pat)
            row.append(lbl)
            
            rm = Gtk.Button(label="×")
            rm.set_has_frame(False)
            rm.connect("clicked", self._on_pat_remove, pat)
            row.append(rm)
            
            self.pat_list_box.append(row)

    def _on_pat_add(self, widget) -> None:
        text = self.pat_entry.get_text().strip()
        if not text:
            return
        
        # Validate template contains {number}
        if "{number}" not in text:
            self.pat_entry.set_text("")
            self.pat_entry.set_placeholder_text("Must contain '{number}'!")
            return
        
        # Validate it generates a valid regex
        try:
            from sprite_view.utils import template_to_regex
            import re
            re.compile(template_to_regex(text))
        except Exception:
            self.pat_entry.set_text("")
            self.pat_entry.set_placeholder_text("Invalid template expression!")
            return

        pats = list(self.settings.get("sequence_patterns", []))
        if text not in pats:
            pats.append(text)
            self.settings["sequence_patterns"] = pats
            save_settings(self.settings)
            self._rebuild_pat_list()
        self.pat_entry.set_text("")
        self.pat_entry.set_placeholder_text("e.g. {prefix}_{number}…")

    def _on_pat_remove(self, btn, pat) -> None:
        pats = list(self.settings.get("sequence_patterns", []))
        if pat in pats:
            pats.remove(pat)
            self.settings["sequence_patterns"] = pats
            save_settings(self.settings)
            self._rebuild_pat_list()

    def present(self) -> None:
        super().present()
        # Schedule focus on the first setting widget on presentation
        GLib.idle_add(self._set_initial_focus)

    def _set_initial_focus(self) -> bool:
        if hasattr(self, "df_spin") and self.df_spin:
            self.set_focus(self.df_spin)
        return False
