"""
tap/liker_like.py

Core liking logic, progress bar handling, and human-like mode for AniTap workflows.
"""

import time
import random
from ui.prompts import print_info, print_error, print_warning, print_progress_bar, close_progress_bar
from config.config import add_failed_action
from ui.colors import boxed_text

def like_activities(activities, token, config, human_like=False):
    liked = skipped = failed = 0
    failed_ids = []
    total = len(activities)
    bar = print_progress_bar(activities, "Liking Activities")
    try:
        for act in bar:
            try:
                actid = act.get("id")
                if not actid:
                    continue
                if act.get("isLiked", False):
                    skipped += 1
                    continue
                from anilist.api import like_activity
                ok = like_activity(actid, token)
                if ok:
                    liked += 1
                else:
                    failed += 1
                    failed_ids.append(actid)
                    add_failed_action(config, actid)
                if human_like:
                    r = random.random()
                    if r < 0.80:
                        delay = random.uniform(4, 18)
                    elif r < 0.95:
                        delay = random.uniform(30, 120)
                    else:
                        delay = random.uniform(600, 1800)
                    print_info(f"Waiting {int(delay)} seconds (human-like)...")
                    time.sleep(delay)
                else:
                    speed = config.get("liking_speed", "medium")
                    delays = {"fast": 0.5, "medium": 1.5, "slow": 3.0}
                    time.sleep(delays.get(speed, 1.5))
            except KeyboardInterrupt:
                print_warning("Interrupted by user! Saving progress and failed actions.")
                break
            except Exception as e:
                print_error(f"Error liking activity {act.get('id')}: {e}")
                failed += 1
                failed_ids.append(act.get('id'))
                add_failed_action(config, act.get('id'))
    finally:
        close_progress_bar(bar)
    return total, liked, skipped, failed, failed_ids