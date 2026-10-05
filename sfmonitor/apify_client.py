"""Instagram post fetching via Apify's hosted instagram-scraper actor.

See README.md for how to create an Apify account and API token. We use
Apify rather than a DIY scraper because Instagram has no public API for
reading someone else's profile and aggressively blocks headless scraping.
"""
import os
import time
from dataclasses import dataclass
from typing import List, Optional

import impit
from apify_client import ApifyClient

TOKEN_ENV_VAR = "APIFY_API_TOKEN"
ACTOR_ID = "apify/instagram-scraper"

RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY_SECONDS = 2


class ApifyConfigError(RuntimeError):
    """Raised when the Apify API token isn't configured."""


@dataclass
class RawPost:
    post_id: str
    url: str
    caption: str
    timestamp: Optional[str]
    likes_count: Optional[int]
    comments_count: Optional[int]


def get_client() -> ApifyClient:
    token = os.environ.get(TOKEN_ENV_VAR)
    if not token:
        raise ApifyConfigError(
            f"Set {TOKEN_ENV_VAR} to your Apify API token (see README.md for setup steps)."
        )
    return ApifyClient(token)


def _with_retry(fn, *args, **kwargs):
    """A transient network blip (DNS hiccup, connection reset) during the
    Apify call previously crashed the whole run with no retry at all --
    every Google Sheets call already got this treatment after repeated
    real crashes, but the Apify fetch itself never did until one hit the
    exact same class of failure. impit.HTTPError is the base class for
    apify-client's underlying transport errors (connect/timeout/etc).
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except impit.HTTPError:
            if attempt == RETRY_ATTEMPTS:
                raise
            time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)


def fetch_posts(profile_url: str, limit: int, client: Optional[ApifyClient] = None) -> List[RawPost]:
    """Fetch the most recent posts from a public Instagram profile."""
    client = client or get_client()
    run_input = {
        "directUrls": [profile_url],
        "resultsType": "posts",
        "resultsLimit": limit,
    }
    run = _with_retry(client.actor(ACTOR_ID).call, run_input=run_input)
    posts = []
    for item in _with_retry(lambda: list(client.dataset(run.default_dataset_id).iterate_items())):
        posts.append(
            RawPost(
                post_id=item["id"],
                url=item.get("url", ""),
                caption=item.get("caption") or "",
                timestamp=item.get("timestamp"),
                likes_count=item.get("likesCount"),
                comments_count=item.get("commentsCount"),
            )
        )
    return posts
