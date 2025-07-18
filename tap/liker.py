"""
tap/liker.py

Flexible AniList Liker Logic:
- Interactive CLI: asks user for how many posts to like (or unlimited), number of users from following/followers (or all), and profiles.
- Liking Modes: global, following, followers, profile, chain (for follows & likes).
- Human-like mode: random delays, breaks, source switching.
- Never likes already-liked posts.
- Shows clean boxed summary with stats.
- Chain system: follow random users by traversing your followings/followers, then theirs, etc.
"""

import time
import random
from ui.prompts import (
    print_info, print_success, print_error, print_warning,
    confirm_boxed, menu_boxed, prompt_boxed, print_progress_bar, close_progress_bar
)
from ui.colors import boxed_text
from anilist.api import (
    fetch_global_activities, fetch_following_activities, fetch_profile_activities,
    get_following_user_ids, get_follower_user_ids, like_activity, get_user_id, get_viewer_info
)
from config.config import (
    add_failed_action, clear_failed_actions, get_failed_actions, save_config, load_config
)

import requests

ANILIST_API = "https://graphql.anilist.co"

def ask_for_limit(prompt, default=None):
    while True:
        val = prompt_boxed(prompt, default=default, color="MAGENTA")
        if not val:
            if default is not None:
                return default
            continue
        if val.lower() in ("unlimited", "inf", "forever"):
            return None  # None means unlimited
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
    if not val.strip():
        return None
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

def fetch_all_unliked_activities(fetch_func, token, user_id=None, required=None):
    activities = []
    page = 1
    per_page = 30
    unliked = []
    while True:
        if user_id is not None:
            acts = fetch_func(token, user_id, page=page, per_page=per_page)
        else:
            acts = fetch_func(token, page=page, per_page=per_page)
        if not acts:
            break
        for act in acts:
            if not act.get("isLiked", False):
                unliked.append(act)
                if required is not None and len(unliked) >= required:
                    break
        if required is not None and len(unliked) >= required:
            break
        if len(acts) < per_page:
            break
        page += 1
    if required is not None:
        unliked = unliked[:required]
    return unliked

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

