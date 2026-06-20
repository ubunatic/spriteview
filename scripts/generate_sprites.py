#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw

def create_rupee_frame(frame_index: int) -> Image.Image:
    # 16x16 RGBA image with transparent background
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 4 frames of horizontal rotation
    widths = [10, 7, 3, 7]
    w = widths[frame_index]
    
    cx = 8
    
    # Outer polygon vertices (dark green border)
    x0_top = cx - w // 4
    x1_top = cx + w // 4
    x_mid_right = cx + w // 2
    x_mid_left = cx - w // 2
    x0_bot = cx - w // 4
    x1_bot = cx + w // 4
    
    y_top = 2
    y_mid = 7
    y_bot = 13
    
    border_color = (22, 60, 23, 255)       # #163c17 dark green
    left_color = (34, 125, 36, 255)        # #227d24 medium green
    right_color = (105, 226, 106, 255)     # #69e26a light green
    shine_color = (200, 255, 201, 255)     # #c8ffc9 very light green
    white = (255, 255, 255, 255)
    
    # Draw border
    outer_poly = [
        (x0_top, y_top),
        (x1_top, y_top),
        (x_mid_right, y_mid),
        (x1_bot, y_bot),
        (x0_bot, y_bot),
        (x_mid_left, y_mid)
    ]
    draw.polygon(outer_poly, fill=border_color)
    
    # Draw inner facets if width is wide enough
    if w > 3:
        # Left facet
        left_poly = [
            (x0_top + 1, y_top + 1),
            (cx, y_top + 1),
            (cx, y_bot - 1),
            (x0_bot + 1, y_bot - 1),
            (x_mid_left + 1, y_mid)
        ]
        draw.polygon(left_poly, fill=left_color)
        
        # Right facet
        right_poly = [
            (cx, y_top + 1),
            (x1_top - 1, y_top + 1),
            (x_mid_right - 1, y_mid),
            (x1_bot - 1, y_bot - 1),
            (cx, y_bot - 1)
        ]
        draw.polygon(right_poly, fill=right_color)
        
        # Inner vertical shine line
        if w > 5:
            # Subtle highlight on the center vertical edge
            draw.line([(cx, y_top + 1), (cx, y_bot - 1)], fill=shine_color, width=1)
            # Sparkle dot
            img.putpixel((cx + 1, y_top + 2), white)
            img.putpixel((cx + 1, y_top + 3), shine_color)
    else:
        # Edge-on: single vertical line
        draw.line([(cx, y_top + 1), (cx, y_bot - 1)], fill=left_color, width=1)
        draw.line([(cx + 1, y_top + 1), (cx + 1, y_bot - 1)], fill=right_color, width=1)
        
    return img

def main():
    os.makedirs("sprites", exist_ok=True)
    for i in range(4):
        img = create_rupee_frame(i)
        img.save(f"sprites/sprite_{i+1:04d}.png")
    print("✅ Successfully generated beautiful spinning Zelda Rupee sprite frames in sprites/")

if __name__ == "__main__":
    main()
