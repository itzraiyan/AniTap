"""
anilist/api.py

Handles all AniList GraphQL API queries and mutations:
- User lookup
- Fetching activities (global/following/profile/followers)
- Like activity mutation
- Get following/follower user IDs (with full paging; for any user)
- Viewer info for token/account verification

Depends on: anilist/auth.py, anilist/ratelimit.py
"""

import requests
from anilist.ratelimit import handle_rate_limit

ANILIST_API = "https://graphql.anilist.co"

def get_user_id(username):
    query = '''
    query ($name: String) {
        User(search: $name) { id }
    }
    '''
    variables = {'name': username}
    resp = requests.post(ANILIST_API, json={'query': query, 'variables': variables})
    if resp.status_code == 200:
        data = resp.json()
        uid = data.get('data', {}).get('User', {}).get('id')
        if uid:
            return uid
    raise Exception(f"Unable to find AniList user '{username}'.")

def get_viewer_info(token):
    """
    Returns dict { "id": ..., "username": ... } for authenticated user.
    """
    query = '''
    query { Viewer { id name } }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    resp = requests.post(ANILIST_API, json={"query": query}, headers=headers)
    if resp.status_code == 200:
        viewer = resp.json()["data"]["Viewer"]
        return {"id": viewer["id"], "username": viewer["name"]}
    return None

def fetch_activities(mode, token, user_id=None, page=1, per_page=30):
    # Fetches activities for global, following, profile, followers
    # Uses proper fragments
    if mode == "PROFILE":
        query = '''
        query ($page: Int, $perPage: Int, $userId: Int) {
          Page(page: $page, perPage: $perPage) {
            activities(
              sort: ID_DESC,
              userId: $userId
            ) {
              ... on ListActivity {
                id
                isLiked
                status
                media {
                  title { userPreferred }
                  type
                }
              }
              ... on TextActivity {
                id
                isLiked
                text
              }
              ... on MessageActivity {
                id
                isLiked
                message
              }
            }
          }
        }
        '''
        variables = {"page": page, "perPage": per_page, "userId": user_id}
    else:
        # GLOBAL, FOLLOWING, FOLLOWERS do not declare $userId
        query = '''
        query ($page: Int, $perPage: Int) {
          Page(page: $page, perPage: $perPage) {
            activities(
              sort: ID_DESC
            ) {
              ... on ListActivity {
                id
                isLiked
                status
                media {
                  title { userPreferred }
                  type
                }
              }
              ... on TextActivity {
                id
                isLiked
                text
              }
              ... on MessageActivity {
                id
                isLiked
                message
              }
            }
          }
        }
        '''
        variables = {"page": page, "perPage": per_page}

    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    resp = requests.post(ANILIST_API, json={'query': query, 'variables': variables}, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        page_data = data["data"]["Page"]
        acts = page_data["activities"]
        return acts
    else:
        handled = handle_rate_limit(resp)
        if handled:
            return []
        else:
            raise Exception(f"Failed to fetch activities (mode={mode}): HTTP {resp.status_code}\n{resp.text}")

def fetch_global_activities(token, page=1, per_page=30):
    return fetch_activities("GLOBAL", token, None, page=page, per_page=per_page)

def fetch_following_activities(token, page=1, per_page=30):
    return fetch_activities("FOLLOWING", token, None, page=page, per_page=per_page)

def fetch_profile_activities(token, user_id, page=1, per_page=30):
    return fetch_activities("PROFILE", token, user_id, page=page, per_page=per_page)

def like_activity(activity_id, token):
    mutation = '''
    mutation ($id: Int) {
      ToggleLikeV2(id: $id, type: ACTIVITY) {
        __typename
      }
    }
    '''
    variables = { "id": activity_id }
    headers = { "Authorization": f"Bearer {token}" }
    resp = requests.post(ANILIST_API, json={"query": mutation, "variables": variables}, headers=headers)
    if resp.status_code == 200:
        return True
    else:
        handled = handle_rate_limit(resp)
        if not handled:
            return False
        return True

# ========== PAGED FOLLOWERS/FOLLOWING QUERIES (for any user) ==========

def get_following_user_ids_paged(token, user_id):
    """
    Returns all user IDs the specified user is following (paged, like export.py).
    If user_id is None, gets Viewer info first.
    """
    if user_id is None:
        viewer = get_viewer_info(token)
        user_id = viewer["id"] if viewer else None
        if user_id is None:
            return []

    query = '''
    query ($userId: Int!, $page: Int!) {
        Page(page: $page, perPage: 50) {
            pageInfo { hasNextPage }
            following(userId: $userId) { id }
        }
    }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    ids = []
    page = 1
    while True:
        variables = { "userId": user_id, "page": page }
        resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
        if resp.status_code != 200:
            handled = handle_rate_limit(resp)
            if not handled:
                break
        else:
            data = resp.json()
            page_data = data["data"]["Page"]
            ids += [u["id"] for u in page_data.get("following", []) if "id" in u]
            if not page_data["pageInfo"]["hasNextPage"]:
                break
            page += 1
    return ids

