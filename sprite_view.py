# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
import gi
from collections import Counter
gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '4.0')
from gi.repository import Nautilus, GObject, Notify, Gtk, Gdk, GdkPixbuf, GLib
from typing import List

# Load CSS globally to style active frames in sprite sheets
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
    Gdk.Display.get_default(),
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

def format_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{bytes_size} B"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def find_sprite_frames(file_path: str) -> List[str]:
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    
    # Matches patterns like prefix_0001.png or prefix_0001.gif
    match = re.match(r"^(.*)_([0-9]{4})\.(png|gif|bmp|jpg|jpeg|webp)$", base_name, re.IGNORECASE)
    if not match:
        return [file_path]
        
    prefix = match.group(1)
    ext = match.group(3)
    
    pattern = re.compile(rf"^{re.escape(prefix)}_([0-9]{{4}})\.{ext}$", re.IGNORECASE)
    
    frames = []
    try:
        for f in os.listdir(dir_name):
            if pattern.match(f):
                frames.append(os.path.join(dir_name, f))
    except Exception:
        return [file_path]
        
    frames.sort()
    return frames if len(frames) > 1 else [file_path]

def get_ansi_256_colors() -> List[tuple]:
    colors = []
    # 0-7: standard low-intensity colors
    std_colors = [
        (0, 0, 0),        # 0: black
        (128, 0, 0),      # 1: red
        (0, 128, 0),      # 2: green
        (128, 128, 0),    # 3: yellow
        (0, 0, 128),      # 4: blue
        (128, 0, 128),    # 5: magenta
        (0, 128, 128),    # 6: cyan
        (192, 192, 192)   # 7: white
    ]
    colors.extend(std_colors)
    
    # 8-15: high-intensity colors
    bright_colors = [
        (128, 128, 128),  # 8: bright black (gray)
        (255, 0, 0),      # 9: bright red
        (0, 255, 0),      # 10: bright green
        (255, 255, 0),    # 11: bright yellow
        (0, 0, 255),      # 12: bright blue
        (255, 0, 255),    # 13: bright magenta
        (0, 255, 255),    # 14: bright cyan
        (255, 255, 255)   # 15: bright white
    ]
    colors.extend(bright_colors)
    
    # 16-231: 6x6x6 color cube
    steps = [0, 95, 135, 175, 215, 255]
    for r in steps:
        for g in steps:
            for b in steps:
                colors.append((r, g, b))
                
    # 232-255: grayscale ramp
    for i in range(24):
        val = 8 + i * 10
        colors.append((val, val, val))
        
    return colors

def describe_cube_color(r: int, g: int, b: int) -> str:
    intensities = ["None", "Very Dark", "Dark", "Medium", "Light", "Bright"]
    
    if r == g == b:
        return f"{intensities[r]} Gray"
        
    max_val = max(r, g, b)
    if r == max_val and g == max_val:
        return f"{intensities[r]} Yellow"
    if r == max_val and b == max_val:
        return f"{intensities[r]} Magenta"
    if g == max_val and b == max_val:
        return f"{intensities[g]} Cyan"
    
    if r == max_val:
        if g > b:
            return f"{intensities[r]} Orange" if g > 1 else f"{intensities[r]} Red"
        return f"{intensities[r]} Red-Purple"
    elif g == max_val:
        if r > b:
            return f"{intensities[g]} Yellow-Green"
        return f"{intensities[g]} Green"
    else:
        if r > g:
            return f"{intensities[b]} Purple"
        return f"{intensities[b]} Blue"

