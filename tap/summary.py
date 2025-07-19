"""
tap/summary.py

Handles AniTap boxed summary after liking operations,
saving failed actions for retry, and retry logic.
"""

from ui.colors import boxed_text, print_success, print_error, print_info
from config.config import get_failed_actions, clear_failed_actions, save_config
from ui.prompts import confirm_boxed

def show_summary(mode, total, liked, skipped, failed):
    # Print a single clean summary box, never nested
    summary = (
        f"Mode: {mode}\n"
        f"Total posts processed: {total}\n"
        f"Liked: {liked}\n"
        f"Skipped (already liked): {skipped}\n"
        f"Failed: {failed}"
    )
    print(boxed_text(summary, "CYAN"))

def save_failed_for_retry(config, failed_ids):
    if failed_ids:
        print_error(f"{len(failed_ids)} actions failed and saved for retry.")
        config["failed_actions"].extend(failed_ids)
        save_config(config)
    else:
        clear_failed_actions(config)

def retry_failed_actions(config, token):
    failed_ids = get_failed_actions(config)
    if not failed_ids:
        print_success("No failed actions to retry!")
        return
    if confirm_boxed(f"Retry {len(failed_ids)} failed actions now?"):
        from anilist.api import like_activity
        retried = 0
        still_failed = []
        for actid in failed_ids:
            ok = like_activity(actid, token)
            if ok:
                retried += 1
            else:
                still_failed.append(actid)
        summary = (
            f"Retried failed actions.\n"
            f"Successfully liked: {retried}\n"
            f"Still failed: {len(still_failed)}"
        )
        print(boxed_text(summary, "CYAN"))
        config["failed_actions"] = still_failed
        save_config(config)
    else:
        print_info("You can retry failed actions later from the main menu.")