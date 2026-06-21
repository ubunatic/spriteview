# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import json

CONFIG_PATH = os.path.expanduser("~/.config/nautilus-sprite-view/config.json")

def load_settings() -> dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return {
        "default_fps": 15.0,
        "default_mode": 0,
        "remember_fps": True,
        "remember_scope": "sheet",
        "sequence_separators": ["_", "-"],
        "saved_fps": {}
    }

def save_settings(settings: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
