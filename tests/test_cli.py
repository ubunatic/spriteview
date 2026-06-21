# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import importlib.util

# Path to sprite_view.py at root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sprite_view_path = os.path.join(root_dir, "sprite_view.py")

spec = importlib.util.spec_from_file_location("sprite_view_entry", sprite_view_path)
sprite_view_entry = importlib.util.module_from_spec(spec)
sys.modules["sprite_view_entry"] = sprite_view_entry
spec.loader.exec_module(sprite_view_entry)

export_cli = sprite_view_entry.export_cli
main = sprite_view_entry.main

class TestCLI(unittest.TestCase):
    @patch("sprite_view_entry.find_sprite_frames")
    @patch("sprite_view_entry.load_settings")
    @patch("PIL.Image.open")
    @patch("os.path.exists")
    def test_export_cli_single_image(self, mock_exists, mock_open, mock_load, mock_find):
        mock_exists.return_value = True
        mock_load.return_value = {
            "default_fps": 15.0,
            "sequence_separators": ["_", "-"],
            "sequence_patterns": ["{prefix}_{number}"]
        }
        mock_find.return_value = ["/path/to/sprite.png"]

        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image.size = (100, 100)
        mock_open.return_value = mock_image

        with patch("os.getcwd", return_value="/mock/cwd"):
            export_cli(["/path/to/sprite.png"], "png")

        mock_open.assert_called_with("/path/to/sprite.png")
        mock_image.convert.assert_called_with("RGBA")
        mock_image.convert.return_value.save.assert_called_with("/mock/cwd/sprite.png", "PNG")

    @patch("sprite_view_entry.find_sprite_frames")
    @patch("sprite_view_entry.load_settings")
    @patch("PIL.Image.open")
    @patch("os.path.exists")
    def test_export_cli_ico_resize(self, mock_exists, mock_open, mock_load, mock_find):
        mock_exists.return_value = True
        mock_load.return_value = {"default_fps": 15.0}
        mock_find.return_value = ["/path/to/sprite.png"]

        mock_image = MagicMock()
        mock_image.mode = "RGBA"
        mock_image.size = (512, 512)
        mock_open.return_value = mock_image

        with patch("os.getcwd", return_value="/mock/cwd"):
            export_cli(["/path/to/sprite.png"], "ico")

        mock_image.resize.assert_called_once()
        mock_image.resize.return_value.save.assert_called_with("/mock/cwd/sprite.ico", format="ICO")

    @patch("sprite_view_entry.load_settings")
    @patch("PIL.Image.open")
    @patch("os.path.exists")
    def test_export_cli_animation_gif(self, mock_exists, mock_open, mock_load):
        mock_exists.return_value = True
        mock_load.return_value = {
            "default_fps": 10.0,
            "sequence_separators": ["_", "-"],
            "sequence_patterns": ["{prefix}_{number}"]
        }

        mock_img1 = MagicMock()
        mock_img1.mode = "RGBA"
        mock_img1.size = (64, 64)
        mock_img2 = MagicMock()
        mock_img2.mode = "RGBA"
        mock_img2.size = (64, 64)

        mock_open.side_effect = [mock_img1, mock_img2]

        with patch("os.getcwd", return_value="/mock/cwd"):
            export_cli(["/path/to/walk_01.png", "/path/to/walk_02.png"], "gif")

        mock_img1.save.assert_called_with(
            "/mock/cwd/walk.gif",
            "GIF",
            save_all=True,
            append_images=[mock_img2],
            duration=100,
            loop=0
        )

    @patch("sprite_view_entry.load_settings")
    @patch("PIL.Image.open")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_export_cli_animation_webm(self, mock_run, mock_exists, mock_open, mock_load):
        mock_exists.return_value = True
        mock_load.return_value = {
            "default_fps": 10.0
        }

        mock_img1 = MagicMock()
        mock_img1.mode = "RGBA"
        mock_img1.size = (64, 64)
        mock_img2 = MagicMock()
        mock_img2.mode = "RGBA"
        mock_img2.size = (64, 64)
        mock_open.side_effect = [mock_img1, mock_img2]

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        with patch("os.getcwd", return_value="/mock/cwd"):
            export_cli(["/path/to/walk_01.png", "/path/to/walk_02.png"], "webm")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-framerate", cmd)
        self.assertIn("10.0", cmd)
        self.assertIn("/mock/cwd/walk.webm", cmd)

    @patch("sprite_view_entry.find_sprite_frames")
    @patch("sprite_view_entry.load_settings")
    @patch("sprite_view_entry.ImagePreviewWindow")
    @patch("sprite_view_entry.ExportOptionsWindow")
    @patch("sprite_view_entry.WindowManager")
    @patch("gi.repository.Gtk.Application")
    @patch("os.path.exists")
    def test_export_cli_choose_dialog(self, mock_exists, mock_gtk_app, mock_wm, mock_export_win, mock_preview_win, mock_load, mock_find):
        mock_exists.return_value = True
        mock_load.return_value = {"default_fps": 15.0}
        mock_find.return_value = ["/path/to/sprite.png"]

        # Call main() to simulate CLI execution with `--export` (which gets parsed as "choose")
        with patch("sys.argv", ["spriteview", "/path/to/sprite.png", "--export"]):
            main()

        # Verify Gtk.Application was created and run
        mock_gtk_app.assert_called_once()
        app_instance = mock_gtk_app.return_value
        app_instance.run.assert_called_once()

        # Simulate Gtk Application activate callback
        connect_calls = app_instance.connect.call_args_list
        activate_func = None
        for call in connect_calls:
            if call[0][0] == "activate":
                activate_func = call[0][1]
                break

        self.assertIsNotNone(activate_func)
        
        # Mock GLib.timeout_add to execute the callback immediately
        def mock_timeout_add(delay, callback, *args):
            callback(*args)
            return 0

        with patch("sprite_view_entry.GLib.timeout_add", side_effect=mock_timeout_add):
            # Call activate function
            activate_func(app_instance)

        # Verify preview window was created and presented
        mock_preview_win.assert_called_once()
        # Verify ExportOptionsWindow was requested via WindowManager
        mock_wm.get_dependent.assert_called_once_with(mock_preview_win.return_value, mock_export_win)

if __name__ == "__main__":
    unittest.main()
