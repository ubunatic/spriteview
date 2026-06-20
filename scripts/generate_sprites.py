#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw

def create_coin_frame(frame_index: int) -> Image.Image:
    # 16x16 RGBA image with transparent background
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define coin widths for 4 frames of rotation (spinning horizontally)
    # Frame 0: width 12 (full circle-ish)
    # Frame 1: width 8 (diagonal-ish)
    # Frame 2: width 3 (side-on-ish)
    # Frame 3: width 8 (diagonal-ish)
    widths = [12, 8, 3, 8]
    w = widths[frame_index]
    h = 12  # constant height of 12
    
    # Calculate bounding box to center the ellipse
    x0 = (16 - w) // 2
    y0 = (16 - h) // 2
    x1 = x0 + w - 1
    y1 = y0 + h - 1
    
    # Colors:
    gold_border = (138, 90, 0, 255)       # #8a5a00
    gold_base = (255, 179, 0, 255)        # #ffb300
    gold_light = (254, 193, 7, 255)       # #fec107
    gold_highlight = (255, 243, 205, 255)  # #fff3cd
    white = (255, 255, 255, 255)
    
    # Draw border/shadow
    draw.ellipse([x0, y0, x1, y1], fill=gold_border)
    
    # Draw inner face
    if w > 3:
        draw.ellipse([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=gold_base)
        # Draw light shine
        draw.ellipse([x0 + 1, y0 + 1, x0 + w//2, y0 + h//2], fill=gold_light)
    else:
        # Edge-on: simple vertical golden bar
        draw.line([8, y0 + 1, 8, y1 - 1], fill=gold_light, width=1)
        
    # Draw sparkling reflection/details depending on frame
    if frame_index == 0:
        # Star gleam at top-left
        img.putpixel((6, 5), white)
        img.putpixel((5, 5), gold_highlight)
        img.putpixel((6, 4), gold_highlight)
    elif frame_index == 1:
        # Sparkle moving
        img.putpixel((6, 5), white)
    elif frame_index == 3:
        # Sparkle moving
        img.putpixel((9, 6), white)
        
    return img

def main():
    os.makedirs("sprites", exist_ok=True)
    for i in range(4):
        img = create_coin_frame(i)
        img.save(f"sprites/sprite_{i+1:04d}.png")
    print("✅ Successfully generated beautiful spinning coin sprite frames in sprites/")

if __name__ == "__main__":
    main()
