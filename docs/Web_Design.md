<!-- SPDX-FileCopyrightText: 2026 Uwe Jugel -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Web Design Guidelines & Layout Lessons

This document records the evergreen styling patterns, CSS/HTML structural decisions, and layout learnings developed during the construction and debugging of the Nautilus SpriteView website.

---

## 1. Responsive Code Boxes & Terminal Mockups

### The Problem
When displaying terminal prompts or code blocks in a flex container (e.g., next to a "Copy" button), inline elements like `<span>` ignore horizontal width constraints (`flex: 1; min-width: 0;`). As a result:
* The code block does not shrink.
* It overflows the container.
* It pushes or gets hidden underneath the copy button.
* If horizontal scrolling (`overflow-x: auto;`) is placed directly on the inline span, the browser engine ignores it completely, rendering the code cut off and unscrollable.

### The Solution: Flexbox Block Wrapping
To make code snippets properly responsive:
1. **Force Block Display**: The scrollable container `<span>` must be set to `display: block;` (or `display: inline-block;`) to respect CSS width calculations and overflow properties.
2. **Apply Flex Constraints**: Configure both the code wrapper and the scrolling container to take up remaining space smoothly:
   ```css
   .terminal-code {
       display: block;
       flex: 1;
       min-width: 0;
   }
   ```

### Command Wrapping vs. Scrolling
For long, single-line commands (like script installation instructions) in terminal mockups:
* **The Pitfall**: Forcing the text to stay on one line (`white-space: nowrap;`) with a hidden scrollbar means the command is partially cut off on standard viewports, with no visual cues for scrolling.
* **The Remedy**: Remove terminal command prompts (like `user@resolute:~$ `) and use dynamic wrapping:
  ```css
  .terminal-command {
      display: block;
      white-space: pre-wrap;
      word-wrap: break-word;
      word-break: break-all;
      flex: 1;
      min-width: 0;
  }
  ```
  This wraps the command onto new lines automatically when it reaches the right boundary of the flex box, keeping the code fully readable on all devices without horizontal scrolling.

---

## 2. Icon-Only Buttons with Hover Tooltips

### The Problem
Including text (like the word `"Copy"`) inline inside a copy button increases the button's layout footprint. This reduces the horizontal space available for the neighboring terminal code container, exacerbating clipping issues on smaller screens.

### The Solution: Absolute Hover Tooltips
To keep copy buttons compact (e.g., `38px` square icons) while retaining the textual state cues:
1. **Remove Text from the Layout Flow**: Give the copy button a relative position and set the tooltip text to absolute alignment so it floats *above* the layout flow:
   ```css
   .copy-button {
       position: relative;
       width: 38px;
       height: 38px;
       display: flex;
       align-items: center;
       justify-content: center;
       flex-shrink: 0;
   }

   .tooltip-text {
       position: absolute;
       bottom: 125%;
       left: 50%;
       transform: translateX(-50%) translateY(4px);
       background-color: #1e293b;
       color: #f8fafc;
       padding: 0.4rem 0.6rem;
       border-radius: 6px;
       font-size: 0.75rem;
       white-space: nowrap;
       opacity: 0;
       visibility: hidden;
       transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
       pointer-events: none;
       z-index: 10;
   }
   ```
2. **Trigger Tooltip on Hover/Success**: Reveal the tooltip text box on button hover or when a `.copied` class is appended via JavaScript:
   ```css
   .copy-button:hover .tooltip-text,
   .copy-button.copied .tooltip-text {
       opacity: 1;
       visibility: visible;
       transform: translateX(-50%) translateY(0);
   }
   ```

---

## 3. Viewport Crop Management for Screenshots (`object-position`)

### The Problem
When using `object-fit: cover;` within cards with a fixed aspect ratio (e.g. `16:10`), the browser default centers (`50% 50%`) the screenshots. This results in critical screenshot elements getting cropped out:
* Selected folders or file list cursors near the top edge of a window are cut off.
* Right-click/context menus near the bottom edge of a window are cut off.

### The Solution: Contextual Focus Points
Override the default object positioning in HTML using inline styling to focus on the active visual element:
* **Context Menu Screenshots**: Focus on the bottom where context menus reside.
  ```html
  <img class="showcase-img" src="menu.png" style="object-position: bottom;">
  ```
* **Selection State Screenshots**: Focus on the top where Nautilus file columns are selected.
  ```html
  <img class="showcase-img" src="select.png" style="object-position: top;">
  ```

---

## 4. Sharp Scaling for Pixel Art Assets

### The Problem
Web browsers apply bilinear interpolation by default when scaling small images (like a `24x24px` pixel art logo). This results in a blurry, anti-aliased look that destroys the visual appeal of pixel art.

### The Solution: Nearest-Neighbor Interpolation
Add styling to the image element (or its class wrapper) to preserve crisp pixel boundaries:
```css
.logo-icon img {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
}
```
This forces the browser to upscale the asset using nearest-neighbor scaling, maintaining perfectly sharp edges.
