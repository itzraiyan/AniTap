"""
anilist/api.py

Handles all AniList GraphQL API queries and mutations:
- User lookup
- Fetching activities (global/following/profile) with proper fragments
- Liking activities
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
    query = '''
    query { Viewer { id name } }
    '''
    headers = { "Authorization": f"Bearer {token}" }
    resp = requests.post(ANILIST_API, json={"query": query}, headers=headers)
    if resp.status_code == 200:
        viewer = resp.json()["data"]["Viewer"]
        return {"id": viewer["id"], "username": viewer["name"]}
    return None

# --------- Activities Fetch (FIXED) ---------
def fetch_activities(mode, token, user_id=None, page=1, per_page=25):
    """
    Fetches activities (global/following/profile)
    mode: "GLOBAL", "FOLLOWING", "PROFILE"
    user_id: required for PROFILE
    """
    # Select the correct query and variables based on mode
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
        # GLOBAL and FOLLOWING do not declare $userId
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

    activities = []
    while True:
        resp = requests.post(ANILIST_API, json={'query': query, 'variables': variables}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            page_data = data["data"]["Page"]
            acts = page_data["activities"]
            activities.extend(acts)
            # Pagination: check if more pages
            # (If you want to support pagination, you should check pageInfo.hasNextPage, but most clients just grab the first page)
            break
        else:
            handled = handle_rate_limit(resp)
            if handled:
                continue
            else:
                raise Exception(f"Failed to fetch activities (mode={mode}): HTTP {resp.status_code}\n{resp.text}")
    return activities

def fetch_global_activities(token):
    # Uses GLOBAL mode, no userId
    return fetch_activities("GLOBAL", token, None)

def fetch_following_activities(token):
    # Uses FOLLOWING mode, no userId
    return fetch_activities("FOLLOWING", token, None)

def fetch_profile_activities(token, user_id):
    return fetch_activities("PROFILE", token, user_id)

def like_activity(activity_id, token):
    """
    Likes a single activity.
    """
    mutation = '''
    mutation ($id: Int) {
      ToggleLikeV2(id: $id, type: ACTIVITY) {
        __typename
      }
    }
    '''
    variables = { "id": activity_id }
    headers = { "Authorization": f"Bearer {token}" }
    while True:
        resp = requests.post(ANILIST_API, json={"query": mutation, "variables": variables}, headers=headers)
        if resp.status_code == 200:
            return True
        else:
            handled = handle_rate_limit(resp)
            if not handled:
                return False
