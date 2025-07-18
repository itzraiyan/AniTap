"""
anilist/ratelimit.py

Handles AniList API rate limiting and exponential backoff,
now with a yellow tqdm wait bar.
"""

import time
import sys

rate_limit_counter = {"count": 0}

def handle_rate_limit(resp):
    """
    Detects AniList API rate limits.
    If rate limited, shows a yellow tqdm bar and waits for Retry-After seconds.
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
        info(f"Rate limit hit #{hit_number}. Waiting {wait} seconds...", color="YELLOW")
        try:
            bar = tqdm(
                total=wait,
                desc=color_text(f"Rate limit cooldown", "YELLOW"),
                unit="sec",
                colour="yellow",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{remaining} left]"
            )
            for _ in range(wait):
                time.sleep(1)
                bar.update(1)
            bar.close()
        except KeyboardInterrupt:
            info("Interrupted during rate limit wait. Exiting...", color="RED")
            sys.exit(1)

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
        info("Rate limit wait over! Resuming your restoring process...", color="GREEN")
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
                    info("Rate limit wait over! Resuming your restoring process...", color="GREEN")
                    return True
    except Exception:
        pass
    return False