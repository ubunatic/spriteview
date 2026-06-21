# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from sprite_view.logo import get_embedded_logo, get_embedded_banner

class TestLogo(unittest.TestCase):
    def test_get_embedded_logo(self):
        # This function should either return a Gdk.Texture or return None cleanly
        # if the GUI / GDK subsystem is not initialized (e.g. in a headless environment).
        logo = get_embedded_logo()
        # Ensure it doesn't crash
        self.assertTrue(logo is None or hasattr(logo, "get_width"))

    def test_get_embedded_banner(self):
        banner = get_embedded_banner()
        self.assertTrue(banner is None or hasattr(banner, "get_width"))

if __name__ == "__main__":
    unittest.main()
