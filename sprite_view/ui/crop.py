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
        self.click_outside_crop = False
        
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
        drag_gesture.set_button(1)
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
        if hasattr(self.win, "get_view_transform"):
            transform = self.win.get_view_transform(widget_w, widget_h)
            if transform is not None:
                return transform

        win = self.win
        if not getattr(win, 'textures', None) or win.current_frame >= len(win.textures):
            return None

        if widget_w is None:
            widget_w = self.crop_overlay.get_width()
        if widget_h is None:
            widget_h = self.crop_overlay.get_height()

        pic_w = win.picture.get_width()
        pic_h = win.picture.get_height()
        if pic_w <= 0 or pic_h <= 0:
            return None

        canvas_w, canvas_h = getattr(win, 'canvas_size', (0, 0))
        if canvas_w <= 0 or canvas_h <= 0:
            return None

        if pic_w <= widget_w:
            pic_x = (widget_w - pic_w) / 2
        else:
            hadj = win.scroll_zoom.get_hadjustment()
            pic_x = -(hadj.get_value() if hadj else 0)
        if pic_h <= widget_h:
            pic_y = (widget_h - pic_h) / 2
        else:
            vadj = win.scroll_zoom.get_vadjustment()
            pic_y = -(vadj.get_value() if vadj else 0)

        if win._zoom == 0:
            tex = win.textures[win.current_frame]
            tex_w = tex.get_width()
            tex_h = tex.get_height()
            s = min(pic_w / tex_w, pic_h / tex_h) if pic_w > 0 else 1
            scale_src_to_view = s * win.scale_factor
            canvas_to_texture_scale = win.scale_factor
        else:
            scale_src_to_view = float(win._zoom)
            canvas_to_texture_scale = 1.0

        from sprite_view.utils import ViewTransform
        return ViewTransform(
            x_min=pic_x,
            y_min=pic_y,
            scale_src_to_view=scale_src_to_view,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            canvas_to_texture_scale=canvas_to_texture_scale,
        )

    def _get_crop_box_widget_coords(self, bounds):
        if not self.crop_box:
            return 0.0, 0.0, 0.0, 0.0

        if hasattr(bounds, 'source_box_to_view'):
            return bounds.source_box_to_view(self.crop_box)

        x1, y1, x2, y2 = self.crop_box
        canvas_scale = bounds.get('canvas_to_texture_scale', 1.0)
        scale_src_to_view = bounds.get('scale_src_to_view', bounds['scale'] * canvas_scale)

        cx1 = bounds['x_min'] + x1 * scale_src_to_view
        cy1 = bounds['y_min'] + y1 * scale_src_to_view
        cx2 = bounds['x_min'] + x2 * scale_src_to_view
        cy2 = bounds['y_min'] + y2 * scale_src_to_view

        return min(cx1, cx2), min(cy1, cy2), max(cx1, cx2), max(cy1, cy2)

    def _on_drag_begin(self, gesture, start_x, start_y) -> None:
        bounds = self._get_image_bounds()
        if not bounds:
            self.drag_in_progress = False
            return

        win = self.win
        self.drag_start_widget = (start_x, start_y)
        self.previous_crop_active = self.crop_active
        self.previous_crop_box = self.crop_box
        self.click_outside_crop = False

        if hasattr(bounds, 'contains_view_point'):
            if not bounds.contains_view_point(start_x, start_y):
                self.drag_in_progress = False
                return
        else:
            if start_x < bounds['x_min'] or start_x > bounds['x_max'] or start_y < bounds['y_min'] or start_y > bounds['y_max']:
                self.drag_in_progress = False
                return

        self.drag_in_progress = True

        if hasattr(bounds, 'view_to_source_pixel'):
            cx, cy = bounds.view_to_source_pixel(start_x, start_y, clamp=True)
        else:
            tx = (start_x - bounds['x_min']) / bounds['scale']
            ty = (start_y - bounds['y_min']) / bounds['scale']
            canvas_scale = bounds.get('canvas_to_texture_scale', 1.0)
            cx = int(round(tx / canvas_scale))
            cy = int(round(ty / canvas_scale))
            canvas_w, canvas_h = win.canvas_size
            cx = max(0, min(canvas_w, cx))
            cy = max(0, min(canvas_h, cy))

        if self.crop_active and self.crop_box:
            x1, y1, x2, y2 = self._get_crop_box_widget_coords(bounds)
            self.click_outside_crop = not (x1 <= start_x <= x2 and y1 <= start_y <= y2)

        self.drag_handle = None
        self.move_mode = False

        if self.crop_active and self.crop_box and not self.click_outside_crop:
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

            if min_dist <= 18.0:
                self.drag_handle = closest_handle
                self.initial_crop_box = self.crop_box

        if not self.drag_handle and not self.click_outside_crop and self.crop_active and self.crop_box:
            bx1, by1, bx2, by2 = self.crop_box
            if bx1 <= cx <= bx2 and by1 <= cy <= by2:
                self.move_mode = True
                self.initial_crop_box = (bx1, by1, bx2, by2)

        if not self.drag_handle and not self.move_mode:
            self.pending_new_crop = True
            self.crop_drag_start = (cx, cy)
        else:
            self.pending_new_crop = False

        self.crop_overlay.queue_draw()

    def _on_drag_update(self, gesture, offset_x, offset_y) -> None:
        if not hasattr(self, 'drag_in_progress') or not self.drag_in_progress:
            return

        bounds = self._get_image_bounds()
        if not bounds:
            return

        win = self.win
        if hasattr(bounds, 'view_delta_to_source'):
            delta_cx, delta_cy = bounds.view_delta_to_source(offset_x, offset_y)
        else:
            canvas_scale = bounds.get('canvas_to_texture_scale', 1.0)
            delta_cx = (offset_x / bounds['scale']) / canvas_scale
            delta_cy = (offset_y / bounds['scale']) / canvas_scale

        offset_cx = int(round(delta_cx))
        offset_cy = int(round(delta_cy))

        if getattr(self, 'pending_new_crop', False):
            if abs(offset_x) < 5.0 and abs(offset_y) < 5.0:
                return
            self.crop_active = True
            start_cx, start_cy = self.crop_drag_start
            self.crop_box = (start_cx, start_cy, start_cx, start_cy)
            self.pending_new_crop = False
            self._update_crop_button_visibility()

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

            new_x1 = bx1 + offset_cx
            new_y1 = by1 + offset_cy

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
            if hasattr(self, 'drag_start_widget'):
                start_x, start_y = self.drag_start_widget
                self.win._on_picture_clicked(gesture, 1, start_x, start_y)
            return
        self.drag_in_progress = False

        bounds = self._get_image_bounds()
        if not bounds:
            return

        is_click = abs(offset_x) < 5.0 and abs(offset_y) < 5.0
        self.pending_new_crop = False

        if is_click:
            if self.click_outside_crop:
                self.reset()
            else:
                self.crop_active = self.previous_crop_active
                self.crop_box = self.previous_crop_box
            start_x, start_y = self.drag_start_widget
            self.win._on_picture_clicked(gesture, 1, start_x, start_y)
        else:
            if not getattr(self, 'drag_handle', None) and not getattr(self, 'move_mode', False):
                if self.crop_box:
                    x1, y1, x2, y2 = self.crop_box
                    if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
                        self.reset()

        self.drag_handle = None
        self.move_mode = False
        self.click_outside_crop = False
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

        cx1, cy1, cx2, cy2 = self._get_crop_box_widget_coords(bounds)

        cx1 = max(x_min, min(x_max, cx1))
        cx2 = max(x_min, min(x_max, cx2))
        cy1 = max(y_min, min(y_max, cy1))
        cy2 = max(y_min, min(y_max, cy2))

        if cx1 == cx2 or cy1 == cy2:
            return

        cr.save()
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)

        if cy1 > y_min:
            cr.rectangle(x_min, y_min, img_w, cy1 - y_min)
            cr.fill()
        if y_max > cy2:
            cr.rectangle(x_min, cy2, img_w, y_max - cy2)
            cr.fill()
        if cx1 > x_min:
            cr.rectangle(x_min, cy1, cx1 - x_min, cy2 - cy1)
            cr.fill()
        if x_max > cx2:
            cr.rectangle(cx2, cy1, x_max - cx2, cy2 - cy1)
            cr.fill()

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        cr.set_line_width(2.0)
        cr.rectangle(cx1, cy1, cx2 - cx1, cy2 - cy1)
        cr.stroke()

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
        cr.set_line_width(1.0)
        cr.set_dash([4.0, 4.0], 0.0)
        cr.rectangle(cx1, cy1, cx2 - cx1, cy2 - cy1)
        cr.stroke()

        cr.set_dash([], 0.0)

        handle_size = 12.0
        handles = [
            (cx1, cy1), (cx2, cy1), (cx1, cy2), (cx2, cy2),
            ((cx1 + cx2)/2, cy1), ((cx1 + cx2)/2, cy2),
            (cx1, (cy1 + cy2)/2), (cx2, (cy1 + cy2)/2)
        ]
        cr.set_line_width(1.0)
        for hx, hy in handles:
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(hx - handle_size/2, hy - handle_size/2, handle_size, handle_size)
            cr.fill()
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.rectangle(hx - handle_size/2 + 1, hy - handle_size/2 + 1, handle_size - 2, handle_size - 2)
            cr.fill()

        bx1, by1, bx2, by2 = self.crop_box
        crop_w = int(round(abs(bx2 - bx1)))
        crop_h = int(round(abs(by2 - by1)))

        size_str = f"{crop_w} × {crop_h}"

        cr.select_font_face("Sans", 0, 1)
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
