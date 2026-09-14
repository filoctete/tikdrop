"""Reddit connector using Reddit's official OAuth API (free, read-only, app-only auth via the
client_credentials grant - no user login needed). Reddit blocks the old unauthenticated
www.reddit.com/*.json endpoints for most callers now, so this is the reliable free option.

Setup:
  1. Create a free "script" app at https://www.reddit.com/prefs/apps
  2. Set as environment variables (never hardcode/commit them):
       REDDIT_CLIENT_ID=...
       REDDIT_CLIENT_SECRET=...
"""

import os
from typing import List, Optional

import httpx

from tikdrop.schemas.trend import RawSignal

_USER_AGENT = "tikdrop-trend-hunter/0.1 (personal product research)"
_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_SEARCH_URL = "https://oauth.reddit.com/search"


class RedditConnectorError(RuntimeError):
    """Raised when Reddit credentials are missing or the API call fails."""


def _get_access_token(client_id: str, client_secret: str) -> str:
    response = httpx.post(
        _TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers={"User-Agent": _USER_AGENT},
        timeout=15.0,
    )
    if response.status_code != 200:
        raise RedditConnectorError(f"Reddit auth failed {response.status_code}: {response.text}")
    return response.json()["access_token"]


def fetch_reddit_signals(
    keyword: str,
    limit: int = 15,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> List[RawSignal]:
    client_id = client_id or os.environ.get("REDDIT_CLIENT_ID")
    client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RedditConnectorError(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are not set. Create a free 'script' app at "
            "https://www.reddit.com/prefs/apps and set both as environment variables."
        )

    token = _get_access_token(client_id, client_secret)
    response = httpx.get(
        _SEARCH_URL,
        params={"q": keyword, "sort": "relevance", "t": "week", "limit": limit},
        headers={"Authorization": f"Bearer {token}", "User-Agent": _USER_AGENT},
        timeout=15.0,
    )
    response.raise_for_status()
    posts = response.json()["data"]["children"]

    signals = []
    for post in posts:
        data = post["data"]
        signals.append(
            RawSignal(
                source="reddit",
                metric_value=float(data.get("score", 0) + data.get("num_comments", 0)),
                engagement_proxy=float(data.get("upvote_ratio") or 0.5),
                raw_text=data.get("title", ""),
                url=f"https://reddit.com{data.get('permalink', '')}",
            )
        )
    return signals
