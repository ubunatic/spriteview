# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from typing import List

def format_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{bytes_size} B"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def template_to_regex(template: str) -> str:
    if "{number}" not in template:
        raise ValueError("Pattern must contain '{number}' placeholder")
    
    if "{prefix}" not in template:
        template = "{prefix}" + template
        
    t = template.replace("{prefix}", "PREFIXPLACEHOLDER").replace("{number}", "NUMBERPLACEHOLDER")
    escaped = re.escape(t)
    regex_str = (
        escaped
        .replace("PREFIXPLACEHOLDER", "(?P<prefix>.*?)")
        .replace("NUMBERPLACEHOLDER", "(?P<num>[0-9]{2,4})")
    )
    return rf"^{regex_str}\.(?P<ext>png|gif|bmp|jpg|jpeg|webp)$"

def find_sprite_frames(file_path: str, separators: List[str] = None, patterns: List[str] = None) -> List[str]:
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)

    if patterns:
        for pat_str in patterns:
            try:
                pat_regex_str = template_to_regex(pat_str)
                pat = re.compile(pat_regex_str, re.IGNORECASE)
                if "num" not in pat.groupindex:
                    continue
                match = pat.match(base_name)
                if match:
                    start, end = match.span("num")
                    digit_len = end - start
                    prefix_part = base_name[:start]
                    suffix_part = base_name[end:]
                    
                    search_pat = re.compile(
                        rf"^{re.escape(prefix_part)}([0-9]{{{digit_len}}}){re.escape(suffix_part)}$",
                        re.IGNORECASE
                    )
                    
                    frames = []
                    for f in os.listdir(dir_name):
                        if search_pat.match(f):
                            frames.append(os.path.join(dir_name, f))
                    
                    frames.sort()
                    if len(frames) > 1:
                        return frames
            except Exception as e:
                print(f"Error matching pattern '{pat_str}': {e}")

    if not separators:
        separators = ["_", "-"]

    # Build alternation from separator list so users can configure extra separators
    sep_alts = "|".join(re.escape(s) for s in separators)
    match = re.match(rf"^(.*)({sep_alts})([0-9]{{2,4}})\.(png|gif|bmp|jpg|jpeg|webp)$", base_name, re.IGNORECASE)
    if not match:
        return [file_path]

    prefix = match.group(1)
    sep = match.group(2)
    ext = match.group(4)
    digit_len = len(match.group(3))

    pattern = re.compile(rf"^{re.escape(prefix)}{re.escape(sep)}([0-9]{{{digit_len}}})\.{ext}$", re.IGNORECASE)
    
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


class ViewTransform:
    """Explicit coordinate transform between natural-resolution source image space
    and displayed widget view space."""

    def __init__(
        self,
        x_min: float,
        y_min: float,
        scale_src_to_view: float,
        canvas_w: int,
        canvas_h: int,
        canvas_to_texture_scale: float = 1.0,
    ) -> None:
        self.x_min = float(x_min)
        self.y_min = float(y_min)
        self.scale_src_to_view = float(scale_src_to_view)
        self.canvas_w = int(canvas_w)
        self.canvas_h = int(canvas_h)
        self.canvas_to_texture_scale = float(canvas_to_texture_scale)

    @property
    def x_max(self) -> float:
        return self.x_min + self.canvas_w * self.scale_src_to_view

    @property
    def y_max(self) -> float:
        return self.y_min + self.canvas_h * self.scale_src_to_view

    @property
    def view_w(self) -> float:
        return self.canvas_w * self.scale_src_to_view

    @property
    def view_h(self) -> float:
        return self.canvas_h * self.scale_src_to_view

    @property
    def scale(self) -> float:
        """Texture-to-widget scale for backward compatibility with legacy tests."""
        if self.canvas_to_texture_scale > 0:
            return self.scale_src_to_view / self.canvas_to_texture_scale
        return self.scale_src_to_view

    def source_to_view(self, src_x: float, src_y: float) -> tuple[float, float]:
        """Convert source coordinate (src_x, src_y) to view coordinate."""
        view_x = self.x_min + src_x * self.scale_src_to_view
        view_y = self.y_min + src_y * self.scale_src_to_view
        return view_x, view_y

    def source_box_to_view(
        self, box: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        """Convert source crop box (x1, y1, x2, y2) to view rectangle (vx1, vy1, vx2, vy2)."""
        if not box:
            return 0.0, 0.0, 0.0, 0.0
        x1, y1, x2, y2 = box
        vx1, vy1 = self.source_to_view(x1, y1)
        vx2, vy2 = self.source_to_view(x2, y2)
        return min(vx1, vx2), min(vy1, vy2), max(vx1, vx2), max(vy1, vy2)

    def view_to_source(self, view_x: float, view_y: float) -> tuple[float, float]:
        """Convert view coordinate (view_x, view_y) to float source coordinate."""
        if self.scale_src_to_view == 0:
            return 0.0, 0.0
        src_x = (view_x - self.x_min) / self.scale_src_to_view
        src_y = (view_y - self.y_min) / self.scale_src_to_view
        return src_x, src_y

    def view_to_source_pixel(
        self, view_x: float, view_y: float, clamp: bool = True
    ) -> tuple[int, int]:
        """Convert view coordinate to discrete integer source pixel coordinate."""
        src_x, src_y = self.view_to_source(view_x, view_y)
        px = int(round(src_x))
        py = int(round(src_y))
        if clamp:
            px = max(0, min(self.canvas_w, px))
            py = max(0, min(self.canvas_h, py))
        return px, py

    def view_delta_to_source(
        self, delta_view_x: float, delta_view_y: float
    ) -> tuple[float, float]:
        """Convert view coordinate delta/offset to source coordinate delta."""
        if self.scale_src_to_view == 0:
            return 0.0, 0.0
        return (
            delta_view_x / self.scale_src_to_view,
            delta_view_y / self.scale_src_to_view,
        )

    def contains_view_point(self, view_x: float, view_y: float) -> bool:
        """Check if a view point falls within rendered canvas bounds in view space."""
        return (
            self.x_min <= view_x <= self.x_max
            and self.y_min <= view_y <= self.y_max
        )

    def __getitem__(self, item: str):
        """Dict-style access for backward compatibility with existing tests/mocks."""
        d = {
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'w': self.view_w,
            'h': self.view_h,
            'scale': self.scale,
            'scale_src_to_view': self.scale_src_to_view,
            'canvas_to_texture_scale': self.canvas_to_texture_scale,
        }
        if item in d:
            return d[item]
        raise KeyError(item)

    def get(self, item: str, default=None):
        try:
            return self[item]
        except KeyError:
            return default