def like_global(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    limit = ask_for_limit("How many global posts to like? (Enter number or 'unlimited')", default="100")
    print_info("Fetching global activities...")
    acts = fetch_all_unliked_activities(fetch_global_activities, token, None, limit)
    if not acts:
        print_warning("No unliked global activities found!")
        return
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Global", total, liked, skipped, failed)

def like_following(config, human_like=False):
    like_following_or_followers(config, mode="following", human_like=human_like)

def like_followers(config, human_like=False):
    like_following_or_followers(config, mode="followers", human_like=human_like)

def like_following_or_followers(config, mode="following", human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    user_list = None
    if mode == "following":
        print_info("Fetching your following list...")
        user_list = get_following_user_ids(token)
    elif mode == "followers":
        print_info("Fetching your follower list...")
        user_list = get_follower_user_ids(token)
    else:
        print_error(f"Unknown mode: {mode}")
        return
    if not user_list:
        print_warning(f"You have no {mode}!")
        return
    num_users = ask_for_limit(f"How many users from your {mode} to pick? (Enter number or 'all')", default="10")
    if num_users and num_users < len(user_list):
        user_list = random.sample(user_list, num_users)
    acts = []
    for uid in user_list:
        acts.extend(fetch_all_unliked_activities(fetch_profile_activities, token, uid))
    if not acts:
        print_warning(f"No activities found for {mode} users!")
        return
    limit = ask_for_limit(f"How many posts to like from your {mode} list? (Enter number or 'unlimited')", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary(mode.capitalize(), total, liked, skipped, failed)

def like_profile(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    usernames = ask_for_usernames(
        "Enter one or more AniList usernames (comma-separated) to like posts from (leave blank to skip):",
        allow_all=False
    )
    if not usernames:
        print_warning("No usernames provided!")
        return
    limit = ask_for_limit("How many posts to like per profile? (Enter number or 'unlimited')", default="100")
    for username in usernames:
        try:
            user_id = get_user_id(username)
            print_info(f"Fetching ALL activities from profile '{username}' (ID: {user_id}), filtering out liked ones...")
            acts = fetch_all_unliked_activities(fetch_profile_activities, token, user_id, limit)
            if not acts:
                print_warning(f"No unliked activities found for user '{username}'.")
                continue
            total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
            show_summary(f"Profile: {username}", total, liked, skipped, failed)
        except Exception as e:
            print_error(f"Could not process user '{username}': {e}")

def chain_users_for_follow(token, depth=3, branch_width=5, max_users=50):
    """
    Chain system for follow: traverse your followings/followers, then theirs, etc.
    Returns a set of user IDs up to max_users, excluding self.
    """
    try:
        viewer = get_viewer_info(token)
        self_id = viewer["id"]
    except Exception:
        self_id = None

    visited = set()
    current_layer = set(get_following_user_ids(token) + get_follower_user_ids(token))
    all_ids = set(current_layer)

    for layer in range(depth):
        next_layer = set()
        for uid in random.sample(list(current_layer), min(branch_width, len(current_layer))):
            if uid in visited or uid == self_id:
                continue
            visited.add(uid)
            # Fetch this user's followings & followers
            try:
                following = get_following_user_ids_for_other(token, uid)
                followers = get_follower_user_ids_for_other(token, uid)
                for idlist in (following, followers):
                    for new_uid in idlist:
                        if new_uid != self_id:
                            next_layer.add(new_uid)
            except Exception:
                continue
        all_ids.update(next_layer)
        current_layer = next_layer
        if len(all_ids) >= max_users:
            break
    # Remove self if present
    if self_id is not None:
        all_ids.discard(self_id)
    return list(all_ids)[:max_users]

def get_following_user_ids_for_other(token, user_id):
    """
    Fetch following user IDs for another user (not viewer).
    """
    query = '''
    query ($userId: Int) {
      User(id: $userId) {
        following(sort: ID_DESC) {
          id
        }
      }
    }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    variables = { "userId": user_id }
    resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
    if resp.status_code == 200:
        users = resp.json()["data"]["User"]["following"]
        return [u["id"] for u in users]
    return []

def get_follower_user_ids_for_other(token, user_id):
    """
    Fetch follower user IDs for another user (not viewer).
    """
    query = '''
    query ($userId: Int) {
      User(id: $userId) {
        followers(sort: ID_DESC) {
          id
        }
      }
    }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    variables = { "userId": user_id }
    resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
    if resp.status_code == 200:
        users = resp.json()["data"]["User"]["followers"]
        return [u["id"] for u in users]
    return []

def follow_chain_users(config):
    """
    Chain system for follows: traverse your followings/followers, then theirs, etc., and follow random users.
    """
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return

    depth = ask_for_limit("Chain depth (how many levels to go, e.g. 2-4 recommended)?", default=3)
    branch_width = ask_for_limit("Branch width (how many users to sample per level)?", default=5)
    count = ask_for_limit("How many random users do you want to follow? (Enter number or 'unlimited')", default=10)
    print_info("Building chain of users for follow...")
    user_ids = chain_users_for_follow(token, depth=depth, branch_width=branch_width, max_users=count*2 if count else 50)
    try:
        viewer = get_viewer_info(token)
        self_id = viewer["id"]
        user_ids = [uid for uid in user_ids if uid != self_id]
    except Exception:
        pass

    if not user_ids:
        print_warning("Could not find any users to follow via chain.")
        return

    random.shuffle(user_ids)
    if count is not None and count < len(user_ids):
        user_ids = user_ids[:count]
    else:
        user_ids = user_ids[:count] if count else user_ids

    print_info(f"Attempting to follow {len(user_ids)} users (chain system)...")
    followed = failed = 0
    bar = print_progress_bar(user_ids, "Following Users (Chain)")
    try:
        for uid in bar:
            query = '''
            mutation ($userId: Int) {
                FollowUser(userId: $userId) {
                    id
                    isFollowing
                }
            }
            '''
            headers = {"Authorization": f"Bearer {token}"}
            variables = {"userId": uid}
            resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data", {}).get("FollowUser", {}).get("isFollowing", False):
                    followed += 1
                else:
                    failed += 1
            else:
                failed += 1
                print_error(f"Failed to follow user {uid}: {resp.status_code} {resp.text}")
    finally:
        close_progress_bar(bar)

    print_success(f"Finished chain follow! Followed: {followed}, Failed: {failed}")

def follow_random_users(config):
    """
    Regular random user follow (global activities based).
    """
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return

    count = ask_for_limit("How many random users do you want to follow? (Enter number or 'unlimited')", default="10")
    print_info("Fetching global activities from multiple pages to find potential users to follow...")
    desired_user_count = count * 3 if count else 100
    user_ids = set()
    max_pages = 10
    page = 1
    while len(user_ids) < desired_user_count and page <= max_pages:
        acts = fetch_global_activities(token, page=page, per_page=30)
        for act in acts:
            uid = None
            if "user" in act and isinstance(act["user"], dict):
                uid = act["user"].get("id")
            uid = uid or act.get("userId") or act.get("user_id")
            if uid:
                user_ids.add(uid)
        if not acts or len(acts) < 30:
            break
        page += 1

    try:
        viewer = get_viewer_info(token)
        self_id = viewer["id"]
        user_ids.discard(self_id)
    except Exception:
        pass

    user_ids = list(user_ids)
    if not user_ids:
        print_warning("Could not find any users to follow.")
        return

    random.shuffle(user_ids)
    if count is not None and count < len(user_ids):
        user_ids = user_ids[:count]
    else:
        user_ids = user_ids[:count] if count else user_ids

    print_info(f"Attempting to follow {len(user_ids)} users...")
    followed = failed = 0
    bar = print_progress_bar(user_ids, "Following Users")
    try:
        for uid in bar:
            query = '''
            mutation ($userId: Int) {
                FollowUser(userId: $userId) {
                    id
                    isFollowing
                }
            }
            '''
            headers = {"Authorization": f"Bearer {token}"}
            variables = {"userId": uid}
            resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data", {}).get("FollowUser", {}).get("isFollowing", False):
                    followed += 1
                else:
                    failed += 1
            else:
                failed += 1
                print_error(f"Failed to follow user {uid}: {resp.status_code} {resp.text}")
    finally:
        close_progress_bar(bar)

    print_success(f"Finished following users! Followed: {followed}, Failed: {failed}")