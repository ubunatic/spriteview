# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from PIL import Image

class CropManager:
    def __init__(self, win) -> None:
        self.win = win
        self.crop_active = False
        self.drag_in_progress = False
        self.crop_box = None
        self.crop_drag_start = (0.0, 0.0)
        
        # Create Drawing Area
        self.crop_overlay = Gtk.DrawingArea()
        self.crop_overlay.set_vexpand(True)
        self.crop_overlay.set_hexpand(True)
        self.crop_overlay.set_halign(Gtk.Align.FILL)
        self.crop_overlay.set_valign(Gtk.Align.FILL)
        self.crop_overlay.set_draw_func(self._on_crop_overlay_draw)
        
        # Overlay Crop Button
        self.btn_overlay_crop = Gtk.Button(label="Crop")
        self.btn_overlay_crop.add_css_class("suggested-action")
        self.btn_overlay_crop.set_halign(Gtk.Align.END)
        self.btn_overlay_crop.set_valign(Gtk.Align.START)
        self.btn_overlay_crop.set_margin_top(12)
        self.btn_overlay_crop.set_margin_end(12)
        self.btn_overlay_crop.set_visible(False)
        self.btn_overlay_crop.connect("clicked", lambda b: self.crop_in_memory())
        
        # Gestures
        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.connect("drag-begin", self._on_drag_begin)
        drag_gesture.connect("drag-update", self._on_drag_update)
        drag_gesture.connect("drag-end", self._on_drag_end)
        self.crop_overlay.add_controller(drag_gesture)

    def reset(self) -> None:
        self.crop_active = False
        self.crop_box = None
        self.crop_overlay.queue_draw()
        self._update_crop_button_visibility()
        if hasattr(self, 'win') and hasattr(self.win, 'btn_crop') and self.win.btn_crop:
            if self.win.btn_crop.get_active():
                self.win.btn_crop.set_active(False)

    def _update_crop_button_visibility(self) -> None:
        if self.btn_overlay_crop:
            self.btn_overlay_crop.set_visible(self.crop_active)

    def _get_image_bounds(self, widget_w=None, widget_h=None):
        win = self.win
        if not win.textures or win.current_frame >= len(win.textures):
            return None
            
        tex = win.textures[win.current_frame]
        tex_w = tex.get_width()
        tex_h = tex.get_height()
        
        if widget_w is None:
            widget_w = self.crop_overlay.get_width()
        if widget_h is None:
            widget_h = self.crop_overlay.get_height()
            
        if widget_w <= 0 or widget_h <= 0:
            return None
            
        s = min(widget_w / tex_w, widget_h / tex_h)
        img_w = tex_w * s
        img_h = tex_h * s
        x_offset = (widget_w - img_w) / 2
        y_offset = (widget_h - img_h) / 2
        
        return {
            'x_min': x_offset,
            'x_max': x_offset + img_w,
            'y_min': y_offset,
            'y_max': y_offset + img_h,
            'w': img_w,
            'h': img_h,
            'scale': s
        }

    def _get_crop_box_widget_coords(self, bounds):
        if not self.crop_box:
            return 0.0, 0.0, 0.0, 0.0
            
        x1, y1, x2, y2 = self.crop_box
        win = self.win
        
        # Map canvas -> texture
        tx1 = x1 * win.scale_factor
        ty1 = y1 * win.scale_factor
        tx2 = x2 * win.scale_factor
        ty2 = y2 * win.scale_factor
        
        # Map texture -> widget
        cx1 = bounds['x_min'] + tx1 * bounds['scale']
        cy1 = bounds['y_min'] + ty1 * bounds['scale']
        cx2 = bounds['x_min'] + tx2 * bounds['scale']
        cy2 = bounds['y_min'] + ty2 * bounds['scale']
        
        cx_min = min(cx1, cx2)
        cx_max = max(cx1, cx2)
        cy_min = min(cy1, cy2)
        cy_max = max(cy1, cy2)
        
        return cx_min, cy_min, cx_max, cy_max

    def _on_drag_begin(self, gesture, start_x, start_y) -> None:
        if not self.crop_active:
            self.drag_in_progress = False
            return
            
        bounds = self._get_image_bounds()
        if not bounds:
            self.drag_in_progress = False
            return
            
        win = self.win
        
        # Click outside the image bounds resets/hides crop helper
        if start_x < bounds['x_min'] or start_x > bounds['x_max'] or start_y < bounds['y_min'] or start_y > bounds['y_max']:
            self.drag_in_progress = False
            self.reset()
            return
            
        self.drag_in_progress = True
        
        # Convert start coordinates to canvas space and snap to source pixels
        tx = (start_x - bounds['x_min']) / bounds['scale']
        ty = (start_y - bounds['y_min']) / bounds['scale']
        cx = int(round(tx / win.scale_factor))
        cy = int(round(ty / win.scale_factor))
        
        canvas_w, canvas_h = win.canvas_size
        cx = max(0, min(canvas_w, cx))
        cy = max(0, min(canvas_h, cy))
        
        self.drag_handle = None
        self.move_mode = False
        
        # Check if clicking on/near a handle first
        if self.crop_active and self.crop_box:
            cx1, cy1, cx2, cy2 = self._get_crop_box_widget_coords(bounds)
            handles = {
                'TL': (cx1, cy1),
                'TR': (cx2, cy1),
                'BL': (cx1, cy2),
                'BR': (cx2, cy2),
                'TC': ((cx1 + cx2)/2, cy1),
                'BC': ((cx1 + cx2)/2, cy2),
                'LC': (cx1, (cy1 + cy2)/2),
                'RC': (cx2, (cy1 + cy2)/2)
            }
            
            closest_handle = None
            min_dist = float('inf')
            for name, (hx, hy) in handles.items():
                dist = ((start_x - hx)**2 + (start_y - hy)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_handle = name
                    
            if min_dist <= 18.0:  # 18 pixels hit target
                self.drag_handle = closest_handle
                self.initial_crop_box = self.crop_box
                
        # If not clicking a handle, check if clicking inside the box
        if not self.drag_handle and self.crop_active and self.crop_box:
            bx1, by1, bx2, by2 = self.crop_box
            if bx1 <= cx <= bx2 and by1 <= cy <= by2:
                self.move_mode = True
                self.initial_crop_box = (bx1, by1, bx2, by2)
                
        # If neither, start drawing a new crop box
        if not self.drag_handle and not self.move_mode:
            self.crop_active = True
            self.crop_drag_start = (cx, cy)
            self.crop_box = (cx, cy, cx, cy)
            
        self.crop_overlay.queue_draw()
        self._update_crop_button_visibility()

    def _on_drag_update(self, gesture, offset_x, offset_y) -> None:
        if not hasattr(self, 'drag_in_progress') or not self.drag_in_progress:
            return
            
        bounds = self._get_image_bounds()
        if not bounds:
            return
            
        win = self.win
        # Map offset to canvas space and snap to source pixels
        offset_cx = int(round((offset_x / bounds['scale']) / win.scale_factor))
        offset_cy = int(round((offset_y / bounds['scale']) / win.scale_factor))
        
        canvas_w, canvas_h = win.canvas_size
        
        if getattr(self, 'drag_handle', None):
            bx1, by1, bx2, by2 = self.initial_crop_box
            x1, y1, x2, y2 = bx1, by1, bx2, by2
            h = self.drag_handle
            
            if h in ('TL', 'BL', 'LC'):
                x1 = max(0, min(x2 - 1, bx1 + offset_cx))
            if h in ('TR', 'BR', 'RC'):
                x2 = max(x1 + 1, min(canvas_w, bx2 + offset_cx))
            if h in ('TL', 'TR', 'TC'):
                y1 = max(0, min(y2 - 1, by1 + offset_cy))
            if h in ('BL', 'BR', 'BC'):
                y2 = max(y1 + 1, min(canvas_h, by2 + offset_cy))
                
            self.crop_box = (x1, y1, x2, y2)
        elif getattr(self, 'move_mode', False):
            bx1, by1, bx2, by2 = self.initial_crop_box
            box_w = bx2 - bx1
            box_h = by2 - by1
            
            # Shift the box
            new_x1 = bx1 + offset_cx
            new_y1 = by1 + offset_cy
            
            # Clamp box to canvas boundaries
            new_x1 = max(0, min(canvas_w - box_w, new_x1))
            new_y1 = max(0, min(canvas_h - box_h, new_y1))
            
            self.crop_box = (new_x1, new_y1, new_x1 + box_w, new_y1 + box_h)
        else:
            start_cx, start_cy = self.crop_drag_start
            curr_cx = max(0, min(canvas_w, start_cx + offset_cx))
            curr_cy = max(0, min(canvas_h, start_cy + offset_cy))
            
            self.crop_box = (
                min(start_cx, curr_cx),
                min(start_cy, curr_cy),
                max(start_cx, curr_cx),
                max(start_cy, curr_cy)
            )
            
        self.crop_overlay.queue_draw()

    def _on_drag_end(self, gesture, offset_x, offset_y) -> None:
        if not hasattr(self, 'drag_in_progress') or not self.drag_in_progress:
            return
        self.drag_in_progress = False
        
        bounds = self._get_image_bounds()
        if not bounds:
            return
            
        # Check if the drag offset is small (indicating a simple click)
        is_click = abs(offset_x) < 5.0 and abs(offset_y) < 5.0
        
        if is_click:
            # If they clicked/interacted with a handle or moved box, keep as is
            if getattr(self, 'drag_handle', None):
                self.crop_box = self.initial_crop_box
            elif getattr(self, 'move_mode', False):
                self.crop_box = self.initial_crop_box
            else:
                self.reset()
        else:
            # If in draw mode (not drag_handle and not move_mode), check if too small
            if not getattr(self, 'drag_handle', None) and not getattr(self, 'move_mode', False):
                if self.crop_box:
                    x1, y1, x2, y2 = self.crop_box
                    if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
                        self.reset()
                        
        self.drag_handle = None
        self.move_mode = False
        self.crop_overlay.queue_draw()
        self._update_crop_button_visibility()

    def _on_crop_overlay_draw(self, area, cr, w, h) -> None:
        if not self.crop_active or not self.crop_box:
            return
            
        bounds = self._get_image_bounds(w, h)
        if not bounds:
            return
            
        x_min = bounds['x_min']
        x_max = bounds['x_max']
        y_min = bounds['y_min']
        y_max = bounds['y_max']
        img_w = bounds['w']
        img_h = bounds['h']
        
        # Get crop box widget coordinates
        cx1, cy1, cx2, cy2 = self._get_crop_box_widget_coords(bounds)
        
        # Ensure we only draw within the actual image bounds
        cx1 = max(x_min, min(x_max, cx1))
        cx2 = max(x_min, min(x_max, cx2))
        cy1 = max(y_min, min(y_max, cy1))
        cy2 = max(y_min, min(y_max, cy2))
        
        if cx1 == cx2 or cy1 == cy2:
            return
            
        # Draw the dimmed background outside the crop box (clamped to image bounds)
        cr.save()
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5) # 50% opacity black
        
        # Top
        if cy1 > y_min:
            cr.rectangle(x_min, y_min, img_w, cy1 - y_min)
            cr.fill()
        # Bottom
        if y_max > cy2:
            cr.rectangle(x_min, cy2, img_w, y_max - cy2)
            cr.fill()
        # Left
        if cx1 > x_min:
            cr.rectangle(x_min, cy1, cx1 - x_min, cy2 - cy1)
            cr.fill()
        # Right
        if x_max > cx2:
            cr.rectangle(cx2, cy1, x_max - cx2, cy2 - cy1)
            cr.fill()
            
        # Draw outer black border for contrast
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        cr.set_line_width(2.0)
        cr.rectangle(cx1, cy1, cx2 - cx1, cy2 - cy1)
        cr.stroke()
        
        # Draw inner white dashed border
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
        cr.set_line_width(1.0)
        cr.set_dash([4.0, 4.0], 0.0)
        cr.rectangle(cx1, cy1, cx2 - cx1, cy2 - cy1)
        cr.stroke()
        
        cr.set_dash([], 0.0)
        
        # Draw handles at corners and edges
        handle_size = 12.0
        handles = [
            (cx1, cy1), (cx2, cy1), (cx1, cy2), (cx2, cy2),
            ((cx1 + cx2)/2, cy1), ((cx1 + cx2)/2, cy2),
            (cx1, (cy1 + cy2)/2), (cx2, (cy1 + cy2)/2)
        ]
        cr.set_line_width(1.0)
        for hx, hy in handles:
            # Black border
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(hx - handle_size/2, hy - handle_size/2, handle_size, handle_size)
            cr.fill()
            # White inner
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.rectangle(hx - handle_size/2 + 1, hy - handle_size/2 + 1, handle_size - 2, handle_size - 2)
            cr.fill()
            
        # Show size text centered on top/inside the crop box
        win = self.win
        tx1 = (cx1 - bounds['x_min']) / bounds['scale']
        ty1 = (cy1 - bounds['y_min']) / bounds['scale']
        tx2 = (cx2 - bounds['x_min']) / bounds['scale']
        ty2 = (cy2 - bounds['y_min']) / bounds['scale']
        
        ox1 = tx1 / win.scale_factor
        oy1 = ty1 / win.scale_factor
        ox2 = tx2 / win.scale_factor
        oy2 = ty2 / win.scale_factor
        
        crop_w = int(round(abs(ox2 - ox1)))
        crop_h = int(round(abs(oy2 - oy1)))
        
        size_str = f"{crop_w} × {crop_h}"
        
        cr.select_font_face("Sans", 0, 1) # font face, slant, weight (1 = Bold)
        cr.set_font_size(12.0)
        
        _, _, text_w, text_h, _, _ = cr.text_extents(size_str)
        
        pill_w = text_w + 12.0
        pill_h = text_h + 8.0
        
        px = (cx1 + cx2)/2 - pill_w/2
        py = cy1 - pill_h - 6.0
        if py < bounds['y_min']:
            py = cy1 + 6.0
            
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.rectangle(px, py, pill_w, pill_h)
        cr.fill()
        
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.move_to(px + 6.0, py + pill_h - 5.0)
        cr.show_text(size_str)
        
        cr.restore()

    def crop_in_memory(self) -> None:
        if not self.crop_active or not self.crop_box:
            return
            
        x1, y1, x2, y2 = self.crop_box
        win = self.win
        
        # Ensure proper order and convert to integers
        cx1 = int(round(min(x1, x2)))
        cy1 = int(round(min(y1, y2)))
        cx2 = int(round(max(x1, x2)))
        cy2 = int(round(max(y1, y2)))
        
        crop_w = cx2 - cx1
        crop_h = cy2 - cy1
        
        if crop_w <= 0 or crop_h <= 0:
            return
            
        canvas_w, canvas_h = win.canvas_size
        
        # Clamp crop box to canvas bounds to avoid any out-of-bounds error
        cx1 = max(0, min(canvas_w - 1, cx1))
        cy1 = max(0, min(canvas_h - 1, cy1))
        crop_w = max(1, min(canvas_w - cx1, crop_w))
        crop_h = max(1, min(canvas_h - cy1, crop_h))
        
        new_pixbufs = []
        new_pil_images = []
        
        for i in range(len(win.original_pixbufs)):
            # 1. GdkPixbuf cropping
            pb = win.original_pixbufs[i]
            if win.has_mixed_sizes:
                pb = win._pad_pixbuf(pb, canvas_w, canvas_h, win.current_align)
            cropped_pb = pb.new_subpixbuf(cx1, cy1, crop_w, crop_h).copy()
            new_pixbufs.append(cropped_pb)
            
            # 2. PIL Image cropping
            img = win.original_pil_images[i]
            if win.has_mixed_sizes:
                img = win._pad_pil_image(img, canvas_w, canvas_h, win.current_align)
            cropped_img = img.crop((cx1, cy1, cx1 + crop_w, cy1 + crop_h))
            cropped_img.format = img.format
            cropped_img.info = img.info.copy()
            new_pil_images.append(cropped_img)
            
        win.original_pixbufs = new_pixbufs
        win.original_pil_images = new_pil_images
        
        # Update canvas size and flag
        win.canvas_size = (crop_w, crop_h)
        win.original_dimensions = [(pb.get_width(), pb.get_height()) for pb in win.original_pixbufs]
        win.frame_palettes = [win._extract_palette_from_pixbuf(pb, 16) for pb in win.original_pixbufs]
        win.has_mixed_sizes = False
        
        # Re-build textures with new crop
        win._build_textures(win.current_align)
        
        # Update main picture and thumbnail pictures
        win.picture.set_paintable(win.textures[win.current_frame])
        for idx, texture in enumerate(win.textures):
            if idx < len(win.thumb_pics):
                win.thumb_pics[idx].set_paintable(texture)
                
        # Hide alignment controls if no longer mixed sizes
        if hasattr(win, 'align_box'):
            win.align_box.set_visible(False)
            
        # Clear crop helper overlay state
        self.reset()
        
        # Unsaved changes track
        win.has_unsaved_changes = True
        win._update_save_button()
        
        # Refresh current frame info/labels
        win._update_frame()
