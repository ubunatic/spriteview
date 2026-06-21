# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
import tempfile
import subprocess
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio
from typing import List
from collections import Counter
from PIL import Image

from sprite_view.utils import format_size, rgb_to_ansi, get_short_hex
from sprite_view.settings import load_settings, save_settings
from sprite_view.ui.about import AboutWindow
from sprite_view.ui.settings import SettingsWindow

_ALIGN_LABELS = ["↖", "↑", "↗", "←", "·", "→", "↙", "↓", "↘"]

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
            .align-active {
                background: alpha(currentColor, 0.25);
                border: 1px solid alpha(currentColor, 0.5);
            }
            .sep-chip {
                border: 1px solid alpha(currentColor, 0.3);
                border-radius: 4px;
                padding: 2px 4px;
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
    _active_instances = []
    _shared_settings_win = None
    _shared_about_win = None

    def __init__(self, file_paths: List[str], selected_file_path: str, title: str) -> None:
        super().__init__(title=title)
        self.set_default_size(780, 580)

        # Initialize style provider
        init_css()

        self._dependent_windows = []
        ImagePreviewWindow._active_instances.append(self)

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

        # Export Actions Group
        if len(self.file_paths) > 1:
            btn_export_png = Gtk.Button(label="Export Frame as PNG...")
            btn_export_png.set_has_frame(False)
            btn_export_png.set_halign(Gtk.Align.START)
            btn_export_png.connect("clicked", self._on_export_png_clicked, menu_popover)
            menu_box.append(btn_export_png)

            btn_export_gif_frame = Gtk.Button(label="Export Frame as GIF...")
            btn_export_gif_frame.set_has_frame(False)
            btn_export_gif_frame.set_halign(Gtk.Align.START)
            btn_export_gif_frame.connect("clicked", self._on_export_gif_frame_clicked, menu_popover)
            menu_box.append(btn_export_gif_frame)

            btn_export_ico = Gtk.Button(label="Export Frame as ICO...")
            btn_export_ico.set_has_frame(False)
            btn_export_ico.set_halign(Gtk.Align.START)
            btn_export_ico.connect("clicked", self._on_export_ico_clicked, menu_popover)
            menu_box.append(btn_export_ico)

            sep_anim = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            menu_box.append(sep_anim)

            btn_export_gif_anim = Gtk.Button(label="Export Animation as GIF...")
            btn_export_gif_anim.set_has_frame(False)
            btn_export_gif_anim.set_halign(Gtk.Align.START)
            btn_export_gif_anim.connect("clicked", self._on_export_gif_anim_clicked, menu_popover)
            menu_box.append(btn_export_gif_anim)

            btn_export_webm = Gtk.Button(label="Export Animation as WebM...")
            btn_export_webm.set_has_frame(False)
            btn_export_webm.set_halign(Gtk.Align.START)
            btn_export_webm.connect("clicked", self._on_export_webm_clicked, menu_popover)
            menu_box.append(btn_export_webm)
        else:
            btn_export_png = Gtk.Button(label="Export as PNG...")
            btn_export_png.set_has_frame(False)
            btn_export_png.set_halign(Gtk.Align.START)
            btn_export_png.connect("clicked", self._on_export_png_clicked, menu_popover)
            menu_box.append(btn_export_png)

            btn_export_gif = Gtk.Button(label="Export as GIF...")
            btn_export_gif.set_has_frame(False)
            btn_export_gif.set_halign(Gtk.Align.START)
            btn_export_gif.connect("clicked", self._on_export_gif_frame_clicked, menu_popover)
            menu_box.append(btn_export_gif)

            btn_export_ico = Gtk.Button(label="Export as ICO...")
            btn_export_ico.set_has_frame(False)
            btn_export_ico.set_halign(Gtk.Align.START)
            btn_export_ico.connect("clicked", self._on_export_ico_clicked, menu_popover)
            menu_box.append(btn_export_ico)

        sep_adv = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        menu_box.append(sep_adv)

        btn_export_adv = Gtk.Button(label="Advanced Export...")
        btn_export_adv.set_has_frame(False)
        btn_export_adv.set_halign(Gtk.Align.START)
        btn_export_adv.connect("clicked", self._on_export_adv_clicked, menu_popover)
        menu_box.append(btn_export_adv)

        sep_menu = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        menu_box.append(sep_menu)

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
        self.thumb_pics: List[Gtk.Picture] = []
        self.original_dimensions = []
        self.original_pixbufs: List[GdkPixbuf.Pixbuf] = []
        self.frame_palettes = []
        self.swatch_colors = [(0, 0, 0, 255)] * 16
        self.selected_color = (0, 0, 0, 255)
        self.current_align = 4  # center
        self.align_btns: List[Gtk.Button] = []
        
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

        # Phase 1: decode originals and extract palettes
        loaded_paths = []
        for path in file_paths:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
                self.original_dimensions.append((pixbuf.get_width(), pixbuf.get_height()))
                self.frame_palettes.append(self._extract_palette_from_pixbuf(pixbuf, 16))
                self.original_pixbufs.append(pixbuf)
                loaded_paths.append(path)
            except Exception as e:
                print(f"Error loading frame {path}: {e}")
        self.file_paths = loaded_paths
        self.first_frame_path = loaded_paths[0] if loaded_paths else ""
        self.dir_path = os.path.dirname(self.first_frame_path) if self.first_frame_path else ""

        # Detect mixed frame sizes and compute bounding-box canvas
        if self.original_dimensions:
            widths = [d[0] for d in self.original_dimensions]
            heights = [d[1] for d in self.original_dimensions]
            self.has_mixed_sizes = len(set(widths)) > 1 or len(set(heights)) > 1
            self.canvas_size = (max(widths), max(heights))
        else:
            self.has_mixed_sizes = False
            self.canvas_size = (0, 0)

        # Phase 2: pad (if mixed) + upscale + create textures
        self._build_textures(self.current_align)

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

        # 3×3 alignment grid — only visible for mixed-size sequences
        align_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        align_box.append(Gtk.Label(label="Align:"))
        align_grid = Gtk.Grid()
        align_grid.set_row_spacing(1)
        align_grid.set_column_spacing(1)
        for i, lbl in enumerate(_ALIGN_LABELS):
            btn = Gtk.Button(label=lbl)
            btn.set_size_request(26, 26)
            btn.connect("clicked", self._on_align_btn_clicked, i)
            align_grid.attach(btn, i % 3, i // 3, 1, 1)
            self.align_btns.append(btn)
        self.align_btns[self.current_align].add_css_class("align-active")
        align_box.append(align_grid)
        align_box.set_visible(self.has_mixed_sizes)
        settings_box.append(align_box)

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
            self.thumb_pics.append(thumb_pic)

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

        # 1. Destroy all registered dependent instance windows
        for win in list(self._dependent_windows):
            try:
                win.destroy()
            except Exception:
                pass
        self._dependent_windows.clear()

        # Remove self from active instances
        if self in ImagePreviewWindow._active_instances:
            ImagePreviewWindow._active_instances.remove(self)

        # 2. Transfer shared singleton windows to another active parent (if any)
        other_parent = None
        for inst in ImagePreviewWindow._active_instances:
            if inst is not self:
                other_parent = inst
                break

        for win in (ImagePreviewWindow._shared_settings_win, ImagePreviewWindow._shared_about_win):
            if win is not None and win.get_transient_for() is self:
                win.set_transient_for(other_parent)

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
        if ImagePreviewWindow._shared_settings_win is not None:
            ImagePreviewWindow._shared_settings_win.present()
            popover.popdown()
            return
        popover.popdown()
        ImagePreviewWindow._shared_settings_win = SettingsWindow(self)
        ImagePreviewWindow._shared_settings_win.connect(
            "destroy", lambda w: setattr(ImagePreviewWindow, "_shared_settings_win", None)
        )
        ImagePreviewWindow._shared_settings_win.present()

    def _on_about_clicked(self, button, popover) -> None:
        if ImagePreviewWindow._shared_about_win is not None:
            ImagePreviewWindow._shared_about_win.present()
            popover.popdown()
            return
        popover.popdown()
        ImagePreviewWindow._shared_about_win = AboutWindow(self)
        ImagePreviewWindow._shared_about_win.connect(
            "destroy", lambda w: setattr(ImagePreviewWindow, "_shared_about_win", None)
        )
        ImagePreviewWindow._shared_about_win.present()

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
            if self.has_mixed_sizes:
                cw, ch = self.canvas_size
                self.lbl_info_dimensions.set_label(f"{orig_w} × {orig_h} px (canvas: {cw} × {ch})")
            else:
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

    def _pad_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf, canvas_w: int, canvas_h: int, align: int) -> GdkPixbuf.Pixbuf:
        src_w = pixbuf.get_width()
        src_h = pixbuf.get_height()
        if src_w == canvas_w and src_h == canvas_h:
            return pixbuf
        canvas = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, canvas_w, canvas_h)
        canvas.fill(0x00000000)
        row, col = align // 3, align % 3
        dx = (canvas_w - src_w) * col // 2
        dy = (canvas_h - src_h) * row // 2
        pixbuf.copy_area(0, 0, src_w, src_h, canvas, dx, dy)
        return canvas

    def _build_textures(self, align: int) -> None:
        self.textures = []
        canvas_w, canvas_h = self.canvas_size
        for i, pixbuf in enumerate(self.original_pixbufs):
            pb = self._pad_pixbuf(pixbuf, canvas_w, canvas_h, align) if self.has_mixed_sizes else pixbuf
            w, h = pb.get_width(), pb.get_height()
            path = self.file_paths[i] if i < len(self.file_paths) else ""
            if path.lower().endswith(('.png', '.gif', '.bmp')) and (w < 1024 or h < 1024):
                scale_factor = max(1, min(1024 // w, 1024 // h))
                if scale_factor > 1:
                    pb = pb.scale_simple(w * scale_factor, h * scale_factor, GdkPixbuf.InterpType.NEAREST)
            self.textures.append(Gdk.Texture.new_for_pixbuf(pb))

    def _on_align_btn_clicked(self, button: Gtk.Button, align: int) -> None:
        if align == self.current_align:
            return
        self.align_btns[self.current_align].remove_css_class("align-active")
        self.current_align = align
        self.align_btns[align].add_css_class("align-active")
        self._build_textures(align)
        self.picture.set_paintable(self.textures[self.current_frame])
        for i, thumb_pic in enumerate(self.thumb_pics):
            thumb_pic.set_paintable(self.textures[i])

    def _get_default_animation_name(self, ext: str) -> str:
        if not self.file_paths:
            return f"animation.{ext}"
        first_file = os.path.basename(self.file_paths[0])
        import re
        seps = self.settings.get("sequence_separators", ["_", "-"])
        sep_alts = "|".join(re.escape(s) for s in seps)
        match = re.match(rf"^(.*)({sep_alts})([0-9]{{2,4}})\.(png|gif|bmp|jpg|jpeg|webp)$", first_file, re.IGNORECASE)
        if match:
            prefix = match.group(1)
            return f"{prefix}.{ext}"
        base, _ = os.path.splitext(first_file)
        return f"{base}.{ext}"

    def _get_pil_image(self, index: int, pad_to_canvas: bool = True) -> "Image.Image":
        from PIL import Image
        path = self.file_paths[index]
        img = Image.open(path)
        
        if img.mode != "RGBA":
            img = img.convert("RGBA")
            
        if pad_to_canvas and self.has_mixed_sizes:
            canvas_w, canvas_h = self.canvas_size
            src_w, src_h = img.size
            
            canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            
            align = self.current_align
            row, col = align // 3, align % 3
            dx = (canvas_w - src_w) * col // 2
            dy = (canvas_h - src_h) * row // 2
            
            canvas.paste(img, (dx, dy))
            return canvas
        return img

    def _export_image_to(self, default_name: str, ext: str, save_func, background: bool = False) -> None:
        dialog = Gtk.FileDialog.new()
        dialog.set_title(f"Export {ext.upper()}")
        dialog.set_initial_name(default_name)
        
        if self.file_paths:
            parent_dir = os.path.dirname(self.file_paths[0])
            gio_folder = Gio.File.new_for_path(parent_dir)
            dialog.set_initial_folder(gio_folder)
            
        store = Gio.ListStore.new(Gtk.FileFilter)
        f = Gtk.FileFilter()
        f.set_name(f"{ext.upper()} Files (*.{ext})")
        f.add_pattern(f"*.{ext}")
        store.append(f)
        dialog.set_filters(store)
        dialog.set_default_filter(f)
        
        def on_saved(dialog_obj, result, user_data):
            try:
                gfile = dialog_obj.save_finish(result)
                if gfile:
                    dest_path = gfile.get_path()
                    if dest_path:
                        if not dest_path.lower().endswith(f".{ext}"):
                            dest_path += f".{ext}"
                        
                        if background:
                            # Run in background (BG job)
                            def bg_save():
                                try:
                                    save_func(dest_path)
                                    GLib.idle_add(self._show_export_success, dest_path)
                                except Exception as ex:
                                    GLib.idle_add(self._show_error_dialog, f"Failed to export: {str(ex)}")
                            
                            import threading
                            threading.Thread(target=bg_save, daemon=True).start()
                        else:
                            # Run in foreground (FG job)
                            try:
                                save_func(dest_path)
                                self._show_export_success(dest_path)
                            except Exception as ex:
                                self._show_error_dialog(f"Failed to export: {str(ex)}")
            except Exception as e:
                err_str = str(e)
                if "dismiss" not in err_str.lower() and "cancel" not in err_str.lower():
                    self._show_error_dialog(f"Failed to export: {err_str}")
                    
        dialog.save(self, None, on_saved, None)

    def _show_export_success(self, path: str) -> None:
        filename = os.path.basename(path)
        try:
            from gi.repository import Notify
            if not Notify.is_initted():
                Notify.init("NautilusPreview")
            n = Notify.Notification.new("Export Successful", f"Exported {filename}", "info")
            n.show()
        except Exception:
            alert = Gtk.AlertDialog.new()
            alert.set_message(f"Successfully exported to:\n{path}")
            alert.show(self)

    def _show_error_dialog(self, message: str) -> None:
        alert = Gtk.AlertDialog.new()
        alert.set_message(message)
        alert.show(self)

    def _on_export_png_clicked(self, button, popover) -> None:
        popover.popdown()
        current_path = self.file_paths[self.current_frame]
        base = os.path.basename(current_path)
        name, _ = os.path.splitext(base)
        default_name = f"{name}.png"
        
        def save_png(dest_path):
            img = self._get_pil_image(self.current_frame, pad_to_canvas=True)
            img.save(dest_path, "PNG")
            
        self._export_image_to(default_name, "png", save_png)

    def _on_export_gif_frame_clicked(self, button, popover) -> None:
        popover.popdown()
        current_path = self.file_paths[self.current_frame]
        base = os.path.basename(current_path)
        name, _ = os.path.splitext(base)
        default_name = f"{name}.gif"
        
        def save_gif_frame(dest_path):
            img = self._get_pil_image(self.current_frame, pad_to_canvas=True)
            img.save(dest_path, "GIF")
            
        self._export_image_to(default_name, "gif", save_gif_frame)

    def _on_export_ico_clicked(self, button, popover) -> None:
        popover.popdown()
        current_path = self.file_paths[self.current_frame]
        base = os.path.basename(current_path)
        name, _ = os.path.splitext(base)
        default_name = f"{name}.ico"
        
        def save_ico(dest_path):
            img = self._get_pil_image(self.current_frame, pad_to_canvas=True)
            w, h = img.size
            if w > 256 or h > 256:
                ratio = min(256 / w, 256 / h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img.save(dest_path, format="ICO")
            
        self._export_image_to(default_name, "ico", save_ico)

    def _on_export_gif_anim_clicked(self, button, popover) -> None:
        popover.popdown()
        default_name = self._get_default_animation_name("gif")
        
        def save_gif_anim(dest_path):
            images = [self._get_pil_image(i, pad_to_canvas=True) for i in range(len(self.file_paths))]
            fps = self.fps_spin.get_value()
            duration_ms = int(1000.0 / fps)
            
            images[0].save(
                dest_path,
                "GIF",
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=0
            )
            
        self._export_image_to(default_name, "gif", save_gif_anim)

    def _on_export_webm_clicked(self, button, popover) -> None:
        popover.popdown()
        default_name = self._get_default_animation_name("webm")
        
        def save_webm(dest_path):
            import tempfile
            import subprocess
            
            fps = self.fps_spin.get_value()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                for i in range(len(self.file_paths)):
                    img = self._get_pil_image(i, pad_to_canvas=True)
                    frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
                    img.save(frame_path, "PNG")
                    
                cmd = [
                    "ffmpeg", "-y",
                    "-framerate", str(fps),
                    "-i", os.path.join(tmpdir, "frame_%04d.png"),
                    "-c:v", "libvpx-vp9",
                    "-pix_fmt", "yuva420p",
                    dest_path
                ]
                
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode != 0:
                    raise Exception(f"ffmpeg error: {res.stderr.decode()}")
                    
        self._export_image_to(default_name, "webm", save_webm)

    def _on_export_adv_clicked(self, button, popover) -> None:
        if hasattr(self, "_export_adv_win") and self._export_adv_win is not None:
            self._export_adv_win.present()
            popover.popdown()
            return
        popover.popdown()
        self._export_adv_win = ExportOptionsWindow(self)
        self._export_adv_win.connect(
            "destroy", lambda w: setattr(self, "_export_adv_win", None)
        )
        self._export_adv_win.present()

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


class DependentWindow(Gtk.Window):
    def __init__(self, parent_win, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_transient_for(parent_win)
        
        # Register with parent preview window
        if hasattr(parent_win, "_dependent_windows"):
            parent_win._dependent_windows.append(self)
            
        self.connect("destroy", self._on_dependent_destroy, parent_win)
        
    def _on_dependent_destroy(self, widget, parent_win) -> None:
        if hasattr(parent_win, "_dependent_windows") and self in parent_win._dependent_windows:
            parent_win._dependent_windows.remove(self)


class ExportOptionsWindow(DependentWindow):
    def __init__(self, parent_win) -> None:
        super().__init__(parent_win, title="Advanced Export Options")
        self.set_default_size(360, 440)
        self.parent_win = parent_win

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        self.set_child(box)

        # 1. Format Selection Row
        format_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        fmt_lbl = Gtk.Label(label="Export Format:")
        fmt_lbl.set_halign(Gtk.Align.START)
        fmt_lbl.set_hexpand(True)
        format_row.append(fmt_lbl)
        
        self.formats = ["PNG (Current Frame)", "GIF (Current Frame)", "ICO (Current Frame)"]
        self.format_keys = ["png_frame", "gif_frame", "ico_frame"]
        
        if len(self.parent_win.file_paths) > 1:
            self.formats.extend(["GIF (Animation)", "WebM (Animation)"])
            self.format_keys.extend(["gif_anim", "webm_anim"])
            
        self.format_dropdown = Gtk.DropDown.new_from_strings(self.formats)
        self.format_dropdown.set_selected(0)
        format_row.append(self.format_dropdown)
        box.append(format_row)
        
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep1)

        # 2. Scaling Options Section
        scale_lbl_title = Gtk.Label()
        scale_lbl_title.set_markup("<b>Scaling Options</b>")
        scale_lbl_title.set_halign(Gtk.Align.START)
        box.append(scale_lbl_title)
        
        scale_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        sc_lbl = Gtk.Label(label="Scale:")
        sc_lbl.set_halign(Gtk.Align.START)
        sc_lbl.set_hexpand(True)
        scale_row.append(sc_lbl)
        
        self.scale_dropdown = Gtk.DropDown.new_from_strings(["1x (Original)", "2x", "4x", "8x", "Custom..."])
        self.scale_dropdown.set_selected(0)
        self.scale_dropdown.connect("notify::selected", self._on_scale_changed)
        scale_row.append(self.scale_dropdown)
        
        adj_scale = Gtk.Adjustment(value=1.0, lower=1.0, upper=32.0, step_increment=1.0)
        self.scale_spin = Gtk.SpinButton(adjustment=adj_scale, climb_rate=1.0, digits=0)
        self.scale_spin.set_visible(False)
        scale_row.append(self.scale_spin)
        box.append(scale_row)
        
        filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        flt_lbl = Gtk.Label(label="Filter:")
        flt_lbl.set_halign(Gtk.Align.START)
        flt_lbl.set_hexpand(True)
        filter_row.append(flt_lbl)
        
        self.filter_dropdown = Gtk.DropDown.new_from_strings(["Nearest Neighbor", "Bilinear (Linear)"])
        self.filter_dropdown.set_selected(0)
        filter_row.append(self.filter_dropdown)
        box.append(filter_row)
        
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep2)

        # 3. Palette Options Section
        palette_lbl_title = Gtk.Label()
        palette_lbl_title.set_markup("<b>Palette Options</b>")
        palette_lbl_title.set_halign(Gtk.Align.START)
        box.append(palette_lbl_title)
        
        self.reduce_chk = Gtk.CheckButton(label="Reduce Palette")
        self.reduce_chk.connect("toggled", self._on_reduce_toggled)
        box.append(self.reduce_chk)
        
        self.palette_sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.palette_sub_box.set_margin_start(16)
        self.palette_sub_box.set_sensitive(False)
        
        colors_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        col_lbl = Gtk.Label(label="Max Colors:")
        col_lbl.set_halign(Gtk.Align.START)
        col_lbl.set_hexpand(True)
        colors_row.append(col_lbl)
        
        adj_colors = Gtk.Adjustment(value=16.0, lower=2.0, upper=256.0, step_increment=1.0)
        self.colors_spin = Gtk.SpinButton(adjustment=adj_colors, climb_rate=1.0, digits=0)
        colors_row.append(self.colors_spin)
        self.palette_sub_box.append(colors_row)
        
        self.shared_chk = Gtk.CheckButton(label="Shared Palette (Across Frames)")
        self.shared_chk.set_active(True)
        if len(self.parent_win.file_paths) <= 1:
            self.shared_chk.set_sensitive(False)
            self.shared_chk.set_active(False)
        self.palette_sub_box.append(self.shared_chk)
        box.append(self.palette_sub_box)
        
        self.ansi_chk = Gtk.CheckButton(label="Map to ANSI 256 Colors")
        self.ansi_chk.connect("toggled", self._on_ansi_toggled)
        box.append(self.ansi_chk)

        self.bg_chk = Gtk.CheckButton(label="Export in Background")
        self.bg_chk.set_active(False)
        box.append(self.bg_chk)
        
        sep3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(sep3)

        # 4. Action Buttons (Cancel / Export)
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_row.set_halign(Gtk.Align.END)
        
        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.connect("clicked", lambda b: self.close())
        btn_row.append(btn_cancel)
        
        btn_export = Gtk.Button(label="Export...")
        btn_export.add_css_class("suggested-action")
        btn_export.connect("clicked", self._on_export_clicked)
        btn_row.append(btn_export)
        box.append(btn_row)

        # Close window when ESC key is pressed
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_scale_changed(self, dropdown, pspec) -> None:
        idx = dropdown.get_selected()
        self.scale_spin.set_visible(idx == 4)

    def _on_reduce_toggled(self, button) -> None:
        active = button.get_active()
        self.palette_sub_box.set_sensitive(active)
        if active:
            self.ansi_chk.set_active(False)

    def _on_ansi_toggled(self, button) -> None:
        active = button.get_active()
        if active:
            self.reduce_chk.set_active(False)

    def _apply_ansi_mapping(self, img: "Image.Image") -> "Image.Image":
        from PIL import Image
        from sprite_view.utils import get_ansi_256_colors
        
        ansi_colors = get_ansi_256_colors()
        palette_data = []
        for r, g, b in ansi_colors:
            palette_data.extend([r, g, b])
        while len(palette_data) < 768:
            palette_data.append(0)
            
        ansi_p_img = Image.new('P', (1, 1))
        ansi_p_img.putpalette(palette_data)
        
        alpha = img.getchannel('A')
        rgb_img = img.convert('RGB')
        quant = rgb_img.quantize(palette=ansi_p_img, dither=Image.Dither.NONE)
        rgba = quant.convert('RGBA')
        rgba.putalpha(alpha)
        return rgba

    def _apply_shared_palette_reduction(self, frames: list, max_colors: int) -> list:
        from PIL import Image
        widths, heights = zip(*(img.size for img in frames))
        max_w = max(widths)
        total_h = sum(heights)
        
        combined = Image.new("RGBA", (max_w, total_h), (0, 0, 0, 0))
        y = 0
        for img in frames:
            combined.paste(img, (0, y))
            y += img.height
            
        master_p = combined.quantize(colors=max_colors)
        
        quantized_frames = []
        for img in frames:
            alpha = img.getchannel('A')
            rgb_img = img.convert('RGB')
            quant = rgb_img.quantize(palette=master_p, dither=Image.Dither.NONE)
            rgba = quant.convert('RGBA')
            rgba.putalpha(alpha)
            quantized_frames.append(rgba)
            
        return quantized_frames

    def _on_export_clicked(self, button) -> None:
        fmt_idx = self.format_dropdown.get_selected()
        fmt_key = self.format_keys[fmt_idx]
        
        ext = "png"
        if "gif" in fmt_key:
            ext = "gif"
        elif "ico" in fmt_key:
            ext = "ico"
        elif "webm" in fmt_key:
            ext = "webm"
            
        if "anim" in fmt_key:
            default_name = self.parent_win._get_default_animation_name(ext)
        else:
            current_path = self.parent_win.file_paths[self.parent_win.current_frame]
            base = os.path.basename(current_path)
            name, _ = os.path.splitext(base)
            default_name = f"{name}.{ext}"
            
        scale_idx = self.scale_dropdown.get_selected()
        if scale_idx == 0:
            scale_val = 1
        elif scale_idx == 1:
            scale_val = 2
        elif scale_idx == 2:
            scale_val = 4
        elif scale_idx == 3:
            scale_val = 8
        else:
            scale_val = int(self.scale_spin.get_value())
            
        filter_idx = self.filter_dropdown.get_selected()
        filter_type = "nearest" if filter_idx == 0 else "linear"
        
        reduce_palette = self.reduce_chk.get_active()
        max_colors = int(self.colors_spin.get_value())
        shared_palette = self.shared_chk.get_active() and len(self.parent_win.file_paths) > 1
        
        map_ansi = self.ansi_chk.get_active()
        
        def process_and_save(dest_path):
            from PIL import Image
            
            # 1. Get original 1x frames
            frames = [self.parent_win._get_pil_image(i, pad_to_canvas=True) for i in range(len(self.parent_win.file_paths))]
            
            # 2. Apply color quantization / mapping at 1x resolution with no dithering
            if reduce_palette:
                if shared_palette and len(frames) > 1:
                    frames = self._apply_shared_palette_reduction(frames, max_colors)
                else:
                    new_frames = []
                    for img in frames:
                        alpha = img.getchannel('A')
                        rgb_img = img.convert('RGB')
                        quant = rgb_img.quantize(colors=max_colors, dither=Image.Dither.NONE)
                        rgba = quant.convert('RGBA')
                        rgba.putalpha(alpha)
                        new_frames.append(rgba)
                    frames = new_frames
            elif map_ansi:
                frames = [self._apply_ansi_mapping(img) for img in frames]
                
            # 3. Scale up the processed frames
            if scale_val != 1:
                resample = Image.Resampling.NEAREST if filter_type == "nearest" else Image.Resampling.BILINEAR
                new_frames = []
                for img in frames:
                    w, h = img.size
                    new_frames.append(img.resize((w * scale_val, h * scale_val), resample))
                frames = new_frames
                
            # 4. Save to destination path
            if "anim" in fmt_key:
                fps = self.parent_win.fps_spin.get_value()
                duration_ms = int(1000.0 / fps)
                
                if ext == "gif":
                    frames[0].save(
                        dest_path,
                        "GIF",
                        save_all=True,
                        append_images=frames[1:],
                        duration=duration_ms,
                        loop=0
                    )
                elif ext == "webm":
                    import tempfile
                    import subprocess
                    
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for i, frame in enumerate(frames):
                            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
                            frame.save(frame_path, "PNG")
                            
                        cmd = [
                            "ffmpeg", "-y",
                            "-framerate", str(fps),
                            "-i", os.path.join(tmpdir, "frame_%04d.png"),
                            "-c:v", "libvpx-vp9",
                            "-pix_fmt", "yuva420p",
                            dest_path
                        ]
                        res = subprocess.run(cmd, capture_output=True)
                        if res.returncode != 0:
                            raise Exception(f"ffmpeg error: {res.stderr.decode()}")
            else:
                # Single frame export
                frame = frames[self.parent_win.current_frame]
                
                if ext == "png":
                    frame.save(dest_path, "PNG")
                elif ext == "gif":
                    frame.save(dest_path, "GIF")
                elif ext == "ico":
                    w, h = frame.size
                    if w > 256 or h > 256:
                        ratio = min(256 / w, 256 / h)
                        new_w, new_h = int(w * ratio), int(h * ratio)
                        resample = Image.Resampling.NEAREST if filter_type == "nearest" else Image.Resampling.LANCZOS
                        frame = frame.resize((new_w, new_h), resample)
                    frame.save(dest_path, format="ICO")
                    
        run_in_bg = self.bg_chk.get_active()
        self.close()
        self.parent_win._export_image_to(default_name, ext, process_and_save, background=run_in_bg)
