import pandas as pd
import pytest

from tikdrop.discovery import _looks_like_a_specific_product, discover_candidates, research_links
from tikdrop.ingestion.store import SignalStore
from tikdrop.schemas.trend import RawSignal


def test_research_links_are_well_formed_urls():
    links = research_links("heated gloves")

    labels = {l["label"] for l in links}
    assert "AliExpress" in labels
    assert all(l["url"].startswith("https://") for l in links)
    assert all("heated+gloves" in l["url"] or "heated%20gloves" in l["url"] for l in links)


@pytest.mark.parametrize(
    "query",
    [
        "best kitchen gadgets",  # listicle word "best"
        "kitchen gadgets 2026",  # contains a year
        "kitchen gadget set",  # "set" = a bundle, not one product
        "top gift ideas",  # multiple listicle words
        "kitchen gadgets",  # just the plural of the seed category itself
    ],
)
def test_rejects_listicle_and_category_style_queries(query):
    assert _looks_like_a_specific_product(query, seed="kitchen gadget") is False


def test_accepts_a_plausible_specific_product_name():
    assert _looks_like_a_specific_product("heated gloves", seed="gadget") is True
    assert _looks_like_a_specific_product("touchless soap dispenser", seed="gadget") is True


def _fake_signals(n_days: int):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    return [
        RawSignal(source="google_trends", metric_value=50, engagement_proxy=0.5, captured_at=now - timedelta(days=i))
        for i in range(n_days)
    ]


def test_discover_candidates_skips_seeds_and_short_or_long_queries(monkeypatch):
    store = SignalStore(db_path=":memory:")

    class FakePytrends:
        def __init__(self, *args, **kwargs):
            pass

        def build_payload(self, *args, **kwargs):
            pass

        def related_queries(self):
            return {
                "gadget": {
                    "rising": pd.DataFrame(
                        {
                            "query": [
                                "gadget",  # too short (1 word) - skipped
                                "a b c d e f g h",  # too long - skipped
                                "cool kitchen gadget",  # 3 words - kept
                            ],
                            "value": [1000, 500, 300],
                        }
                    )
                }
            }

    monkeypatch.setattr("pytrends.request.TrendReq", FakePytrends)
    monkeypatch.setattr("tikdrop.discovery.SEED_TERMS", ["gadget"])
    monkeypatch.setattr("tikdrop.discovery.fetch_google_trends_signal", lambda q, geo="": _fake_signals(20))

    discovered = discover_candidates(store)

    assert discovered == ["cool kitchen gadget"]
    candidates = store.list_discovered_candidates()
    assert candidates[0]["candidate_key"] == "cool kitchen gadget"
    assert candidates[0]["trend_days"] == 20


def test_discover_candidates_skips_weak_trend_signal(monkeypatch):
    store = SignalStore(db_path=":memory:")

    class FakePytrends:
        def __init__(self, *args, **kwargs):
            pass

        def build_payload(self, *args, **kwargs):
            pass

        def related_queries(self):
            return {"gadget": {"rising": pd.DataFrame({"query": ["weak signal gadget"], "value": [100]})}}

    monkeypatch.setattr("pytrends.request.TrendReq", FakePytrends)
    monkeypatch.setattr("tikdrop.discovery.SEED_TERMS", ["gadget"])
    # only 5 days of signal - below the _MIN_TREND_DAYS bar
    monkeypatch.setattr("tikdrop.discovery.fetch_google_trends_signal", lambda q, geo="": _fake_signals(5))

    discovered = discover_candidates(store)

    assert discovered == []
    assert store.list_discovered_candidates() == []


def test_discover_candidates_skips_already_known_candidates(monkeypatch):
    store = SignalStore(db_path=":memory:")
    store.save_discovered_candidate("cool kitchen gadget", trend_days=20, weeks_sustained=4, research_links=[])

    class FakePytrends:
        def __init__(self, *args, **kwargs):
            pass

        def build_payload(self, *args, **kwargs):
            pass

        def related_queries(self):
            return {"gadget": {"rising": pd.DataFrame({"query": ["cool kitchen gadget"], "value": [300]})}}

    monkeypatch.setattr("pytrends.request.TrendReq", FakePytrends)
    monkeypatch.setattr("tikdrop.discovery.SEED_TERMS", ["gadget"])
    calls = []
    monkeypatch.setattr(
        "tikdrop.discovery.fetch_google_trends_signal",
        lambda q, geo="": (calls.append(q), _fake_signals(20))[1],
    )

    discovered = discover_candidates(store)

    assert discovered == []
    assert calls == []  # never even re-checked - already known
