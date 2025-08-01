"""
tap/liker.py

AniList Liker Logic, rewritten to use EXACT logic from gaf.py, gaf2.py, sal.py, tree.py for all core features.
UI: Progress bar (TQDM), spinner & rate limit prompts are preserved as in original AniTap code.
Prompts: All user guidance, selection, and context-sensitive wording updated ("all"/"unlimited"/etc.) for better UX.
"""

import time
import random
from ui.prompts import (
    print_info, print_success, print_error, print_warning,
    confirm_boxed, menu_boxed, prompt_boxed, print_progress_bar, close_progress_bar
)
from ui.colors import boxed_text
from anilist.api import (
    fetch_global_activities, fetch_profile_activities,
    get_following_user_ids, get_follower_user_ids, like_activity, get_user_id, get_viewer_info,
    get_following_user_ids_for_other
)
from config.config import (
    add_failed_action, clear_failed_actions, get_failed_actions, save_config, load_config
)

def ask_for_limit(prompt, default=None, context="count"):
    # Context-aware "all" vs "unlimited"
    word = "all" if "user" in prompt.lower() else "unlimited"
    val = prompt_boxed(f"{prompt} (Enter number or '{word}')", default=default, color="MAGENTA")
    if val is None or val == "":
        if default is not None:
            try:
                return int(default)
            except:
                return None
        return None
    if str(val).lower() in ("unlimited", "all", "inf", "forever"):
        return None
    try:
        num = int(val)
        if num < 1:
            print_warning("Please enter a positive integer or 'unlimited'/'all'.")
            return ask_for_limit(prompt, default)
        return num
    except ValueError:
        print_warning("Please enter a number or 'unlimited'/'all'.")
        return ask_for_limit(prompt, default)

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

def fetch_global_activities_until(token, required=None):
    # Uses gaf2.py: fetches all types, paginates and collects until required count
    activities = []
    page = 1
    per_page = 30
    while True:
        acts = fetch_global_activities(token, page=page, per_page=per_page)
        if not acts:
            break
        activities.extend(acts)
        if required is not None and len(activities) >= required:
            activities = activities[:required]
            break
        if len(acts) < per_page:
            break
        page += 1
    return activities

def fetch_all_unliked_activities(fetch_func, token, user_id=None, required=None):
    # Uses sal.py logic: fetches all activities for a user, filters out already liked, paginates
    activities = []
    page = 1
    per_page = 30
    while True:
        if user_id is not None:
            acts = fetch_func(token, user_id, page=page, per_page=per_page)
        else:
            acts = fetch_func(token, page=page, per_page=per_page)
        if not acts:
            break
        for act in acts:
            if not act.get("isLiked", False):
                activities.append(act)
                if required is not None and len(activities) >= required:
                    break
        if required is not None and len(activities) >= required:
            activities = activities[:required]
            break
        if len(acts) < per_page:
            break
        page += 1
    return activities

def like_activities(activities, token, config, human_like=False):
    # Progress bar, rate limit spinner, and delay logic preserved
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
    limit = ask_for_limit("How many global posts to like?", default="100")
    print_info("Fetching global activities...")
    acts = fetch_global_activities_until(token, required=limit)
    acts = [a for a in acts if not a.get("isLiked", False)]
    if not acts:
        print_warning("No unliked global activities found!")
        return
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Global", total, liked, skipped, failed)

