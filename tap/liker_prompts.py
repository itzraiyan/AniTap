"""
tap/liker_prompts.py

Prompt and utility functions for AniTap liking workflows.
"""

from ui.prompts import (
    prompt_boxed, print_warning
)

def ask_for_limit(prompt, default=None):
    while True:
        val = prompt_boxed(prompt, default=default, color="MAGENTA")
        if not val:
            if default is not None:
                return default
            continue
        if val.lower() in ("unlimited", "all", "inf", "forever"):
            return None  # None means unlimited/all
        try:
            num = int(val)
            if num < 1:
                print_warning("Please enter a positive integer, 'all', or 'unlimited'.")
                continue
            return num
        except ValueError:
            print_warning("Please enter a number, 'all', or 'unlimited'.")

def ask_for_usernames(prompt, allow_all=True):
    val = prompt_boxed(prompt, color="MAGENTA")
    if not val.strip():
        return None
    if allow_all and val.strip().lower() in ("all", "everybody", "everyone"):
        return None
    names = [u.strip() for u in val.split(",") if u.strip()]
    return names if names else None