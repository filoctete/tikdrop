"""Automated candidate discovery. There is no free, legal API that hands over "what's viral on
TikTok right now" (checked extensively - see conversation history / commit log), but Google
Trends' "rising related queries" endpoint (still working, unlike its old "trending searches"
endpoint) gives a genuine, free, legal signal: seed a handful of broad product categories, see
what specific queries are rising under each, then verify each one against real worldwide search
history before trusting it.

This deliberately does NOT auto-score or auto-publish anything. It only surfaces candidates with
real trend evidence and ready-to-click sourcing-research links - a human still has to find the
real supplier cost and enter it (idea.pdf/development_guide.pdf are both explicit that margin,
PT competition and supplier reliability can never be assumed away).
"""

from typing import List
from urllib.parse import quote_plus

from tikdrop.ingestion.google_trends import fetch_google_trends_signal
from tikdrop.ingestion.store import SignalStore

# Broad, generic dropshipping-relevant categories - not products themselves. Kept short so an
# hourly run stays fast and doesn't hammer pytrends' unofficial endpoint.
SEED_TERMS = [
    "gadget",
    "kitchen gadget",
    "phone accessory",
    "pet product",
    "beauty tool",
    "car accessory",
]

# A rising query only gets checked against real Trends history if it looks like a plausible
# product name (2-5 words) - filters out both single generic seed echoes and long noisy
# long-tail junk queries pytrends sometimes returns.
_MIN_QUERY_WORDS = 2
_MAX_QUERY_WORDS = 5

# Minimum real evidence before a candidate is worth a human's time: enough days with measurable
# interest and enough distinct weeks (not just one viral burst) - same bar that turned up
# "heated gloves" as our strongest candidate yet.
_MIN_TREND_DAYS = 15
_MIN_WEEKS_SUSTAINED = 3

_MAX_CANDIDATES_CHECKED_PER_RUN = 15


def research_links(candidate_key: str) -> List[dict]:
    q = quote_plus(candidate_key)
    return [
        {"label": "AliExpress", "url": f"https://www.aliexpress.com/wholesale?SearchText={q}"},
        {"label": "Google Shopping", "url": f"https://www.google.com/search?q={q}&tbm=shop"},
        {"label": "Spocket search", "url": f"https://www.spocket.co/search?query={q}"},
    ]


def _rising_queries_for_seed(seed: str) -> List[str]:
    from pytrends.request import TrendReq

    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload([seed], timeframe="today 1-m", geo="")
    related = pytrends.related_queries()
    rising = (related or {}).get(seed, {}).get("rising")
    if rising is None:
        return []

    queries = []
    for query in rising["query"].tolist():
        word_count = len(query.split())
        if _MIN_QUERY_WORDS <= word_count <= _MAX_QUERY_WORDS:
            queries.append(query)
    return queries


def discover_candidates(store: SignalStore) -> List[str]:
    """Runs one discovery pass. Returns the candidate_keys newly added (status=needs_input)."""
    candidate_queries: List[str] = []
    for seed in SEED_TERMS:
        try:
            candidate_queries.extend(_rising_queries_for_seed(seed))
        except Exception:
            continue

    newly_discovered = []
    checked = 0
    for query in candidate_queries:
        if checked >= _MAX_CANDIDATES_CHECKED_PER_RUN:
            break
        if store.is_known_candidate(query):
            continue
        checked += 1

        try:
            signals = fetch_google_trends_signal(query, geo="")
        except Exception:
            continue
        if len(signals) < _MIN_TREND_DAYS:
            continue

        store.save(query, signals)
        trend_input = store.build_trend_input(query)
        if trend_input.weeks_sustained < _MIN_WEEKS_SUSTAINED:
            continue

        store.save_discovered_candidate(
            query,
            trend_days=len(signals),
            weeks_sustained=trend_input.weeks_sustained,
            research_links=research_links(query),
        )
        newly_discovered.append(query)

    return newly_discovered
