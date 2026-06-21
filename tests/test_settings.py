# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch, mock_open
from sprite_view.settings import load_settings, save_settings

class TestSettings(unittest.TestCase):
    @patch("sprite_view.settings.CONFIG_PATH", "/tmp/mock_config.json")
    @patch("os.path.exists")
    def test_load_settings_not_found(self, mock_exists):
        mock_exists.return_value = False
        settings = load_settings()
        self.assertEqual(settings["default_fps"], 15.0)
        self.assertEqual(settings["default_mode"], 0)
        self.assertTrue(settings["remember_fps"])

    @patch("sprite_view.settings.CONFIG_PATH", "/tmp/mock_config.json")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"default_fps": 30.0, "default_mode": 1}')
    def test_load_settings_success(self, mock_file, mock_exists):
        mock_exists.return_value = True
        settings = load_settings()
        self.assertEqual(settings["default_fps"], 30.0)
        self.assertEqual(settings["default_mode"], 1)

    @patch("sprite_view.settings.CONFIG_PATH", "/tmp/mock_config.json")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_settings(self, mock_file, mock_makedirs):
        save_settings({"default_fps": 24.0})
        mock_makedirs.assert_called_once_with("/tmp", exist_ok=True)
        mock_file.assert_called_once_with("/tmp/mock_config.json", "w")

if __name__ == "__main__":
    unittest.main()
