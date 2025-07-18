"""
tap/liker.py

Flexible AniList Liker Logic:
- Interactive CLI: asks user for how many posts to like (or unlimited), number of users from following (or all), and profiles.
- Liking Modes: global, following (pick users), profile (pick one or multiple).
- Human-like mode: random delays, breaks, source switching.
- Never likes already-liked posts.
- Shows clean boxed summary with stats.
"""

import time
import random
from ui.prompts import (
    print_info, print_success, print_error, print_warning,
    confirm_boxed, menu_boxed, prompt_boxed, print_progress_bar
)
from ui.colors import boxed_text
from anilist.api import (
    fetch_global_activities, fetch_following_activities, fetch_profile_activities,
    like_activity, get_viewer_info, get_user_id, follow_user, get_following_user_ids, search_users
)
from config.config import (
    add_failed_action, clear_failed_actions, get_failed_actions, save_config, load_config
)

def ask_for_limit(prompt, default=None):
    while True:
        val = prompt_boxed(prompt, default=default, color="MAGENTA")
        if val.lower() in ("unlimited", "inf", "forever"):
            return None
        try:
            num = int(val)
            if num < 1:
                print_warning("Please enter a positive integer or 'unlimited'.")
                continue
            return num
        except ValueError:
            print_warning("Please enter a number or 'unlimited'.")

def ask_for_usernames(prompt, allow_all=True):
    val = prompt_boxed(prompt, color="MAGENTA")
    if allow_all and val.strip().lower() in ("all", "everybody", "everyone"):
        return None
    names = [u.strip() for u in val.split(",") if u.strip()]
    return names if names else None

def show_summary(mode, total, liked, skipped, failed):
    summary = (
        f"Mode: {mode}\n"
        f"Total posts processed: {total}\n"
        f"Liked: {liked}\n"
        f"Skipped (already liked): {skipped}\n"
        f"Failed: {failed}"
    )
    print(boxed_text(summary, "CYAN"))

def fetch_all_activities(fetch_func, token, limit=None):
    # Fetches activities across all available pages, up to the limit
    activities = []
    page = 1
    per_page = 30
    while True:
        acts = fetch_func(token, page=page, per_page=per_page)
        if not acts:
            break
        activities.extend(acts)
        if limit and len(activities) >= limit:
            activities = activities[:limit]
            break
        if len(acts) < per_page:
            break
        page += 1
    return activities

def like_activities(activities, token, config, human_like=False):
    liked = skipped = failed = 0
    failed_ids = []
    total = len(activities)
    bar = print_progress_bar(activities, "Liking Activities")
    for act in bar:
        try:
            actid = act.get("id")
            if not actid:
                continue
            if act.get("isLiked", False):
                skipped += 1
                continue
            ok = like_activity(actid, token)
            if ok:
                liked += 1
            else:
                failed += 1
                failed_ids.append(actid)
                add_failed_action(config, actid)
            # Human-like delays
            if human_like:
                r = random.random()
                if r < 0.80:
                    delay = random.uniform(4, 18)
                elif r < 0.95:
                    delay = random.uniform(30, 120)
                else:
                    delay = random.uniform(600, 1800)  # 10-30 min
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
    return total, liked, skipped, failed, failed_ids

