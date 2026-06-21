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

def find_sprite_frames(file_path: str) -> List[str]:
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    
    # Matches patterns like prefix_0001.png, prefix_001.png, prefix_01.png
    match = re.match(r"^(.*)_([0-9]{2,4})\.(png|gif|bmp|jpg|jpeg|webp)$", base_name, re.IGNORECASE)
    if not match:
        return [file_path]

    prefix = match.group(1)
    ext = match.group(3)
    digit_len = len(match.group(2))

    pattern = re.compile(rf"^{re.escape(prefix)}_([0-9]{{{digit_len}}})\.{ext}$", re.IGNORECASE)
    
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
