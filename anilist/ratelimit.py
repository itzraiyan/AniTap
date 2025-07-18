"""
anilist/ratelimit.py

Handles AniList API rate limiting and exponential backoff,
with a yellow tqdm wait bar that appears in the progress bar's place.
"""

import time
import sys

rate_limit_counter = {"count": 0}

def handle_rate_limit(resp, main_bar=None):
    """
    Detects AniList API rate limits.
    If rate limited, shows a yellow tqdm bar and waits for Retry-After seconds.
    Closes main_bar if provided.
    Returns True if handled (should retry), or False if not a rate limit.
    """
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False

    try:
        from ui.colors import color_text
    except ImportError:
        def color_text(text, color): return text

    def info(msg, color=None):
        if color:
            msg = color_text(msg, color)
        if use_tqdm:
            tqdm.write(msg)
        else:
            print(msg)

    def tqdm_wait(wait, hit_number):
        if main_bar:
            main_bar.close()
        info(f"Rate limit hit #{hit_number}. Waiting {wait} seconds...", color="YELLOW")
        bar = tqdm(
            total=wait,
            desc=color_text("Rate limit cooldown", "YELLOW"),
            unit="sec",
            colour="yellow",
            bar_format="{desc}: {bar}| {n_fmt}/{total_fmt} [{remaining}s left]"
        )
        for _ in range(wait):
            time.sleep(1)
            bar.update(1)
        bar.close()
        info("Rate limit wait over! Resuming...", color="GREEN")

    # AniList returns 429 for rate limit
    if resp.status_code == 429:
        rate_limit_counter["count"] += 1
        hit_number = rate_limit_counter["count"]
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                wait = int(float(retry_after))
            except Exception:
                wait = 15
        else:
            wait = 15
        tqdm_wait(wait, hit_number)
        return True

    # Sometimes 400 with rate limit error in body
    try:
        data = resp.json()
        if "errors" in data:
            for err in data["errors"]:
                if "rate limit" in err.get("message", "").lower():
                    rate_limit_counter["count"] += 1
                    hit_number = rate_limit_counter["count"]
                    wait = 15
                    tqdm_wait(wait, hit_number)
                    return True
    except Exception:
        pass
    return False