def like_global(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    limit = ask_for_limit("How many global posts to like? (Enter number or 'unlimited')", default="100")
    print_info("Fetching global activities...")
    acts = fetch_all_activities(fetch_global_activities, token, limit)
    if not acts:
        print_warning("No global activities found!")
        return
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Global", total, liked, skipped, failed)

def like_following(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    num_users = ask_for_limit("How many users from your following list to pick? (Enter number or 'all')", default="10")
    print_info("Fetching your following list...")
    following_ids = get_following_user_ids(token)
    if not following_ids:
        print_warning("You are not following anyone!")
        return
    if num_users and num_users < len(following_ids):
        following_ids = random.sample(following_ids, num_users)
    acts = []
    for uid in following_ids:
        acts.extend(fetch_all_activities(lambda t, page, per_page: fetch_profile_activities(t, uid, page=page, per_page=per_page), token))
    if not acts:
        print_warning("No activities found for followed users!")
        return
    limit = ask_for_limit("How many posts to like from your following list? (Enter number or 'unlimited')", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Following", total, liked, skipped, failed)

def like_profile(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    usernames = ask_for_usernames("Enter one or more AniList usernames (comma-separated) to like all posts from:")
    if not usernames:
        print_warning("No usernames provided!")
        return
    limit = ask_for_limit("How many posts to like per profile? (Enter number or 'unlimited')", default="100")
    for username in usernames:
        try:
            user_id = get_user_id(username)
            print_info(f"Fetching activities from profile '{username}' (ID: {user_id})...")
            acts = fetch_all_activities(lambda t, page, per_page: fetch_profile_activities(t, user_id, page=page, per_page=per_page), token, limit)
            if not acts:
                print_warning(f"No activities found for user '{username}'.")
                continue
            total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
            show_summary(f"Profile: {username}", total, liked, skipped, failed)
        except Exception as e:
            print_error(f"Could not process user '{username}': {e}")

def human_like_liker(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    print_info("Starting Human-Like Random Liker Mode...\nAniTap will randomly like activities across global, following, and provided profiles, with human-like breaks.")

    # Ask for profile list for randomness
    profile_list = ask_for_usernames("Enter comma-separated AniList usernames for human-like mode (or leave blank):", allow_all=False)
    limit = ask_for_limit("How many posts to like this session? (Enter number or 'unlimited')", default="100")
    session_likes = 0

    sources = ["global", "following", "profile"]

    while True:
        src = random.choice([s for s in sources if (s != "profile" or profile_list)])
        if src == "global":
            acts = fetch_all_activities(fetch_global_activities, token)
            source_name = "Global"
        elif src == "following":
            following_ids = get_following_user_ids(token)
            if not following_ids:
                print_warning("You are not following anyone! Skipping following mode.")
                continue
            uid = random.choice(following_ids)
            acts = fetch_all_activities(lambda t, page, per_page: fetch_profile_activities(t, uid, page=page, per_page=per_page), token)
            source_name = f"Following ({uid})"
        else:
            prof = random.choice(profile_list)
            user_id = get_user_id(prof)
            acts = fetch_all_activities(lambda t, page, per_page: fetch_profile_activities(t, user_id, page=page, per_page=per_page), token)
            source_name = f"Profile ({prof})"

        random.shuffle(acts)
        batch_size = random.randint(10, 30)
        acts_to_like = []
        for act in acts:
            if not act.get("isLiked", False):
                acts_to_like.append(act)
                if len(acts_to_like) >= batch_size:
                    break
        # Enforce session limit
        if limit is not None and session_likes + len(acts_to_like) > limit:
            acts_to_like = acts_to_like[:limit - session_likes]
        if not acts_to_like:
            continue
        print_info(f"Liking {len(acts_to_like)} activities from {source_name}...")
        total, liked, skipped, failed, failed_ids = like_activities(acts_to_like, token, config, human_like=True)
        session_likes += liked

        show_summary(f"Human-like: {source_name}", total, liked, skipped, failed)
        # Random break
        if random.random() < 0.35:
            break_time = random.choice([60, 180, 900, 1800, 3600])  # 1 min, 3 min, 15 min, 30 min, 1 hr
            msg = f"AniTap is taking a human-like break for {break_time//60} minutes..."
            print_warning(msg)
            time.sleep(break_time)

        if limit is not None and session_likes >= limit:
            print_success(f"Session complete! Total likes this session: {session_likes}")
            break

    print_success(f"Human-Like Random Liker Mode finished! Total likes: {session_likes}.")

def follow_random_users(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    num_to_follow = ask_for_limit("How many random users to follow? (Enter number or 'unlimited')", default="100")
    print_info("Searching for random users to follow...")
    # For demonstration, search users by a popular query. In reality, you'd want to fetch a list of users in some smart way.
    random_users = search_users(token, num_to_follow)
    if not random_users:
        print_warning("No users found to follow!")
        return
    followed = 0
    for user in random_users:
        try:
            if follow_user(user["id"], token):
                followed += 1
                print_success(f"Followed user: {user['name']} (ID: {user['id']})")
            else:
                print_warning(f"Failed to follow user: {user['name']} (ID: {user['id']})")
        except Exception as e:
            print_error(f"Error following user {user['name']}: {e}")
        if num_to_follow and followed >= num_to_follow:
            break
    print_info(f"Followed {followed} users.")