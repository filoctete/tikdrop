"""Google Trends connector: free, no API key, no login required. Uses the unofficial pytrends
library. Install with: pip install -e ".[ingestion]"

Pulls the full 3-month interest-over-time series in one call (not just the latest value) and
backfills it into the SignalStore, so a single run already has enough history to tell a
sustained trend from a one-day spike - no need to run this daily for weeks first.
"""

from datetime import timezone
from typing import List

from tikdrop.schemas.trend import RawSignal


def fetch_google_trends_signal(keyword: str, geo: str = "PT") -> List[RawSignal]:
    try:
        from pytrends.request import TrendReq
    except ImportError as exc:  # pragma: no cover
        raise ImportError('Needs pytrends. Install with: pip install -e ".[ingestion]"') from exc

    pytrends = TrendReq(hl="pt-PT", tz=0)
    pytrends.build_payload([keyword], timeframe="today 3-m", geo=geo)
    df = pytrends.interest_over_time()

    if df.empty:
        return []

    signals = []
    for date, row in df.iterrows():
        interest = float(row[keyword])
        if interest <= 0:
            continue  # skip noise - only keep days with actual measured interest

        captured_at = date.to_pydatetime()
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)

        signals.append(
            RawSignal(
                source="google_trends",
                metric_value=interest,
                engagement_proxy=interest / 100.0,
                raw_text=f"Google Trends interest for '{keyword}' in {geo} on {date.date()}: {interest:.0f}/100",
                url=f"https://trends.google.com/trends/explore?geo={geo}&q={keyword}",
                captured_at=captured_at,
            )
        )
    return signals
