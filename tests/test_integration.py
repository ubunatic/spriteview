# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
import subprocess
import shutil
import os
import sys

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.packed_script = os.path.join(self.root_dir, "dist", "sprite_view.py")
        
        # Ensure the script is packed before running integration tests
        if not os.path.exists(self.packed_script):
            subprocess.run([sys.executable, os.path.join(self.root_dir, "scripts", "pack.py")], check=True)

    def test_help_execution(self):
        """Verify the packaged script runs and responds to --help without errors."""
        res = subprocess.run([sys.executable, self.packed_script, "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Standalone sprite sheet", res.stdout)
        self.assertEqual(res.stderr, "")

    def test_startup_smoke_test(self):
        """Verify that the Gtk application starts up without throwing AttributeErrors or crashing."""
        xvfb = shutil.which("xvfb-run")
        if not xvfb:
            self.skipTest("xvfb-run not available in PATH")

        # Run under xvfb-run with a 2-second timeout to verify it enters Gtk loop and doesn't crash on start
        cmd = [xvfb, "timeout", "2", sys.executable, self.packed_script, "--about"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        # If it ran successfully and was killed by timeout, return code will be 124.
        # If it crashed with a python traceback, fail the test.
        if res.returncode != 124:
            if "Traceback" in res.stderr or "AttributeError" in res.stderr or "ImportError" in res.stderr:
                self.fail(f"Application crashed on startup:\n{res.stderr}")
        else:
            self.assertNotIn("Traceback", res.stderr)
            self.assertNotIn("AttributeError", res.stderr)
            self.assertNotIn("ImportError", res.stderr)

if __name__ == "__main__":
    unittest.main()
