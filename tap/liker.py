"""
tap/liker.py

Implements AniTap's mass-like logic and all modes:
- Global Mode: Like all global activities
- Following Mode: Like activities from users you follow
- Profile Mode: Like all posts on a specific profile
- Human-Like Random Mode: Like activities randomly from global, following, or profiles, with random breaks/delays

Handles:
- Progress bar, rate limit spinner, skipping already-liked posts
- Failed actions saved for retry
- Summary after each operation
"""

import time
import random
from ui.prompts import (
    print_info, print_success, print_error, print_warning,
    confirm_boxed, menu_boxed, prompt_boxed, print_progress_bar
)
from anilist.api import (
    fetch_global_activities, fetch_following_activities, fetch_profile_activities,
    like_activity, get_viewer_info, get_user_id
)
from config.config import (
    add_failed_action, clear_failed_actions, get_failed_actions, save_config, load_config
)
from tap.summary import show_summary, save_failed_for_retry, retry_failed_actions

def like_activities(activities, token, config, desc="Liking", dry_run=False):
    speed = config.get("liking_speed", "medium")
    delays = {"fast": 0.5, "medium": 1.5, "slow": 3.0}
    delay = delays.get(speed, 1.5)

    total = len(activities)
    liked = skipped = failed = 0
    failed_ids = []

    if total == 0:
        print_warning("No activities found to process.")
        return total, liked, skipped, failed, failed_ids

    bar = print_progress_bar(activities, desc)
    for act in bar:
        try:
            actid = act["id"]
            if act.get("isLiked", False):
                skipped += 1
                continue
            if not dry_run:
                ok = like_activity(actid, token)
                if ok:
                    liked += 1
                else:
                    failed += 1
                    failed_ids.append(actid)
                    add_failed_action(config, actid)
            else:
                print_info(f"[Dry Run] Would like activity {actid}")
                liked += 1
            time.sleep(delay)
        except KeyboardInterrupt:
            print_warning("Interrupted by user! Saving progress and failed actions.")
            break
        except Exception as e:
            print_error(f"Error liking activity {actid}: {e}")
            failed += 1
            failed_ids.append(actid)
            add_failed_action(config, actid)

    print_success(f"Done! Total: {total}, Liked: {liked}, Skipped: {skipped}, Failed: {failed}")
    return total, liked, skipped, failed, failed_ids

def like_global(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    print_info("Fetching global activities...")
    acts = fetch_global_activities(token)
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, desc="Global Liking")
    show_summary("Global", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)
    if failed_ids:
        retry_failed_actions(config, token)

def like_following(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    print_info("Fetching activities from users you follow...")
    acts = fetch_following_activities(token)
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, desc="Following Liking")
    show_summary("Following", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)
    if failed_ids:
        retry_failed_actions(config, token)

def like_profile(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    username_or_url = prompt_boxed(
        "Enter AniList username or profile URL (type '-help' for info):",
        color="CYAN",
        helpmsg="You can enter either an AniList username or a full profile URL (e.g., https://anilist.co/user/YourName/)."
    )
    # Extract username from URL if needed
    if "/" in username_or_url and "anilist.co/user/" in username_or_url:
        username = username_or_url.strip().split("anilist.co/user/")[-1].split("/")[0]
    else:
        username = username_or_url.strip()
    try:
        user_id = get_user_id(username)
    except Exception as e:
        print_error(f"Could not find user '{username}': {e}")
        return
    print_info(f"Fetching activities from profile '{username}' (ID: {user_id})...")
    acts = fetch_profile_activities(token, user_id)
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, desc=f"Liking {username}'s posts")
    show_summary(f"Profile: {username}", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)
    if failed_ids:
        retry_failed_actions(config, token)

def ask_profile_list():
    print_info("To humanize, you may want to provide a list of AniList usernames whose activities may be liked at random.")
    usernames_raw = prompt_boxed(
        "Enter comma-separated AniList usernames (e.g. user1,user2,user3), or leave blank for none:",
        color="MAGENTA"
    )
    if not usernames_raw.strip():
        return []
    return [u.strip() for u in usernames_raw.split(",") if u.strip()]

def human_like_liker(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return

    # Ask for profile list once per session
    profile_list = ask_profile_list()
    print_info("Starting Human-Like Random Liker Mode...\nAniTap will randomly like activities across global, following, and provided profiles, with human-like breaks.")

    sources = ["global", "following", "profile"]
    session_likes = 0

    while True:
        # Randomly choose source
        src = random.choice(sources if profile_list else ["global", "following"])
        if src == "global":
            acts = fetch_global_activities(token)
            source_name = "Global"
        elif src == "following":
            acts = fetch_following_activities(token)
            source_name = "Following"
        else:
            if not profile_list:
                print_warning("No profile list provided. Skipping profile mode.")
                continue
            prof = random.choice(profile_list)
            try:
                user_id = get_user_id(prof)
                acts = fetch_profile_activities(token, user_id)
                source_name = f"Profile ({prof})"
            except Exception as e:
                print_error(f"Could not fetch activities for profile '{prof}': {e}")
                continue

        # Shuffle and pick a random subset of activities
        if not acts:
            print_warning(f"No activities found for source {source_name}. Skipping.")
            continue

        random.shuffle(acts)
        max_batch = random.randint(2, min(10, len(acts)))
        acts_to_like = random.sample(acts, max_batch)
        print_info(f"Liking {max_batch} activities from {source_name}...")

        # Like with random skip rate and random delay
        for act in acts_to_like:
            # Random skip: sometimes don't like
            if random.random() < 0.15:
                print_info(f"Skipping activity {act['id']} for extra humanization.")
                continue
            ok = like_activity(act['id'], token)
            if ok:
                print_success(f"Liked activity {act['id']} from {source_name}.")
                session_likes += 1
            else:
                print_error(f"Failed to like activity {act['id']}.")
                add_failed_action(config, act['id'])
            # Random delay between likes (sometimes short, sometimes long)
            delay = random.choice([
                random.uniform(7, 22),    # Fast/typical
                random.uniform(30, 120),  # "Thinking"
                random.uniform(300, 1200) # Occasional long break
            ])
            print_info(f"Waiting {int(delay)} seconds before next action...")
            time.sleep(delay)

        # After a random batch, possibly take a "break"
        if random.random() < 0.35:
            break_time = random.choice([60, 180, 900, 1800, 3600])  # 1 min, 3 min, 15 min, 30 min, 1 hr
            msg = f"AniTap is taking a human-like break for {break_time//60} minutes..."
            print_warning(msg)
            time.sleep(break_time)

        # Random session termination (simulate human leaving)
        if session_likes >= random.randint(30, 120):
            print_info(f"Session complete! Total likes this session: {session_likes}")
            break

    print_success(f"Human-Like Random Liker Mode finished! Total likes: {session_likes}.")
    failed_ids = get_failed_actions(config)
    if failed_ids:
        retry_failed_actions(config, token)