# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch
from sprite_view.utils import (
    format_size,
    find_sprite_frames,
    get_ansi_256_colors,
    describe_cube_color,
    rgb_to_ansi,
    get_short_hex,
)

class TestUtils(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(format_size(100), "100 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 5), "5.0 GB")

    @patch("os.listdir")
    def test_find_sprite_frames_matched(self, mock_listdir):
        # Mock directory structure for matching prefix_0001.png frames
        mock_listdir.return_value = [
            "sprite_0001.png",
            "sprite_0002.png",
            "sprite_0003.png",
            "other_file.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite_0002.png")
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], "/path/to/dir/sprite_0001.png")
        self.assertEqual(frames[1], "/path/to/dir/sprite_0002.png")
        self.assertEqual(frames[2], "/path/to/dir/sprite_0003.png")

    @patch("os.listdir")
    def test_find_sprite_frames_matched_3digit(self, mock_listdir):
        mock_listdir.return_value = [
            "sprite_001.png",
            "sprite_002.png",
            "sprite_003.png",
            "other_file.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite_002.png")
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], "/path/to/dir/sprite_001.png")
        self.assertEqual(frames[2], "/path/to/dir/sprite_003.png")

    @patch("os.listdir")
    def test_find_sprite_frames_matched_2digit(self, mock_listdir):
        mock_listdir.return_value = [
            "sprite_01.png",
            "sprite_02.png",
            "sprite_03.png",
            "other_file.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite_02.png")
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], "/path/to/dir/sprite_01.png")
        self.assertEqual(frames[2], "/path/to/dir/sprite_03.png")

    @patch("os.listdir")
    def test_find_sprite_frames_no_cross_digit_match(self, mock_listdir):
        # 3-digit input should not match 4-digit files
        mock_listdir.return_value = [
            "sprite_0001.png",
            "sprite_0002.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite_001.png")
        self.assertEqual(frames, ["/path/to/dir/sprite_001.png"])

    @patch("os.listdir")
    def test_find_sprite_frames_hyphen_separator(self, mock_listdir):
        mock_listdir.return_value = [
            "screen-sheet-001.png",
            "screen-sheet-002.png",
            "screen-sheet-003.png",
            "other_file.png",
        ]
        frames = find_sprite_frames("/path/to/dir/screen-sheet-001.png")
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], "/path/to/dir/screen-sheet-001.png")
        self.assertEqual(frames[2], "/path/to/dir/screen-sheet-003.png")

    @patch("os.listdir")
    def test_find_sprite_frames_custom_separator(self, mock_listdir):
        mock_listdir.return_value = [
            "sprite.001.png",
            "sprite.002.png",
            "sprite.003.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite.001.png", separators=[".", "_"])
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], "/path/to/dir/sprite.001.png")

    @patch("os.listdir")
    def test_find_sprite_frames_no_match_empty_separators(self, mock_listdir):
        mock_listdir.return_value = ["sprite_001.png"]
        frames = find_sprite_frames("/path/to/dir/sprite_001.png", separators=[])
        self.assertEqual(frames, ["/path/to/dir/sprite_001.png"])

    @patch("os.listdir")
    def test_find_sprite_frames_no_cross_sep_match(self, mock_listdir):
        # hyphen-separated should not match underscore-separated files
        mock_listdir.return_value = [
            "sprite_001.png",
            "sprite_002.png",
        ]
        frames = find_sprite_frames("/path/to/dir/sprite-001.png")
        self.assertEqual(frames, ["/path/to/dir/sprite-001.png"])

    @patch("os.listdir")
    def test_find_sprite_frames_no_match(self, mock_listdir):
        mock_listdir.return_value = [
            "sprite_0001.png",
            "other_file.png",
        ]
        # Not matching sequence pattern
        frames = find_sprite_frames("/path/to/dir/other_file.png")
        self.assertEqual(frames, ["/path/to/dir/other_file.png"])

    def test_get_ansi_256_colors(self):
        colors = get_ansi_256_colors()
        self.assertEqual(len(colors), 256)
        # Check standard low-intensity white
        self.assertEqual(colors[7], (192, 192, 192))
        # Check bright white
        self.assertEqual(colors[15], (255, 255, 255))

    def test_describe_cube_color(self):
        # Gray
        self.assertEqual(describe_cube_color(2, 2, 2), "Dark Gray")
        # Yellow
        self.assertEqual(describe_cube_color(5, 5, 0), "Bright Yellow")
        # Cyan
        self.assertEqual(describe_cube_color(0, 3, 3), "Medium Cyan")
        # Red
        self.assertEqual(describe_cube_color(5, 1, 0), "Bright Red")
        self.assertEqual(describe_cube_color(5, 0, 0), "Bright Red-Purple")
        # Orange
        self.assertEqual(describe_cube_color(5, 2, 0), "Bright Orange")

    def test_rgb_to_ansi(self):
        # Precise black matches index 0
        idx, name = rgb_to_ansi(0, 0, 0)
        self.assertEqual(idx, 0)
        self.assertEqual(name, "Black")

        # White matches index 15
        idx, name = rgb_to_ansi(255, 255, 255)
        self.assertEqual(idx, 15)
        self.assertEqual(name, "Bright White")

    def test_get_short_hex(self):
        # Can be shortened
        self.assertEqual(get_short_hex(255, 255, 255), "#fff")
        self.assertEqual(get_short_hex(0, 17, 34), "#012")
        # Cannot be shortened
        self.assertEqual(get_short_hex(255, 255, 254), "#fffffe")
        self.assertEqual(get_short_hex(12, 34, 56), "#0c2238")

if __name__ == "__main__":
    unittest.main()
