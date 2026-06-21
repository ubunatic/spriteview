# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from sprite_view.settings import save_settings

class SettingsWindow(Gtk.Window):
    def __init__(self, parent_win) -> None:
        super().__init__(title="Settings")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(320, 240)
        self.parent_win = parent_win
        self.settings = parent_win.settings

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