def get_follower_user_ids_paged(token, user_id):
    """
    Returns all user IDs who follow the specified user (paged, like export.py).
    If user_id is None, gets Viewer info first.
    """
    if user_id is None:
        viewer = get_viewer_info(token)
        user_id = viewer["id"] if viewer else None
        if user_id is None:
            return []

    query = '''
    query ($userId: Int!, $page: Int!) {
        Page(page: $page, perPage: 50) {
            pageInfo { hasNextPage }
            followers(userId: $userId) { id }
        }
    }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    ids = []
    page = 1
    while True:
        variables = { "userId": user_id, "page": page }
        resp = requests.post(ANILIST_API, json={"query": query, "variables": variables}, headers=headers)
        if resp.status_code != 200:
            handled = handle_rate_limit(resp)
            if not handled:
                break
        else:
            data = resp.json()
            page_data = data["data"]["Page"]
            ids += [u["id"] for u in page_data.get("followers", []) if "id" in u]
            if not page_data["pageInfo"]["hasNextPage"]:
                break
            page += 1
    return ids

# Viewer-only legacy (not paged), kept for backward compatibility
def get_following_user_ids(token):
    viewer = get_viewer_info(token)
    return get_following_user_ids_paged(token, viewer["id"] if viewer else None)

def get_follower_user_ids(token):
    viewer = get_viewer_info(token)
    return get_follower_user_ids_paged(token, viewer["id"] if viewer else None)

def follow_user(user_id, token):
    mutation = '''
    mutation ($userId: Int) {
      FollowUser(userId: $userId) {
        id
        name
        isFollowing
      }
    }
    '''
    variables = { "userId": user_id }
    headers = { "Authorization": f"Bearer {token}" }
    resp = requests.post(ANILIST_API, json={"query": mutation, "variables": variables}, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("data", {}).get("FollowUser", {}).get("isFollowing", False)
    return False

def search_users(token, num_to_fetch=100):
    # This is a placeholder. AniList doesn't provide a public global user search, so you may want to use other heuristics.
    # Here, just fetch first N users from Page.
    query = '''
    query ($page: Int, $perPage: Int) {
      Page(page: $page, perPage: $perPage) {
        users {
          id
          name
        }
      }
    }
    '''
    users = []
    page = 1
    per_page = min(num_to_fetch, 50)
    headers = { "Authorization": f"Bearer {token}" }
    while len(users) < num_to_fetch:
        resp = requests.post(ANILIST_API, json={"query": query, "variables": {"page": page, "perPage": per_page}}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            page_users = data["data"]["Page"]["users"]
            if not page_users:
                break
            users.extend(page_users)
            if len(page_users) < per_page:
                break
            page += 1
        else:
            break
    return users[:num_to_fetch]