# Issue: Support Advanced Export Options

## Overview
Enhance the Sprite View export functionality by introducing an **Advanced Export Options** dialog/panel. This will allow developers and artists to scale exports, optimize color palettes, and map colors to target retro/terminal standards.

---

## Detailed Requirements

### 1. Scaling Options
* **Goal**: Allow users to export images or animations scaled up or down using configurable scaling factors.
* **Options**:
  * Scaling factors: `Orig (1x)`, `2x`, `4x`, `8x`, and a custom numeric scale field.
  * Resampling filters:
    * `Nearest Neighbor` (default, critical for crisp pixel-art sprites).
    * `Linear/Bilinear` (for smooth scaling).

### 2. Palette Reduction (Per-Frame)
* **Goal**: Optimize images by quantizing colors to a reduced palette size.
* **Options**:
  * Max colors: `2`, `4`, `8`, `16`, `32`, `64`, `128`, `256`.
  * Quantization method: Adaptive palette generation (e.g., Median Cut, Octree quantization using Pillow).

### 3. Shared Palette Reduction (Across Animation Frames)
* **Goal**: Ensure that all individual frames exported from a sequence share the exact same palette mapping. This is critical for retro consoles (like NES/Sega) or game engines that expect a unified color index across all animation states.
* **Implementation Plan**:
  1. Stitch or compile pixels from all animation frames into a single temporary virtual image.
  2. Compute an optimized master palette (e.g., 16 or 256 colors) from this virtual image.
  3. Quantize each frame against this master palette.

### 4. ANSI 256 Color Mapping
* **Goal**: Map the colors in the export to the closest matching colors in the standard 8-bit ANSI 256 terminal color palette.
* **Options**:
  * Map each frame independently.
  * Map all frames to a shared subset of the ANSI 256 palette.

---

## Proposed UI Design

Add an **Advanced Export Options...** button to the hamburger menu. Clicking this button opens a dialog containing:

```
┌──────────────────────────────────────────────────────────┐
│                 Advanced Export Options                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Scale: [ 1x (Original) │ 2x │ 4x │ 8x │ Custom... ]      │
│  Filter: (•) Nearest Neighbor   ( ) Linear (Bilinear)    │
│                                                          │
│  [x] Reduce Palette                                      │
│      Max Colors: [ 16  v]                                │
│      [x] Shared Palette (Unified color map across frames)│
│                                                          │
│  [ ] Map to ANSI 256 colors                              │
│                                                          │
│                                      [ Cancel ] [ Export ]│
└──────────────────────────────────────────────────────────┘
```

---

## Technical Considerations
* **Pillow Quantization**: Use `PIL.Image.quantize()` for color reduction.
* **Shared Palette Calculation**:
  ```python
  from PIL import Image
  
  def generate_shared_palette(images: list, max_colors: int):
      # Combine images vertically/horizontally
      widths, heights = zip(*(i.size for i in images))
      total_width = max(widths)
      total_height = sum(heights)
      
      combined = Image.new("RGBA", (total_width, total_height))
      y_offset = 0
      for img in images:
          combined.paste(img, (0, y_offset))
          y_offset += img.height
          
      # Get the master palette image
      master_p = combined.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)
      return master_p
  ```
* **ANSI 256 Matching**: Use the existing mapping logic in `sprite_view/utils.py` (`rgb_to_ansi`).