def like_following(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    user_list = get_following_user_ids(token)
    if not user_list:
        print_warning("You have no following!")
        return
    num_users = ask_for_limit("How many users from your following to pick?", default="10")
    if num_users and num_users < len(user_list):
        user_list = random.sample(user_list, num_users)
    acts = []
    for uid in user_list:
        acts.extend(fetch_all_unliked_activities(fetch_profile_activities, token, uid))
    if not acts:
        print_warning("No activities found for following users!")
        return
    limit = ask_for_limit("How many posts to like from your following list?", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Following", total, liked, skipped, failed)

def like_followers(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    user_list = get_follower_user_ids(token)
    if not user_list:
        print_warning("You have no followers!")
        return
    num_users = ask_for_limit("How many users from your followers to pick?", default="10")
    if num_users and num_users < len(user_list):
        user_list = random.sample(user_list, num_users)
    acts = []
    for uid in user_list:
        acts.extend(fetch_all_unliked_activities(fetch_profile_activities, token, uid))
    if not acts:
        print_warning("No activities found for follower users!")
        return
    limit = ask_for_limit("How many posts to like from your followers list?", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Followers", total, liked, skipped, failed)

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
    limit = ask_for_limit("How many posts to like per profile?", default="100")
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

def chain_users(token, required=100, max_depth=10, branch_width=10):
    # Uses tree.py logic for chain expansion, BFS with visited set
    try:
        viewer = get_viewer_info(token)
        self_id = viewer["id"]
    except Exception:
        self_id = None

    collected = set()
    queue = []
    first_layer = set(get_following_user_ids(token))
    queue.extend(first_layer)
    collected.update(first_layer)
    depth = 0

    while len(collected) < required and queue and depth < max_depth:
        next_queue = []
        for uid in queue[:branch_width]:
            if uid == self_id:
                continue
            try:
                next_following = set(get_following_user_ids_for_other(token, uid))
            except Exception:
                next_following = set()
            new_ids = next_following - collected
            next_queue.extend(list(new_ids))
            collected.update(new_ids)
            if len(collected) >= required:
                break
        queue = next_queue
        depth += 1
        if not queue:
            break
    if self_id is not None:
        collected.discard(self_id)
    return list(collected)[:required]

def follow_chain_users(config):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    count = ask_for_limit("How many random users do you want to follow (chain system)?", default=10)
    print_info("Building chain of users for follow...")
    user_ids = chain_users(token, required=count if count is not None else 50)
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
    print_info(f"Attempting to follow {len(user_ids)} users (chain system)...")
    followed = failed = 0
    bar = print_progress_bar(user_ids, "Following Users (Chain)")
    import requests
    ANILIST_API = "https://graphql.anilist.co"
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
    # Uses gaf2.py logic for user ID extraction from global activities
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return

    count = ask_for_limit("How many random users do you want to follow?", default="10")
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
    import requests
    ANILIST_API = "https://graphql.anilist.co"
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

def human_like_liker(config):
    # Human-like mode, using random selection and delays, as in original code but with proper logic
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    print_info(
        "Starting Human-Like Random Liker Mode...\n"
        "AniTap will randomly like activities across global, following, followers, and optionally specified profiles, with realistic human-like breaks."
    )

    profile_list = ask_for_usernames(
        "Optional: Enter AniList usernames (comma-separated) to include in the mix, or just press Enter for default sources:",
        allow_all=False
    )
    total_likes = ask_for_limit(
        "Total number of likes for this session?", default="100"
    )
    session_time_limit = ask_for_limit(
        "Or run for how many minutes? (Enter number or leave blank for no time limit):", default=None
    )
    session_likes = 0
    session_start = time.time()

    sources = ["global", "following", "followers"]
    if profile_list:
        sources.append("profile")

    try:
        while True:
            if session_time_limit is not None:
                if (time.time() - session_start) > (session_time_limit * 60):
                    print_success(f"Session time limit reached. Total likes this session: {session_likes}")
                    break
            src = random.choice(sources)
            acts = []
            source_name = ""
            if src == "global":
                acts = fetch_global_activities_until(token)
                acts = [a for a in acts if not a.get("isLiked", False)]
                source_name = "Global"
            elif src == "following":
                user_list = get_following_user_ids(token)
                if not user_list:
                    print_warning("You are not following anyone! Skipping following mode.")
                    continue
                uid = random.choice(user_list)
                acts = fetch_all_unliked_activities(fetch_profile_activities, token, uid)
                source_name = f"Following ({uid})"
            elif src == "followers":
                user_list = get_follower_user_ids(token)
                if not user_list:
                    print_warning("You have no followers! Skipping followers mode.")
                    continue
                uid = random.choice(user_list)
                acts = fetch_all_unliked_activities(fetch_profile_activities, token, uid)
                source_name = f"Follower ({uid})"
            else:  # profile
                if not profile_list:
                    continue
                prof = random.choice(profile_list)
                user_id = get_user_id(prof)
                acts = fetch_all_unliked_activities(fetch_profile_activities, token, user_id)
                source_name = f"Profile ({prof})"

            if not acts:
                continue

            random.shuffle(acts)
            batch_size = random.randint(10, 30)
            acts_to_like = acts[:batch_size]
            if total_likes is not None and session_likes + len(acts_to_like) > total_likes:
                acts_to_like = acts_to_like[:total_likes - session_likes]
            if not acts_to_like:
                continue
            print_info(f"Liking {len(acts_to_like)} activities from {source_name}...")
            total, liked, skipped, failed, failed_ids = like_activities(acts_to_like, token, config, human_like=True)
            session_likes += liked

            show_summary(f"Human-like: {source_name}", total, liked, skipped, failed)

            if random.random() < 0.35:
                break_time = random.choice([60, 180, 900, 1800, 3600])
                msg = f"AniTap is taking a human-like break for {break_time//60} minutes..."
                print_warning(msg)
                try:
                    for i in range(break_time):
                        time.sleep(1)
                except KeyboardInterrupt:
                    print_warning("Interrupted during human-like break. Ending session early.")
                    break

            if random.random() < 0.1:
                idle_time = random.randint(60, 300)
                print_info(f"AniTap is idling like a distracted human for {idle_time//60} minutes...")
                try:
                    for i in range(idle_time):
                        time.sleep(1)
                except KeyboardInterrupt:
                    print_warning("Interrupted while idling. Ending session early.")
                    break

            if total_likes is not None and session_likes >= total_likes:
                print_success(f"Session complete! Total likes this session: {session_likes}")
                break

    except KeyboardInterrupt:
        print_warning("Session interrupted by user. Saving progress and showing summary...")

    print_success(f"Human-Like Random Liker Mode finished! Total likes: {session_likes}.")