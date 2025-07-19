"""
tap/liker_follow.py

Chain and random follow logic for AniTap workflows.
"""

import random
import requests
from ui.prompts import print_info, print_warning, print_error, print_success, print_progress_bar, close_progress_bar
from anilist.api import (
    get_viewer_info, get_following_user_ids, get_follower_user_ids,
)
from tap.liker_fetch import chain_users
from tap.liker_prompts import ask_for_limit

ANILIST_API = "https://graphql.anilist.co"

def follow_chain_users(config):
    """
    Chain system for follows: start from self → followers/following → their followers/following → ... and follow required number of users.
    """
    token = config.get("token")
    if not token:
        print_error("No AniList token found! Please authenticate in Account Management.")
        return
    count = ask_for_limit("How many random users do you want to follow (chain system)? (Enter number, 'all', or 'unlimited')", default=10)
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

    count = ask_for_limit("How many random users do you want to follow? (Enter number, 'all', or 'unlimited')", default="10")
    print_info("Fetching global activities from multiple pages to find potential users to follow...")
    desired_user_count = count * 3 if count else 100
    user_ids = set()
    max_pages = 10
    page = 1
    from anilist.api import fetch_global_activities, get_viewer_info
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