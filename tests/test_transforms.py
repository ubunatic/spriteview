# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch
from sprite_view.utils import ViewTransform
from sprite_view.ui.preview import ImagePreviewWindow
from sprite_view.ui.crop import CropManager


class TestViewTransformUnit(unittest.TestCase):
    def test_auto_zoom_transform(self):
        # 300x200 canvas on 800x600 viewport, pic_w=600, pic_h=400 (centered at 100, 100)
        transform = ViewTransform(
            x_min=100.0,
            y_min=100.0,
            scale_src_to_view=2.0,
            canvas_w=300,
            canvas_h=200,
            canvas_to_texture_scale=1.0,
        )

        self.assertEqual(transform.x_max, 700.0)
        self.assertEqual(transform.y_max, 500.0)
        self.assertEqual(transform.view_w, 600.0)
        self.assertEqual(transform.view_h, 400.0)

        # Forward mapping
        self.assertEqual(transform.source_to_view(0, 0), (100.0, 100.0))
        self.assertEqual(transform.source_to_view(150, 100), (400.0, 300.0))
        self.assertEqual(transform.source_box_to_view((10, 20, 50, 60)), (120.0, 140.0, 200.0, 220.0))

        # Inverse mapping
        self.assertEqual(transform.view_to_source(100.0, 100.0), (0.0, 0.0))
        self.assertEqual(transform.view_to_source(400.0, 300.0), (150.0, 100.0))
        self.assertEqual(transform.view_to_source_pixel(400.2, 300.4), (150, 100))

        # Delta mapping
        self.assertEqual(transform.view_delta_to_source(20.0, -10.0), (10.0, -5.0))

        # Contains point
        self.assertTrue(transform.contains_view_point(100.0, 100.0))
        self.assertTrue(transform.contains_view_point(400.0, 300.0))
        self.assertFalse(transform.contains_view_point(99.0, 300.0))
        self.assertFalse(transform.contains_view_point(701.0, 300.0))

    def test_fractional_manual_zoom_transform(self):
        # 32x32 canvas zoomed 2.5x on 200x200 viewport, pic_w=80, pic_h=80 (centered at 60, 60)
        transform = ViewTransform(
            x_min=60.0,
            y_min=60.0,
            scale_src_to_view=2.5,
            canvas_w=32,
            canvas_h=32,
            canvas_to_texture_scale=1.0,
        )

        self.assertEqual(transform.source_to_view(0, 0), (60.0, 60.0))
        self.assertEqual(transform.source_to_view(32, 32), (140.0, 140.0))
        self.assertEqual(transform.view_to_source(110.0, 110.0), (20.0, 20.0))
        self.assertEqual(transform.view_to_source_pixel(110.0, 110.0), (20, 20))
        self.assertEqual(transform.view_delta_to_source(25.0, 50.0), (10.0, 20.0))

    def test_panning_transform(self):
        # Scrolled offsets hadj=80, vadj=30 -> pic_x=-80, pic_y=-30, zoom=3.0
        transform = ViewTransform(
            x_min=-80.0,
            y_min=-30.0,
            scale_src_to_view=3.0,
            canvas_w=100,
            canvas_h=100,
            canvas_to_texture_scale=1.0,
        )

        self.assertEqual(transform.source_to_view(0, 0), (-80.0, -30.0))
        self.assertEqual(transform.source_to_view(10, 20), (-50.0, 30.0))
        self.assertEqual(transform.view_to_source(-50.0, 30.0), (10.0, 20.0))
        self.assertEqual(transform.view_to_source_pixel(-50.0, 30.0), (10, 20))

    def test_upscaled_texture_transform(self):
        # Small 16x16 canvas, scale_factor=4 (texture=64x64), fit to 256x256 view
        transform = ViewTransform(
            x_min=0.0,
            y_min=0.0,
            scale_src_to_view=16.0, # (256/64) * 4 = 16
            canvas_w=16,
            canvas_h=16,
            canvas_to_texture_scale=4.0,
        )

        self.assertEqual(transform.source_to_view(1, 1), (16.0, 16.0))
        self.assertEqual(transform.view_to_source(32.0, 32.0), (2.0, 2.0))
        self.assertEqual(transform.scale, 4.0)

    def test_dict_interface_compatibility(self):
        transform = ViewTransform(
            x_min=10.0,
            y_min=20.0,
            scale_src_to_view=2.0,
            canvas_w=100,
            canvas_h=50,
            canvas_to_texture_scale=1.0,
        )

        self.assertEqual(transform['x_min'], 10.0)
        self.assertEqual(transform['y_min'], 20.0)
        self.assertEqual(transform['w'], 200.0)
        self.assertEqual(transform['h'], 100.0)
        self.assertEqual(transform['scale'], 2.0)
        self.assertEqual(transform.get('x_min'), 10.0)
        self.assertEqual(transform.get('non_existent', 42), 42)


