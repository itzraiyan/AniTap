"""
tap/liker.py

Public interface for AniTap liking workflows.
Re-exports major logic from submodules.
Other code (main.py etc) can keep using tap.liker as before.
"""

from .liker_prompts import (
    ask_for_limit,
    ask_for_usernames
)
from .liker_fetch import (
    fetch_global_activities_until,
    fetch_all_unliked_activities,
    chain_users,
    get_following_user_ids_for_other,
    get_follower_user_ids_for_other,
)
from .liker_like import (
    like_activities,
)
from .liker_follow import (
    follow_chain_users,
    follow_random_users
)
from .liker_summary import (
    show_summary,
    save_failed_for_retry,
    retry_failed_actions
)

# High-level workflow functions (as before)
def like_global(config, human_like=False):
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    limit = ask_for_limit("How many global posts to like? (Enter number, 'all', or 'unlimited')", default="100")
    print_info("AniTap will repeatedly refresh global activities until your requested number is fulfilled.")
    acts = fetch_global_activities_until(token, required=limit)
    acts = [a for a in acts if not a.get("isLiked", False)]
    if not acts:
        print_warning("No unliked global activities found!")
        return
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Global", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)

def like_following(config, human_like=False):
    from anilist.api import get_following_user_ids, fetch_profile_activities
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    user_list = get_following_user_ids(token)
    if not user_list:
        print_warning("You have no following!")
        return
    num_users = ask_for_limit("How many users from your following to pick? (Enter number, 'all', or 'unlimited')", default="10")
    if num_users and num_users < len(user_list):
        import random
        user_list = random.sample(user_list, num_users)
    acts = []
    for uid in user_list:
        acts.extend(fetch_all_unliked_activities(fetch_profile_activities, token, uid))
    if not acts:
        print_warning("No activities found for following users!")
        return
    limit = ask_for_limit("How many posts to like from your following list? (Enter number, 'all', or 'unlimited')", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Following", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)

def like_followers(config, human_like=False):
    from anilist.api import get_follower_user_ids, fetch_profile_activities
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    user_list = get_follower_user_ids(token)
    if not user_list:
        print_warning("You have no followers!")
        return
    num_users = ask_for_limit("How many users from your followers to pick? (Enter number, 'all', or 'unlimited')", default="10")
    if num_users and num_users < len(user_list):
        import random
        user_list = random.sample(user_list, num_users)
    acts = []
    for uid in user_list:
        acts.extend(fetch_all_unliked_activities(fetch_profile_activities, token, uid))
    if not acts:
        print_warning("No activities found for follower users!")
        return
    limit = ask_for_limit("How many posts to like from your followers list? (Enter number, 'all', or 'unlimited')", default="100")
    if limit:
        acts = acts[:limit]
    total, liked, skipped, failed, failed_ids = like_activities(acts, token, config, human_like=human_like)
    show_summary("Followers", total, liked, skipped, failed)
    save_failed_for_retry(config, failed_ids)

def like_profile(config, human_like=False):
    from anilist.api import get_user_id, fetch_profile_activities
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
    limit = ask_for_limit("How many posts to like per profile? (Enter number, 'all', or 'unlimited')", default="100")
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
            save_failed_for_retry(config, failed_ids)
        except Exception as e:
            print_error(f"Could not process user '{username}': {e}")

def human_like_liker(config):
    from .liker_like import like_activities
    from .liker_fetch import fetch_global_activities_until, fetch_all_unliked_activities
    from anilist.api import get_following_user_ids, get_follower_user_ids, get_user_id, fetch_profile_activities
    import time, random

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
        "Total number of likes for this session? (Enter number, 'all', or 'unlimited')",
        default="100"
    )
    session_time_limit = ask_for_limit(
        "Or run for how many minutes? (Enter number or leave blank for no time limit):",
        default=None
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
            save_failed_for_retry(config, failed_ids)

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