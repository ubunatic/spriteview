# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import json

CONFIG_PATH = os.path.expanduser("~/.config/nautilus-sprite-view/config.json")

def load_settings() -> dict:
    defaults = {
        "default_fps": 15.0,
        "default_mode": 0,
        "remember_fps": True,
        "remember_scope": "sheet",
        "sequence_separators": ["_", "-"],
        "sequence_patterns": [
            "{prefix}_{number}",
            "{prefix}-{number}",
            "{prefix}{number}"
        ],
        "saved_fps": {}
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                loaded = json.load(f)
                for k, v in defaults.items():
                    if k not in loaded:
                        loaded[k] = v
                # Clean up old complicated regex patterns if present
                pats = loaded.get("sequence_patterns", [])
                if pats and any("(?P<" in p for p in pats):
                    loaded["sequence_patterns"] = defaults["sequence_patterns"]
                return loaded
    except Exception as e:
        print(f"Error loading settings: {e}")
    return defaults

def save_settings(settings: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
