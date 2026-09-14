from datetime import datetime, timedelta, timezone

from tikdrop.ingestion.store import SignalStore
from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.score import DimensionScore, ProductScoreInput, ProductScoreResult
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import RawSignal, TrendInput


def test_build_trend_input_splits_recent_vs_prior_and_counts_sources():
    store = SignalStore(db_path=":memory:")
    now = datetime(2026, 9, 14, tzinfo=timezone.utc)

    store.save(
        "widget",
        [RawSignal(source="reddit", metric_value=50, engagement_proxy=0.8, raw_text="old post")],
        captured_at=now - timedelta(days=10),
    )
    store.save(
        "widget",
        [
            RawSignal(source="reddit", metric_value=80, engagement_proxy=0.9, raw_text="new post"),
            RawSignal(source="google_trends", metric_value=60, engagement_proxy=0.6, raw_text="trend"),
        ],
        captured_at=now - timedelta(days=1),
    )

    trend_input = store.build_trend_input("widget", now=now)

    assert trend_input.signal_count_7d == 2
    assert trend_input.signal_count_prior_7d == 1
    assert trend_input.distinct_sources == 2
    assert 0 < trend_input.avg_engagement_rate <= 1


def test_save_uses_per_signal_captured_at_when_set():
    store = SignalStore(db_path=":memory:")
    now = datetime(2026, 9, 14, tzinfo=timezone.utc)

    store.save(
        "widget",
        [
            RawSignal(source="google_trends", metric_value=10, engagement_proxy=0.1, captured_at=now - timedelta(days=30)),
            RawSignal(source="google_trends", metric_value=90, engagement_proxy=0.9, captured_at=now - timedelta(days=1)),
        ],
    )

    trend_input = store.build_trend_input("widget", now=now)

    # only the day-1 signal falls in the last 7 days, even though both were saved in one call
    assert trend_input.signal_count_7d == 1
    assert trend_input.signal_count_prior_7d == 0


def test_weeks_sustained_ignores_weeks_with_low_engagement():
    store = SignalStore(db_path=":memory:")
    now = datetime(2026, 9, 14, tzinfo=timezone.utc)

    store.save(
        "widget",
        [RawSignal(source="google_trends", metric_value=90, engagement_proxy=0.9, captured_at=now - timedelta(days=1))],
    )
    store.save(
        "widget",
        [RawSignal(source="google_trends", metric_value=5, engagement_proxy=0.05, captured_at=now - timedelta(days=60))],
    )

    trend_input = store.build_trend_input("widget", now=now)

    # the low-engagement week (0.05) doesn't count as "sustained", only the strong one does
    assert trend_input.weeks_sustained == 1


def test_build_trend_input_with_no_history_is_all_zero():
    store = SignalStore(db_path=":memory:")

    trend_input = store.build_trend_input("never-seen-before")

    assert trend_input.signal_count_7d == 0
    assert trend_input.signal_count_prior_7d == 0
    assert trend_input.distinct_sources == 0
    assert trend_input.weeks_sustained == 0


def test_save_score_result_upserts_and_maps_recommendation_to_status():
    store = SignalStore(db_path=":memory:")
    result = ProductScoreResult(
        product_name="widget",
        dimensions={"trend": DimensionScore(raw_score=8, weight=0.2, weighted_contribution=1.6)},
        total_score=7.5,
        recommendation="test",
        recommendation_reason="looks good",
    )

    store.save_score_result("widget", result)
    opportunities = store.list_opportunities()

    assert len(opportunities) == 1
    assert opportunities[0]["status"] == "queued_for_store"
    assert opportunities[0]["total_score"] == 7.5

    # a re-score updates the same row instead of duplicating it
    result.total_score = 8.2
    store.save_score_result("widget", result)
    assert len(store.list_opportunities()) == 1
    assert store.list_opportunities()[0]["total_score"] == 8.2


def test_get_opportunity_detail_roundtrips_the_full_result():
    store = SignalStore(db_path=":memory:")
    result = ProductScoreResult(
        product_name="widget",
        dimensions={"trend": DimensionScore(raw_score=8, weight=0.2, weighted_contribution=1.6)},
        total_score=7.5,
        recommendation="test",
        recommendation_reason="looks good",
    )
    store.save_score_result("widget", result)

    detail = store.get_opportunity_detail("widget")

    assert detail is not None
    assert detail.dimensions["trend"].raw_score == 8
    assert detail.recommendation_reason == "looks good"
    assert store.get_opportunity_detail("never-scored") is None


def test_get_candidate_input_roundtrips_and_defaults_to_none():
    store = SignalStore(db_path=":memory:")
    assert store.get_candidate_input("widget") is None

    product_input = ProductScoreInput(
        product_name="widget",
        trend=TrendInput(signal_count_7d=1, signal_count_prior_7d=0, avg_engagement_rate=0.5, distinct_sources=1, weeks_sustained=1),
        portugal_opportunity=PortugalOpportunityInput(pt_competitor_count=3, differentiation_score=6.0),
        costs=CostInputs(sale_price=20, product_cost=5, shipping_cost=3, payment_fees=1, ad_cost_per_unit=4, returns_cost_estimate=1),
        supplier=SupplierInput(),
        creative=CreativeInput(demo_video_feasibility=7, ugc_potential=6),
        logistics=LogisticsInput(weight_grams=200, avg_shipping_days=7),
        risk_compliance=RiskComplianceInput(),
    )
    result = ProductScoreResult(
        product_name="widget",
        dimensions={"trend": DimensionScore(raw_score=8, weight=0.2, weighted_contribution=1.6)},
        total_score=7.5,
        recommendation="test",
        recommendation_reason="looks good",
    )

    store.save_score_result("widget", result, product_input=product_input)

    loaded = store.get_candidate_input("widget")
    assert loaded is not None
    assert loaded.costs.sale_price == 20
    assert loaded.portugal_opportunity.pt_competitor_count == 3
