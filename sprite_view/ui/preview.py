# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from typing import List
from collections import Counter

from sprite_view.utils import format_size, rgb_to_ansi, get_short_hex
from sprite_view.settings import load_settings, save_settings
from sprite_view.ui.about import AboutWindow
from sprite_view.ui.settings import SettingsWindow

def init_css():
    display = Gdk.Display.get_default()
    if display:
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .active-frame {
                border: 3px solid #3584e4;
                border-radius: 4px;
            }
            .thumb-btn {
                padding: 2px;
                margin: 4px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

class SelectableLabel(Gtk.Label):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_selectable(True)
        self.set_focusable(False)

class ImagePreviewWindow(Gtk.Window):
    def __init__(self, file_paths: List[str], selected_file_path: str, title: str) -> None:
        super().__init__(title=title)
        self.set_default_size(780, 580)

        # Initialize style provider
        init_css()

        self.file_paths = file_paths
        self.first_frame_path = file_paths[0] if file_paths else ""
        self.dir_path = os.path.dirname(self.first_frame_path) if self.first_frame_path else ""

        # Load settings
        self.settings = load_settings()

        # Determine initial FPS for this sequence
        self.initial_fps = self.settings.get("default_fps", 15.0)
        if self.settings.get("remember_fps", True) and self.first_frame_path:
            saved_fps = self.settings.get("saved_fps", {})
            scope = self.settings.get("remember_scope", "sheet")
            key = f"sheet:{self.first_frame_path}" if scope == "sheet" else f"dir:{self.dir_path}"
            if key in saved_fps:
                try:
                    self.initial_fps = float(saved_fps[key])
                except (ValueError, TypeError):
                    pass

        # Create custom HeaderBar for title bar
        header_bar = Gtk.HeaderBar()
        self.set_titlebar(header_bar)

        # Create hamburger menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")

        # Create a simple popover containing "Settings..." and "About..." buttons
        menu_popover = Gtk.Popover()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)

        btn_settings = Gtk.Button(label="Settings...")
        btn_settings.set_has_frame(False)
        btn_settings.set_halign(Gtk.Align.START)
        btn_settings.connect("clicked", self._on_settings_clicked, menu_popover)
        menu_box.append(btn_settings)

        btn_about = Gtk.Button(label="About...")
        btn_about.set_has_frame(False)
        btn_about.set_halign(Gtk.Align.START)
        btn_about.connect("clicked", self._on_about_clicked, menu_popover)
        menu_box.append(btn_about)

        menu_popover.set_child(menu_box)
        menu_button.set_popover(menu_popover)
        header_bar.pack_end(menu_button)

        self.textures: List[Gdk.Texture] = []
        self.thumb_buttons: List[Gtk.Button] = []
        self.original_dimensions = []
        self.frame_palettes = []
        self.swatch_colors = [(0, 0, 0, 255)] * 16
        self.selected_color = (0, 0, 0, 255)
        
        try:
            self.current_frame = file_paths.index(selected_file_path)
        except ValueError:
            self.current_frame = 0
            
        self.is_playing = len(file_paths) > 1
        self.play_direction = 1
        self.timer_id = None

        # Root split-pane layout
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(500)
        self.set_child(paned)

        # Left pane (main preview and controls)
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_box.set_margin_start(10)
        left_box.set_margin_end(10)
        left_box.set_margin_top(10)
        left_box.set_margin_bottom(10)
        paned.set_start_child(left_box)

        # Right pane (sidebar panel for properties, palette, selected color)
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_box.set_margin_start(12)
        right_box.set_margin_end(12)
        right_box.set_margin_top(12)
        right_box.set_margin_bottom(12)
        right_box.set_size_request(240, -1)
        paned.set_end_child(right_box)

        # Load all images
        for path in file_paths:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
                w = pixbuf.get_width()
                h = pixbuf.get_height()
                self.original_dimensions.append((w, h))

                # Extract and store color palette from original frame image
                palette = self._extract_palette_from_pixbuf(pixbuf, 16)
                self.frame_palettes.append(palette)

                # Upscale using nearest neighbor if it's small pixel image
                if path.lower().endswith(('.png', '.gif', '.bmp')) and (w < 1024 or h < 1024):
                    scale_factor = max(1, min(1024 // w, 1024 // h))
                    if scale_factor > 1:
                        new_w = w * scale_factor
                        new_h = h * scale_factor
                        pixbuf = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.NEAREST)

                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.textures.append(texture)
            except Exception as e:
                print(f"Error loading frame {path}: {e}")

        if not self.textures:
            label = Gtk.Label(label="Error: Could not load any images.")
            left_box.append(label)
            return

        # Setup main picture (left pane)
        self.picture = Gtk.Picture.new_for_paintable(self.textures[self.current_frame])
        self.picture.props.content_fit = Gtk.ContentFit.CONTAIN
        self.picture.set_vexpand(True)
        self.picture.set_hexpand(True)
        left_box.append(self.picture)

        # Setup Sidebar properties (right pane)
        title_lbl = Gtk.Label()
        title_lbl.set_markup("<b>File Properties</b>")
        title_lbl.set_halign(Gtk.Align.START)
        right_box.append(title_lbl)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        right_box.append(sep)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right_box.append(info_box)

        def create_sidebar_row(title: str) -> Gtk.Label:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            t_lbl = Gtk.Label()
            t_lbl.set_markup(f"<b>{title}:</b>")
            t_lbl.set_halign(Gtk.Align.START)
            v_lbl = SelectableLabel(label="-")
            v_lbl.set_halign(Gtk.Align.START)
            row.append(t_lbl)
            row.append(v_lbl)
            info_box.append(row)
            return v_lbl

        self.lbl_info_filename = create_sidebar_row("Filename")
        self.lbl_info_filename.set_wrap(True)
        self.lbl_info_filename.set_max_width_chars(24)
        
        self.lbl_info_dimensions = create_sidebar_row("Dimensions")
        self.lbl_info_filesize = create_sidebar_row("File Size")
        self.lbl_info_frame = create_sidebar_row("Frame")

        # Setup Color Palette sidebar section
        palette_lbl = Gtk.Label()
        palette_lbl.set_markup("<b>Color Palette</b>")
        palette_lbl.set_halign(Gtk.Align.START)
        right_box.append(palette_lbl)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        right_box.append(sep2)

        self.palette_flowbox = Gtk.FlowBox()
        self.palette_flowbox.set_valign(Gtk.Align.START)
        self.palette_flowbox.set_max_children_per_line(8)
        self.palette_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.palette_flowbox.set_column_spacing(4)
        self.palette_flowbox.set_row_spacing(4)
        right_box.append(self.palette_flowbox)

        # Pre-create exactly 16 color swatches in FlowBox to avoid widget creation lifecycle churn during play
        self.swatch_widgets = []
        for i in range(16):
            swatch = Gtk.DrawingArea()
            swatch.set_size_request(24, 24)
            
            # Setup draw callback binding to array index state
            def make_draw_func(idx):
                def draw_cb(area, cr, w, h):
                    col = self.swatch_colors[idx]
                    cr.set_source_rgb(col[0]/255.0, col[1]/255.0, col[2]/255.0)
                    cr.rectangle(0, 0, w, h)
                    cr.fill()
                    cr.set_source_rgb(0.3, 0.3, 0.3)
                    cr.set_line_width(1.0)
                    cr.rectangle(0.5, 0.5, w - 1, h - 1)
                    cr.stroke()
                return draw_cb
            
            swatch.set_draw_func(make_draw_func(i))

            # Bind gesture clicks
            gesture = Gtk.GestureClick()
            def make_click_func(idx):
                def click_cb(gest, n_press, x, y):
                    col = self.swatch_colors[idx]
                    self._on_swatch_clicked(gest, n_press, x, y, col)
                return click_cb

            gesture.connect("pressed", make_click_func(i))
            swatch.add_controller(gesture)

            self.palette_flowbox.append(swatch)
            self.swatch_widgets.append(swatch)

        # Setup Selected Color Details section (hidden by default)
        self.color_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.color_details_box.set_visible(False)
        
        detail_title = Gtk.Label()
        detail_title.set_markup("<b>Selected Color</b>")
        detail_title.set_halign(Gtk.Align.START)
        self.color_details_box.append(detail_title)
        
        sep3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.color_details_box.append(sep3)

        detail_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.color_details_box.append(detail_row)

        # Large swatch representation
        self.selected_swatch = Gtk.DrawingArea()
        self.selected_swatch.set_size_request(48, 48)
        def draw_selected_cb(area, cr, w, h):
            col = self.selected_color
            cr.set_source_rgb(col[0]/255.0, col[1]/255.0, col[2]/255.0)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.set_line_width(1.0)
            cr.rectangle(0.5, 0.5, w - 1, h - 1)
            cr.stroke()
        self.selected_swatch.set_draw_func(draw_selected_cb)
        detail_row.append(self.selected_swatch)

        # Labels panel
        labels_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        detail_row.append(labels_vbox)

        def create_detail_field(title: str) -> Gtk.Label:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            t_lbl = Gtk.Label()
            t_lbl.set_markup(f"<b>{title}:</b>")
            t_lbl.set_halign(Gtk.Align.START)
            v_lbl = SelectableLabel(label="-")
            v_lbl.set_halign(Gtk.Align.START)
            row.append(t_lbl)
            row.append(v_lbl)
            labels_vbox.append(row)
            return v_lbl

        self.lbl_selected_ansi_num = create_detail_field("ANSI #")
        self.lbl_selected_ansi_name = create_detail_field("Name")
        self.lbl_selected_ansi_name.set_wrap(True)
        self.lbl_selected_ansi_name.set_max_width_chars(16)

        self.lbl_selected_short_hex = create_detail_field("Short")
        self.lbl_selected_long_hex = create_detail_field("Long")
        self.lbl_selected_rgba = create_detail_field("RGBA")

        right_box.append(self.color_details_box)

        # Close window when ESC key is pressed
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

        # If it's single image, skip animation controls setup but populate properties
        if len(self.textures) == 1:
            self._update_frame()
            return

        # Setup indicator row (centered on its own row below picture)
        self.lbl_indicator = Gtk.Label(label="")
        self.lbl_indicator.set_halign(Gtk.Align.CENTER)
        left_box.append(self.lbl_indicator)

        # Setup Control Bar (centered on its own row below indicator)
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        control_box.set_halign(Gtk.Align.CENTER)
        
        btn_prev = Gtk.Button(label="<")
        btn_prev.connect("clicked", self._on_prev_clicked)
        control_box.append(btn_prev)
        
        self.btn_play_pause = Gtk.Button(label="⏸ Pause")
        self.btn_play_pause.connect("clicked", self._on_play_pause_clicked)
        control_box.append(self.btn_play_pause)
        
        btn_next = Gtk.Button(label=">")
        btn_next.connect("clicked", self._on_next_clicked)
        control_box.append(btn_next)
        
        left_box.append(control_box)

        # Setup Settings Box (centered below control buttons, combining FPS and Mode)
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        settings_box.set_halign(Gtk.Align.CENTER)
        
        fps_lbl = Gtk.Label(label="FPS:")
        settings_box.append(fps_lbl)
        
        adj = Gtk.Adjustment(value=self.initial_fps, lower=1.0, upper=60.0, step_increment=1.0, page_increment=5.0, page_size=0.0)
        self.fps_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1.0, digits=0)
        self.fps_spin.connect("value-changed", self._on_fps_changed)
        settings_box.append(self.fps_spin)
        
        mode_lbl = Gtk.Label(label="Mode:")
        settings_box.append(mode_lbl)
        
        self.mode_dropdown = Gtk.DropDown.new_from_strings(["Loop", "Ping-Pong", "Once"])
        self.mode_dropdown.set_selected(self.settings.get("default_mode", 0))
        self.mode_dropdown.connect("notify::selected", self._on_mode_changed)
        settings_box.append(self.mode_dropdown)
        
        left_box.append(settings_box)

        # Setup Sprite Sheet (ScrolledWindow containing horizontal Box)
        scroll_win = Gtk.ScrolledWindow()
        scroll_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll_win.set_min_content_height(80)
        scroll_win.set_hexpand(True)
        
        thumbs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        thumbs_box.set_halign(Gtk.Align.CENTER)
        scroll_win.set_child(thumbs_box)
        
        left_box.append(scroll_win)

        # Create thumbnail buttons for the sprite sheet
        for idx, texture in enumerate(self.textures):
            btn_thumb = Gtk.Button()
            btn_thumb.add_css_class("thumb-btn")
            
            thumb_pic = Gtk.Picture.new_for_paintable(texture)
            thumb_pic.set_size_request(48, 48)
            thumb_pic.props.content_fit = Gtk.ContentFit.CONTAIN
            btn_thumb.set_child(thumb_pic)
            
            btn_thumb.connect("clicked", self._on_thumb_clicked, idx)
            thumbs_box.append(btn_thumb)
            self.thumb_buttons.append(btn_thumb)

        self._update_frame()
        self.connect("destroy", self._on_destroy)
        
        # Start timer matching the initial spin button value
        initial_fps = self.fps_spin.get_value()
        initial_interval = int(1000.0 / initial_fps)
        self.timer_id = GLib.timeout_add(initial_interval, self._on_timer_tick)

    def _extract_palette_from_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf, max_colors: int = 16) -> List[tuple]:
        w = pixbuf.get_width()
        h = pixbuf.get_height()
        
        # Downsample large images for performance (keeps count analysis fast)
        if w > 64 or h > 64:
            scale = min(64.0 / w, 64.0 / h)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            pixbuf = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.NEAREST)
            w = pixbuf.get_width()
            h = pixbuf.get_height()

        pixels = pixbuf.get_pixels()
        n_channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()
        
        color_counts = Counter()
        for y in range(h):
            row_offset = y * rowstride
            for x in range(w):
                offset = row_offset + x * n_channels
                r = pixels[offset]
                g = pixels[offset+1]
                b = pixels[offset+2]
                a = pixels[offset+3] if n_channels == 4 else 255
                
                # Ignore fully transparent pixels
                if a < 16:
                    continue
                
                color_counts[(r, g, b, a)] += 1
                
        return [color for color, count in color_counts.most_common(max_colors)]

    def _on_timer_tick(self) -> bool:
        if self.is_playing:
            self._advance_frame()
        return True

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_destroy(self, widget) -> None:
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def _on_fps_changed(self, spin_button) -> None:
        fps = spin_button.get_value()
        interval_ms = int(1000.0 / fps)
        
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            
        self.timer_id = GLib.timeout_add(interval_ms, self._on_timer_tick)

        if hasattr(self, "settings") and self.settings.get("remember_fps", True) and self.first_frame_path:
            scope = self.settings.get("remember_scope", "sheet")
            key = f"sheet:{self.first_frame_path}" if scope == "sheet" else f"dir:{self.dir_path}"
            self.settings.setdefault("saved_fps", {})[key] = fps
            save_settings(self.settings)

    def _on_settings_clicked(self, button, popover) -> None:
        popover.popdown()
        settings_win = SettingsWindow(self)
        settings_win.present()

    def _on_about_clicked(self, button, popover) -> None:
        popover.popdown()
        about_win = AboutWindow(self)
        about_win.present()

    def _on_mode_changed(self, dropdown, pspec) -> None:
        self.play_direction = 1

    def _advance_frame(self) -> None:
        n_frames = len(self.textures)
        if n_frames <= 1:
            return

        mode = self.mode_dropdown.get_selected()  # 0: Loop, 1: Ping-Pong, 2: Once

        if mode == 0:  # Loop
            self.current_frame = (self.current_frame + 1) % n_frames
            
        elif mode == 1:  # Ping-Pong
            if self.play_direction == 1:
                if self.current_frame < n_frames - 1:
                    self.current_frame += 1
                else:
                    self.play_direction = -1
                    self.current_frame = max(0, self.current_frame - 1)
            else:
                if self.current_frame > 0:
                    self.current_frame -= 1
                else:
                    self.play_direction = 1
                    self.current_frame = min(n_frames - 1, self.current_frame + 1)
                    
        elif mode == 2:  # Once
            if self.current_frame < n_frames - 1:
                self.current_frame += 1
            else:
                self.is_playing = False
                self._update_play_pause_button()

        self._update_frame()

    def _next_frame(self) -> None:
        self.current_frame = (self.current_frame + 1) % len(self.textures)
        self._update_frame()

    def _prev_frame(self) -> None:
        self.current_frame = (self.current_frame - 1) % len(self.textures)
        self._update_frame()

    def _on_next_clicked(self, button) -> None:
        self.is_playing = False
        self._update_play_pause_button()
        self._next_frame()

    def _on_prev_clicked(self, button) -> None:
        self.is_playing = False
        self._update_play_pause_button()
        self._prev_frame()

    def _on_play_pause_clicked(self, button) -> None:
        self.is_playing = not self.is_playing
        
        # If play is pressed and we are at the end of "Once" mode, reset to frame 0
        if self.is_playing and self.mode_dropdown.get_selected() == 2:
            if self.current_frame >= len(self.textures) - 1:
                self.current_frame = 0
                self._update_frame()
                
        self._update_play_pause_button()

    def _on_thumb_clicked(self, button, idx: int) -> None:
        self.is_playing = False
        self._update_play_pause_button()
        self.current_frame = idx
        self._update_frame()

    def _on_swatch_clicked(self, gesture, n_press: int, x: float, y: float, color: tuple) -> None:
        self.selected_color = color
        self._update_selected_color_ui()

    def _update_play_pause_button(self) -> None:
        if self.is_playing:
            self.btn_play_pause.set_label("⏸ Pause")
        else:
            self.btn_play_pause.set_label("▶ Play")

    def _update_selected_color_ui(self) -> None:
        if not hasattr(self, 'color_details_box') or not self.color_details_box:
            return
            
        self.color_details_box.set_visible(True)
        self.selected_swatch.queue_draw()
        
        r, g, b, a = self.selected_color
        
        ansi_num, ansi_name = rgb_to_ansi(r, g, b)
        
        short_hex = get_short_hex(r, g, b)
        long_hex = f"#{r:02x}{g:02x}{b:02x}{a:02x}" if a < 255 else f"#{r:02x}{g:02x}{b:02x}"
        rgba_str = f"rgba({r}, {g}, {b}, {a/255.0:.2f})"
        
        self.lbl_selected_ansi_num.set_label(str(ansi_num))
        self.lbl_selected_ansi_name.set_label(ansi_name)
        self.lbl_selected_short_hex.set_label(short_hex)
        self.lbl_selected_long_hex.set_label(long_hex)
        self.lbl_selected_rgba.set_label(rgba_str)

    def _update_frame(self) -> None:
        self.picture.set_paintable(self.textures[self.current_frame])
        
        current_path = self.file_paths[self.current_frame]
        frame_file = os.path.basename(current_path)
        
        # Update control indicator if in animation mode
        if hasattr(self, 'lbl_indicator') and self.lbl_indicator:
            self.lbl_indicator.set_label(f"Frame {self.current_frame + 1} / {len(self.textures)}")
            
        if hasattr(self, 'lbl_info_frame') and self.lbl_info_frame:
            if len(self.textures) > 1:
                self.lbl_info_frame.set_label(f"{self.current_frame + 1} of {len(self.textures)}")
            else:
                self.lbl_info_frame.set_label("1 of 1 (Static Image)")

        # Update sidebar info
        self.lbl_info_filename.set_label(frame_file)
        
        try:
            orig_w, orig_h = self.original_dimensions[self.current_frame]
            self.lbl_info_dimensions.set_label(f"{orig_w} × {orig_h} px")
            
            size_bytes = os.path.getsize(current_path)
            self.lbl_info_filesize.set_label(format_size(size_bytes))
        except Exception as e:
            self.lbl_info_dimensions.set_label("Unknown")
            self.lbl_info_filesize.set_label("Unknown")

        # Update color palette swatch colors instead of rebuilding widgets
        palette = self.frame_palettes[self.current_frame]
        for i in range(16):
            swatch = self.swatch_widgets[i]
            if i < len(palette):
                col = palette[i]
                self.swatch_colors[i] = col
                r, g, b, a = col
                swatch.set_tooltip_text(f"RGB: ({r}, {g}, {b})\nHex: #{r:02x}{g:02x}{b:02x}")
                swatch.set_visible(True)
                swatch.queue_draw()
            else:
                swatch.set_visible(False)

        # Update active frame styling if in animation mode
        if hasattr(self, 'thumb_buttons'):
            for i, btn in enumerate(self.thumb_buttons):
                if i == self.current_frame:
                    btn.add_css_class("active-frame")
                else:
                    btn.remove_css_class("active-frame")

    def present(self) -> None:
        super().present()
        # Schedule setting/clearing focus on presentation to ensure proper startup focus state
        GLib.idle_add(self._set_initial_focus)

    def _set_initial_focus(self) -> bool:
        if len(self.textures) > 1 and hasattr(self, "btn_play_pause") and self.btn_play_pause:
            self.set_focus(self.btn_play_pause)
        else:
            self.set_focus(None)
        return False