class TestPreviewWindowTransformIntegration(unittest.TestCase):
    def test_get_view_transform_auto_zoom(self):
        win = MagicMock()
        win.textures = [MagicMock()]
        win.current_frame = 0
        win.textures[0].get_width.return_value = 100
        win.textures[0].get_height.return_value = 100
        win.picture.get_width.return_value = 200
        win.picture.get_height.return_value = 200
        win.outer_overlay.get_width.return_value = 400
        win.outer_overlay.get_height.return_value = 400
        win.crop_manager.crop_overlay.get_width.return_value = 400
        win.crop_manager.crop_overlay.get_height.return_value = 400
        win.canvas_size = (100, 100)
        win._zoom = 0
        win.scale_factor = 1.0

        transform = ImagePreviewWindow.get_view_transform(win)

        self.assertIsNotNone(transform)
        self.assertEqual(transform.x_min, 100.0)
        self.assertEqual(transform.y_min, 100.0)
        self.assertEqual(transform.scale_src_to_view, 2.0)

    def test_get_view_transform_manual_zoom_scale_factor_greater_than_one(self):
        # Fixes issue 008: manual zoom with scale_factor > 1
        win = MagicMock()
        win.textures = [MagicMock()]
        win.current_frame = 0
        win.picture.get_width.return_value = 80
        win.picture.get_height.return_value = 80
        win.crop_manager.crop_overlay.get_width.return_value = 200
        win.crop_manager.crop_overlay.get_height.return_value = 200
        win.canvas_size = (32, 32)
        win._zoom = 2.5
        win.scale_factor = 4.0 # small image display texture upscaling

        transform = ImagePreviewWindow.get_view_transform(win)

        self.assertIsNotNone(transform)
        self.assertEqual(transform.x_min, 60.0) # (200 - 80) / 2
        self.assertEqual(transform.y_min, 60.0)
        # scale_src_to_view must be _zoom = 2.5 (NOT 2.5 * 4.0 = 10.0)
        self.assertEqual(transform.scale_src_to_view, 2.5)

        # Source box (10, 10, 20, 20) -> view box (60 + 25, 60 + 25, 60 + 50, 60 + 50)
        view_box = transform.source_box_to_view((10, 10, 20, 20))
        self.assertEqual(view_box, (85.0, 85.0, 110.0, 110.0))

    def test_crop_gesture_and_draw_with_scale_factor_gt_one(self):
        # End-to-end crop drag test with manual zoom and scale_factor = 4
        win = MagicMock()
        win.textures = [MagicMock()]
        win.current_frame = 0
        win.picture.get_width.return_value = 100
        win.picture.get_height.return_value = 100
        win.scroll_zoom.get_hadjustment.return_value.get_value.return_value = 0
        win.scroll_zoom.get_vadjustment.return_value.get_value.return_value = 0
        win.canvas_size = (40, 40)
        win._zoom = 2.5
        win.scale_factor = 4

        manager = CropManager(win)

        transform = ViewTransform(
            x_min=0.0,
            y_min=0.0,
            scale_src_to_view=2.5,
            canvas_w=40,
            canvas_h=40,
            canvas_to_texture_scale=4.0,
        )

        with patch.object(manager, "_get_image_bounds", return_value=transform):
            # Drag from view (25, 25) -> source (10, 10)
            manager._on_drag_begin(None, 25.0, 25.0)
            # Drag offset (50, 25) in view -> source offset (20, 10)
            manager._on_drag_update(None, 50.0, 25.0)

            # Crop box stored in source coordinates
            self.assertEqual(manager.crop_box, (10, 10, 30, 20))

            # Widget box rendered on screen
            widget_coords = manager._get_crop_box_widget_coords(transform)
            self.assertEqual(widget_coords, (25.0, 25.0, 75.0, 50.0))

    def test_zoom_change_retains_stored_crop_state(self):
        win = MagicMock()
        win.canvas_size = (100, 100)
        win.textures = [MagicMock()]
        win.current_frame = 0
        win.scale_factor = 1

        manager = CropManager(win)
        manager.crop_active = True
        manager.crop_box = (10, 15, 60, 80)

        # Before zoom change
        win._zoom = 1.0
        transform1 = ViewTransform(x_min=0, y_min=0, scale_src_to_view=1.0, canvas_w=100, canvas_h=100)
        vbox1 = manager._get_crop_box_widget_coords(transform1)
        self.assertEqual(vbox1, (10.0, 15.0, 60.0, 80.0))

        # After zoom change to 3.0x
        win._zoom = 3.0
        transform2 = ViewTransform(x_min=0, y_min=0, scale_src_to_view=3.0, canvas_w=100, canvas_h=100)
        vbox2 = manager._get_crop_box_widget_coords(transform2)

        # Source coordinates in manager.crop_box remain unchanged
        self.assertEqual(manager.crop_box, (10, 15, 60, 80))
        # View coordinates scale dynamically with view transform
        self.assertEqual(vbox2, (30.0, 45.0, 180.0, 240.0))


if __name__ == "__main__":
    unittest.main()
