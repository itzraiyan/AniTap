"""
tap/liker_fetch.py

Activity fetching and chain logic for AniTap liking workflows.
"""

from anilist.api import (
    fetch_global_activities, fetch_profile_activities,
    get_following_user_ids, get_follower_user_ids, get_user_id, get_viewer_info
)
from ui.colors import boxed_text
import requests

ANILIST_API = "https://graphql.anilist.co"

def fetch_global_activities_until(token, required=None):
    """
    Fetch global activities, paginating until required amount is reached.
    Always fetch next page if more are needed.
    """
    activities = []
    page = 1
    per_page = 30  # AniList default
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
    """
    Paginate through activities, filtering out already liked, and stopping when required amount is collected.
    """
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

def chain_users(token, required=100, max_depth=10, branch_width=10):
    """
    Chain system for random users: start from your own followers/following, expand via their followers/following recursively.
    """
    try:
        viewer = get_viewer_info(token)
        self_id = viewer["id"]
    except Exception:
        self_id = None

    from anilist.api import get_following_user_ids, get_follower_user_ids

    collected = set()
    queue = []
    first_layer = set(get_following_user_ids(token)) | set(get_follower_user_ids(token))
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
                next_followers = set(get_follower_user_ids_for_other(token, uid))
            except Exception:
                next_following = set()
                next_followers = set()
            new_ids = (next_following | next_followers) - collected
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

def get_following_user_ids_for_other(token, user_id):
    """
    Get the public following list of any user.
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
        users = resp.json().get("data", {}).get("User", {}).get("following", [])
        return [u["id"] for u in users]
    return []

def get_follower_user_ids_for_other(token, user_id):
    """
    Get the public followers list of any user.
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
        users = resp.json().get("data", {}).get("User", {}).get("followers", [])
        return [u["id"] for u in users]
    return []