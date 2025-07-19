"""
config/config.py

Handles AniTap configuration management:
- Loads and saves user settings (JSON).
- Config includes: liking speed, default mode, last used account, etc.
- Config file is stored in ~/.anitap_config.json for user privacy.
"""

import os
import json

CONFIG_PATH = os.path.expanduser("~/.anitap_config.json")

DEFAULT_CONFIG = {
    "liking_speed": "medium",        # Options: fast, medium, slow
    "default_mode": "global",        # global, following, profile
    "last_used_account": None,       # AniList username of last authenticated account
    "color_theme": "auto",           # auto, light, dark
    "banner_style": "random",        # random, classic, minimal
    "failed_actions": [],            # List of failed activity IDs for retry
    "other_settings": {}             # For extensibility
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            # Merge with defaults (keep old keys if present)
            config.update(user_cfg)
        except Exception:
            pass
    return config

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_liking_speed(config):
    speed = config.get("liking_speed", "medium")
    if speed not in ("fast", "medium", "slow"):
        speed = "medium"
    return speed

def set_liking_speed(config, speed):
    if speed in ("fast", "medium", "slow"):
        config["liking_speed"] = speed
        save_config(config)
        return True
    return False

def add_failed_action(config, activity_id):
    if "failed_actions" not in config:
        config["failed_actions"] = []
    config["failed_actions"].append(activity_id)
    save_config(config)

def clear_failed_actions(config):
    config["failed_actions"] = []
    save_config(config)

def get_failed_actions(config):
    return config.get("failed_actions", [])

def set_default_mode(config, mode):
    if mode in ("global", "following", "profile"):
        config["default_mode"] = mode
        save_config(config)
        return True
    return False

def set_last_used_account(config, username):
    config["last_used_account"] = username
    save_config(config)