def rgb_to_ansi(r: int, g: int, b: int) -> tuple:
    ansi_colors = get_ansi_256_colors()
    min_dist = float('inf')
    closest_idx = 0
    
    for idx, (ar, ag, ab) in enumerate(ansi_colors):
        dist = (r - ar) ** 2 + (g - ag) ** 2 + (b - ab) ** 2
        if dist < min_dist:
            min_dist = dist
            closest_idx = idx
            
    ansi_names = {
        0: "Black", 1: "Red", 2: "Green", 3: "Yellow", 4: "Blue", 5: "Magenta", 6: "Cyan", 7: "White",
        8: "Bright Black (Gray)", 9: "Bright Red", 10: "Bright Green", 11: "Bright Yellow",
        12: "Bright Blue", 13: "Bright Magenta", 14: "Bright Cyan", 15: "Bright White"
    }
    
    if closest_idx in ansi_names:
        name = ansi_names[closest_idx]
    elif closest_idx >= 232:
        step = closest_idx - 232
        name = f"Gray (Step {step}/23)"
    else:
        cube_idx = closest_idx - 16
        b_val = cube_idx % 6
        g_val = (cube_idx // 6) % 6
        r_val = cube_idx // 36
        name = describe_cube_color(r_val, g_val, b_val)
        
    return closest_idx, name

def get_short_hex(r: int, g: int, b: int) -> str:
    hex_long = f"#{r:02x}{g:02x}{b:02x}"
    if (r % 17 == 0) and (g % 17 == 0) and (b % 17 == 0):
        return f"#{r//17:x}{g//17:x}{b//17:x}"
    return hex_long


CONFIG_PATH = os.path.expanduser("~/.config/nautilus-sprite-view/config.json")

def load_settings() -> dict:
    import json
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return {
        "default_fps": 15.0,
        "default_mode": 0,
        "remember_fps": True,
        "remember_scope": "sheet",
        "saved_fps": {}
    }

def save_settings(settings: dict) -> None:
    import json
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")


class ImagePreviewWindow(Gtk.Window):
    def __init__(self, file_paths: List[str], selected_file_path: str, title: str) -> None:
        super().__init__(title=title)
        self.set_default_size(780, 580)

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

        # Create popover content for settings
        popover = Gtk.Popover()
        popover.set_autohide(True)
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        popover_box.set_margin_start(12)
        popover_box.set_margin_end(12)
        popover_box.set_margin_top(12)
        popover_box.set_margin_bottom(12)

        settings_title = Gtk.Label()
        settings_title.set_markup("<b>Settings</b>")
        settings_title.set_halign(Gtk.Align.START)
        popover_box.append(settings_title)

        # 1. Default FPS Row
        default_fps_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        df_lbl = Gtk.Label(label="Default FPS:")
        df_lbl.set_halign(Gtk.Align.START)
        default_fps_row.append(df_lbl)

        df_adj = Gtk.Adjustment(value=self.settings.get("default_fps", 15.0), lower=1.0, upper=60.0, step_increment=1.0)
        self.df_spin = Gtk.SpinButton(adjustment=df_adj, climb_rate=1.0, digits=0)
        self.df_spin.connect("value-changed", self._on_default_fps_changed)
        default_fps_row.append(self.df_spin)
        popover_box.append(default_fps_row)

        # Separator
        sep_set = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        popover_box.append(sep_set)

        # 2. Remember FPS CheckButton
        self.remember_check = Gtk.CheckButton(label="Remember FPS")
        self.remember_check.set_active(self.settings.get("remember_fps", True))
        self.remember_check.connect("toggled", self._on_remember_changed)
        popover_box.append(self.remember_check)

        # 3. Remember Scope Row
        scope_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        sc_lbl = Gtk.Label(label="Scope:")
        sc_lbl.set_halign(Gtk.Align.START)
        scope_row.append(sc_lbl)

        self.scope_dropdown = Gtk.DropDown.new_from_strings(["Per Sheet", "Per Directory"])
        current_scope = self.settings.get("remember_scope", "sheet")
        self.scope_dropdown.set_selected(0 if current_scope == "sheet" else 1)
        self.scope_dropdown.set_sensitive(self.settings.get("remember_fps", True))
        self.scope_dropdown.connect("notify::selected", self._on_remember_scope_changed)
        scope_row.append(self.scope_dropdown)
        popover_box.append(scope_row)

        # Separator
        sep_mode = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        popover_box.append(sep_mode)

        # 4. Default Mode Row
        default_mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dm_lbl = Gtk.Label(label="Default Mode:")
        dm_lbl.set_halign(Gtk.Align.START)
        default_mode_row.append(dm_lbl)

        self.default_mode_dropdown = Gtk.DropDown.new_from_strings(["Loop", "Ping-Pong", "Once"])
        self.default_mode_dropdown.set_selected(self.settings.get("default_mode", 0))
        self.default_mode_dropdown.connect("notify::selected", self._on_default_mode_changed)
        default_mode_row.append(self.default_mode_dropdown)
        popover_box.append(default_mode_row)

        popover.set_child(popover_box)
        menu_button.set_popover(popover)
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
            v_lbl = Gtk.Label(label="-")
            v_lbl.set_halign(Gtk.Align.START)
            v_lbl.set_selectable(True)
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
            v_lbl = Gtk.Label(label="-")
            v_lbl.set_halign(Gtk.Align.START)
            v_lbl.set_selectable(True)
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

    def _on_default_fps_changed(self, spin_button) -> None:
        self.settings["default_fps"] = spin_button.get_value()
        save_settings(self.settings)

    def _on_remember_changed(self, check_button) -> None:
        active = check_button.get_active()
        self.settings["remember_fps"] = active
        self.scope_dropdown.set_sensitive(active)
        
        # Grab focus back to check button to prevent popover grab/focus loss when disabling dropdown
        check_button.grab_focus()
        
        if active and hasattr(self, "fps_spin") and self.first_frame_path:
            current_fps = self.fps_spin.get_value()
            scope = self.settings.get("remember_scope", "sheet")
            key = f"sheet:{self.first_frame_path}" if scope == "sheet" else f"dir:{self.dir_path}"
            self.settings.setdefault("saved_fps", {})[key] = current_fps
            
        save_settings(self.settings)

    def _on_remember_scope_changed(self, dropdown, pspec) -> None:
        selected_idx = dropdown.get_selected()
        scope = "sheet" if selected_idx == 0 else "dir"
        self.settings["remember_scope"] = scope
        
        # Grab focus back to restore Popover's active grab
        dropdown.grab_focus()
        
        if self.settings.get("remember_fps", True) and hasattr(self, "fps_spin") and self.first_frame_path:
            current_fps = self.fps_spin.get_value()
            key = f"sheet:{self.first_frame_path}" if scope == "sheet" else f"dir:{self.dir_path}"
            self.settings.setdefault("saved_fps", {})[key] = current_fps
            
        save_settings(self.settings)

    def _on_default_mode_changed(self, dropdown, pspec) -> None:
        self.settings["default_mode"] = dropdown.get_selected()
        save_settings(self.settings)
        
        # Grab focus back to restore Popover's active grab
        dropdown.grab_focus()

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


class NautilusPreview(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self) -> None:
        super().__init__()
        Notify.init("NautilusPreview")
        self.preview_windows: List[Gtk.Window] = []

    def _show_notification(self, title: str, message: str) -> None:
        notification = Notify.Notification.new(title, message, "info")
        notification.show()

    def _on_preview_activated(self, menu: Nautilus.MenuItem, files: List[Nautilus.FileInfo]) -> None:
        if len(files) == 1:
            file = files[0]
            name = file.get_name()
            location = file.get_location()
            if not location:
                self._show_notification("Preview Error", f"Could not get location for {name}")
                return

            file_path = location.get_path()
            if not file_path or not os.path.exists(file_path):
                self._show_notification("Preview Error", f"File path does not exist: {file_path}")
                return

            # Find all sprite frames
            frames = find_sprite_frames(file_path)
            selected_file_path = file_path
            title = f"Preview: {os.path.basename(file_path)}"
        else:
            frames = []
            for file in files:
                location = file.get_location()
                if location:
                    path = location.get_path()
                    if path and os.path.exists(path):
                        frames.append(path)

            if not frames:
                self._show_notification("Preview Error", "No valid files found for preview")
                return

            # Sort the frames alphabetically so they play in the correct chronological/numerical sequence
            frames.sort()
            selected_file_path = frames[0]
            title = f"Preview: {len(frames)} Selected Frames"

        try:
            win = ImagePreviewWindow(frames, selected_file_path, title)
            self.preview_windows.append(win)
            win.connect("destroy", lambda w: self.preview_windows.remove(w))
            win.present()
        except Exception as e:
            self._show_notification("Preview Error", f"Failed to open preview: {str(e)}")

    def get_file_items(self, *args) -> List[Nautilus.MenuItem]:
        files = args[-1]
        if not files:
            return []

        # Verify all selected items are valid image files (none are directories)
        image_files = []
        for file in files:
            if file.is_directory():
                return []
            name = file.get_name().lower()
            if not name.endswith(('.png', '.gif', '.bmp', '.jpg', '.jpeg', '.webp')):
                return []
            location = file.get_location()
            if not location or not location.get_path():
                return []
            image_files.append(file)

        if len(image_files) == 1:
            file = image_files[0]
            file_path = file.get_location().get_path()
            label = "Preview Image"
            if len(find_sprite_frames(file_path)) > 1:
                label = "Preview Sprite Sheet"

            item = Nautilus.MenuItem(
                name="NautilusPreview::preview_image",
                label=label,
                tip=f"Open preview for {file.get_name()}"
            )
            item.connect("activate", self._on_preview_activated, [file])
            return [item]
        elif len(image_files) > 1:
            item = Nautilus.MenuItem(
                name="NautilusPreview::preview_image",
                label="Preview Animation",
                tip="Open animation preview for selected frames"
            )
            item.connect("activate", self._on_preview_activated, image_files)
            return [item]

        return []

    def get_background_items(self, *args) -> List[Nautilus.MenuItem]:
        return []
