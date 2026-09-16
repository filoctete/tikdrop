from tikdrop.schemas.trend import TrendInput
from tikdrop.scoring.quick_input import build_quick_score_input


def _trend(**overrides):
    defaults = dict(signal_count_7d=0, signal_count_prior_7d=0, avg_engagement_rate=0.0, distinct_sources=0, weeks_sustained=0)
    defaults.update(overrides)
    return TrendInput(**defaults)


def test_build_quick_score_input_uses_placeholders_for_unknown_market_data():
    result = build_quick_score_input(
        name="wooden wireless mouse",
        trend_input=_trend(),
        product_cost=9.50,
        sale_price=24.99,
        weight_grams=120,
    )

    assert result.portugal_opportunity.pt_competitor_count == 5
    assert result.portugal_opportunity.differentiation_score == 5.0
    assert result.costs.product_cost == 9.50
    assert result.costs.ad_cost_per_unit == 24.99 * 0.25


def test_build_quick_score_input_applies_compliance_keyword_matching():
    result = build_quick_score_input(
        name="whey protein powder",
        trend_input=_trend(),
        product_cost=10.0,
        sale_price=20.0,
        weight_grams=500,
    )

    assert result.risk_compliance.category_risk_level == "high"


def test_build_quick_score_input_defaults_creative_to_neutral():
    result = build_quick_score_input(
        name="widget",
        trend_input=_trend(),
        product_cost=5.0,
        sale_price=15.0,
        weight_grams=100,
    )

    assert result.creative.demo_video_feasibility == 5.0
    assert result.creative.ugc_potential == 5.0


def test_build_quick_score_input_passes_through_listing_url():
    result = build_quick_score_input(
        name="widget",
        trend_input=_trend(),
        product_cost=5.0,
        sale_price=15.0,
        weight_grams=100,
        listing_url="https://www.aliexpress.com/item/12345.html",
    )

    assert result.supplier.listing_url == "https://www.aliexpress.com/item/12345.html"


def test_build_quick_score_input_defaults_listing_url_to_none():
    result = build_quick_score_input(
        name="widget", trend_input=_trend(), product_cost=5.0, sale_price=15.0, weight_grams=100
    )

    assert result.supplier.listing_url is None
