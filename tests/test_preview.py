# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch, MagicMock, call
import os
from gi.repository import Gdk, Gtk, Gio, GdkPixbuf, GLib
from sprite_view.ui.preview import ImagePreviewWindow

class TestImagePreviewWindow(unittest.TestCase):
    def test_standalone_png_hides_sidebar_by_default(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.btn_sidebar = MagicMock()
        win.file_paths = ["/images/icon.png"]

        ImagePreviewWindow._update_sidebar_visibility(win)

        win.btn_sidebar.set_active.assert_called_once_with(False)

    def test_detected_sequence_shows_sidebar(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.btn_sidebar = MagicMock()
        win.file_paths = ["/images/walk_01.png", "/images/walk_02.png"]

        ImagePreviewWindow._update_sidebar_visibility(win)

        win.btn_sidebar.set_active.assert_called_once_with(True)

    def test_other_standalone_image_keeps_sidebar_choice(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.btn_sidebar = MagicMock()
        win.file_paths = ["/images/photo.jpg"]

        ImagePreviewWindow._update_sidebar_visibility(win)

        win.btn_sidebar.set_active.assert_not_called()

    def test_sidebar_toggle_collapses_and_reopens_panel(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.sidebar_box = MagicMock()
        button = MagicMock()
        button.get_active.side_effect = [False, True]

        ImagePreviewWindow._on_sidebar_toggled(win, button)
        ImagePreviewWindow._on_sidebar_toggled(win, button)

        win.sidebar_box.set_visible.assert_has_calls([call(False), call(True)])

    def test_on_key_pressed_navigation(self):
        # Create a mock window instance
        win = MagicMock(spec=ImagePreviewWindow)
        win.btn_folder_prev = MagicMock()
        win.btn_folder_prev.get_sensitive.return_value = True
        win.btn_folder_next = MagicMock()
        win.btn_folder_next.get_sensitive.return_value = True
        
        # Test ESC closes the window
        win.close = MagicMock()
        handled = ImagePreviewWindow._on_key_pressed(win, None, Gdk.KEY_Escape, None, 0)
        self.assertTrue(handled)
        win.close.assert_called_once()
        
        # Test Page Up calls _load_sibling_image(-1)
        win._load_sibling_image = MagicMock()
        handled = ImagePreviewWindow._on_key_pressed(win, None, Gdk.KEY_Page_Up, None, 0)
        self.assertTrue(handled)
        win._load_sibling_image.assert_called_once_with(-1)
        
        # Test Page Down calls _load_sibling_image(1)
        win._load_sibling_image.reset_mock()
        handled = ImagePreviewWindow._on_key_pressed(win, None, Gdk.KEY_Page_Down, None, 0)
        self.assertTrue(handled)
        win._load_sibling_image.assert_called_once_with(1)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_update_folder_navigation_sensitivity(self, mock_listdir, mock_exists):
        win = MagicMock(spec=ImagePreviewWindow)
        win.btn_folder_prev = MagicMock()
        win.btn_folder_next = MagicMock()
        
        # Case 1: no dir path
        win.dir_path = ""
        ImagePreviewWindow._update_folder_navigation_sensitivity(win)
        win.btn_folder_prev.set_sensitive.assert_called_with(False)
        win.btn_folder_next.set_sensitive.assert_called_with(False)
        
        # Case 2: dir path doesn't exist
        win.dir_path = "/mock/dir"
        mock_exists.return_value = False
        ImagePreviewWindow._update_folder_navigation_sensitivity(win)
        win.btn_folder_prev.set_sensitive.assert_called_with(False)
        win.btn_folder_next.set_sensitive.assert_called_with(False)
        
        # Case 3: directory exists but has no other images
        mock_exists.return_value = True
        mock_listdir.return_value = ["frame_01.png"]
        win.file_paths = ["/mock/dir/frame_01.png"]
        
        # We need os.path.isfile mock
        with patch("os.path.isfile", return_value=True):
            ImagePreviewWindow._update_folder_navigation_sensitivity(win)
            
        win.btn_folder_prev.set_sensitive.assert_called_with(False)
        win.btn_folder_next.set_sensitive.assert_called_with(False)
        
        # Case 4: directory exists and has other images
        mock_exists.return_value = True
        mock_listdir.return_value = ["frame_01.png", "other_image.png"]
        win.file_paths = ["/mock/dir/frame_01.png"]
        
        win.btn_folder_prev.reset_mock()
        win.btn_folder_next.reset_mock()
        with patch("os.path.isfile", return_value=True):
            ImagePreviewWindow._update_folder_navigation_sensitivity(win)
            
        win.btn_folder_prev.set_sensitive.assert_called_with(True)
        win.btn_folder_next.set_sensitive.assert_called_with(True)

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("sprite_view.utils.find_sprite_frames")
    def test_load_sibling_image(self, mock_find, mock_listdir, mock_exists):
        win = MagicMock(spec=ImagePreviewWindow)
        win.dir_path = "/mock/dir"
        win.first_frame_path = "/mock/dir/frame_01.png"
        win.file_paths = ["/mock/dir/frame_01.png"]
        win.settings = {}
        
        mock_exists.return_value = True
        mock_listdir.return_value = ["frame_01.png", "sibling.png"]
        mock_find.return_value = ["/mock/dir/sibling.png"]
        
        win._load_sequence = MagicMock()
        
        with patch("os.path.isfile", return_value=True):
            ImagePreviewWindow._load_sibling_image(win, 1)
            
        win._load_sequence.assert_called_once_with(["/mock/dir/sibling.png"], "/mock/dir/sibling.png")

    @patch("gi.repository.GdkPixbuf.Pixbuf.new_from_file")
    @patch("gi.repository.GLib.timeout_add")
    @patch("gi.repository.GLib.source_remove")
    @patch("PIL.Image.open")
    def test_load_sequence(self, mock_image_open, mock_source_remove, mock_timeout_add, mock_new_from_file):
        win = MagicMock(spec=ImagePreviewWindow)
        win.timer_id = 123
        win.settings = {}
        win.current_align = 4
        win.original_dimensions = []
        win.original_pixbufs = []
        win.frame_palettes = []
        win.textures = []
        win.thumb_buttons = []
        win.thumb_pics = []
        
        # Mock widgets to avoid NoneType attribute errors
        win.thumbs_box = MagicMock()
        win.thumbs_box.get_first_child.return_value = None
        win.picture = MagicMock()
        win.lbl_indicator = MagicMock()
        win.control_box = MagicMock()
        win.settings_box = MagicMock()
        win.scroll_win = MagicMock()
        win.align_box = MagicMock()
        win.fps_spin = MagicMock()
        win.mode_dropdown = MagicMock()
        win.align_btns = [MagicMock() for _ in range(9)]
        
        # Mock class methods
        win._extract_palette_from_pixbuf.return_value = []
        win._build_textures = MagicMock()
        win._update_menu_model = MagicMock()
        win._update_frame = MagicMock()
        win._update_play_pause_button = MagicMock()
        win._update_folder_navigation_sensitivity = MagicMock()
        
        # Mock GdkPixbuf loading
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.return_value = 100
        mock_pixbuf.get_height.return_value = 100
        mock_new_from_file.return_value = mock_pixbuf
        
        ImagePreviewWindow._load_sequence(win, ["/mock/dir/frame_01.png", "/mock/dir/frame_02.png"], "/mock/dir/frame_01.png")
        
        # Verify it removed the old timer
        mock_source_remove.assert_called_once_with(123)
        # Verify it loaded the new files
        self.assertEqual(win.file_paths, ["/mock/dir/frame_01.png", "/mock/dir/frame_02.png"])
        # Verify it build textures, updated frame and navigation sensitivity
        win._build_textures.assert_called_once()
        win._update_frame.assert_called_once()
        win._update_folder_navigation_sensitivity.assert_called_once()
        # Verify play/pause status and UI changes are called
        win._update_play_pause_button.assert_called_once()

    def test_get_crop_box_widget_coords(self):
        from sprite_view.ui.crop import CropManager
        win = MagicMock(spec=ImagePreviewWindow)
        win.scale_factor = 2
        
        manager = CropManager(win)
        manager.crop_box = (10, 20, 50, 60)
        
        bounds = {
            'x_min': 100,
            'y_min': 150,
            'scale': 1.5
        }
        cx1, cy1, cx2, cy2 = manager._get_crop_box_widget_coords(bounds)
        self.assertEqual((cx1, cy1, cx2, cy2), (130, 210, 250, 330))

    def test_crop_in_memory(self):
        from sprite_view.ui.crop import CropManager
        win = MagicMock(spec=ImagePreviewWindow)
        win.canvas_size = (100, 100)
        win.has_mixed_sizes = False
        win.current_align = 4
        win.current_frame = 0
        
        win.picture = MagicMock()
        win.textures = [MagicMock()]
        
        mock_pixbuf = MagicMock()
        mock_subpixbuf = MagicMock()
        mock_pixbuf.new_subpixbuf.return_value = mock_subpixbuf
        win.original_pixbufs = [mock_pixbuf]
        
        mock_pil_img = MagicMock()
        mock_cropped_pil = MagicMock()
        mock_pil_img.crop.return_value = mock_cropped_pil
        mock_pil_img.format = "PNG"
        mock_pil_img.info = {"dpi": (72, 72)}
        win.original_pil_images = [mock_pil_img]
        
        win.thumb_pics = []
        
        # Mock methods that are called inside crop_in_memory
        win._extract_palette_from_pixbuf.return_value = []
        win._build_textures = MagicMock()
        win._update_save_button = MagicMock()
        win._update_frame = MagicMock()
        
        manager = CropManager(win)
        manager.crop_active = True
        manager.crop_box = (10.1, 20.2, 50.3, 60.4)
        
        manager.crop_in_memory()
        
        mock_pixbuf.new_subpixbuf.assert_called_once_with(10, 20, 40, 40)
        mock_pil_img.crop.assert_called_once_with((10, 20, 50, 60))
        
        self.assertEqual(win.canvas_size, (40, 40))
        self.assertEqual(win.has_unsaved_changes, True)

    def test_reset_current_view_restores_baseline(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.file_paths = ["/mock/dir/frame_01.png"]
        win.current_frame = 0
        win.current_align = 4

        source_pixbuf = MagicMock()
        source_pixbuf.copy.return_value = "restored-pixbuf"
        source_img = MagicMock()
        source_img.copy.return_value = "restored-image"

        win._source_pixbufs = [source_pixbuf]
        win._source_pil_images = [source_img]
        win._source_dimensions = [(100, 120)]
        win._source_frame_palettes = [[(1, 2, 3, 4)]]
        win._source_canvas_size = (100, 120)
        win._source_has_mixed_sizes = True

        win.original_pixbufs = [MagicMock()]
        win.original_pil_images = [MagicMock()]
        win.original_dimensions = [(40, 50)]
        win.frame_palettes = [[(9, 9, 9, 9)]]
        win.canvas_size = (40, 50)
        win.has_mixed_sizes = False
        win.textures = ["texture"]
        win.thumb_pics = [MagicMock()]
        win.picture = MagicMock()
        win.align_box = MagicMock()
        win.crop_manager = MagicMock()
        win.has_unsaved_changes = True
        win._build_textures = MagicMock()
        win._update_save_button = MagicMock()
        win._update_reset_button = MagicMock()
        win._update_frame = MagicMock()

        ImagePreviewWindow._reset_current_view(win)

        win.crop_manager.reset.assert_called_once()
        self.assertEqual(win.original_pixbufs, ["restored-pixbuf"])
        self.assertEqual(win.original_pil_images, ["restored-image"])
        self.assertEqual(win.original_dimensions, [(100, 120)])
        self.assertEqual(win.frame_palettes, [[(1, 2, 3, 4)]])
        self.assertEqual(win.canvas_size, (100, 120))
        self.assertTrue(win.has_mixed_sizes)
        self.assertFalse(win.has_unsaved_changes)
        win._build_textures.assert_called_once_with(4)
        win.picture.set_paintable.assert_called_once_with("texture")
        win.thumb_pics[0].set_paintable.assert_called_once_with("texture")
        win.align_box.set_visible.assert_called_once_with(False)
        win._update_save_button.assert_called_once()
        win._update_reset_button.assert_called_once()
        win._update_frame.assert_called_once()

    def test_reload_current_files_uses_current_selection(self):
        win = MagicMock(spec=ImagePreviewWindow)
        win.file_paths = ["/mock/dir/frame_01.png", "/mock/dir/frame_02.png"]
        win.current_frame = 1
        win._load_sequence = MagicMock()

        ImagePreviewWindow._reload_current_files(win)

        win._load_sequence.assert_called_once_with(
            ["/mock/dir/frame_01.png", "/mock/dir/frame_02.png"],
            "/mock/dir/frame_02.png"
        )

if __name__ == "__main__":
    unittest.main()
