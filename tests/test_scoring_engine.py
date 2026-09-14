import pytest

from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.score import ProductScoreInput
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import TrendInput
from tikdrop.scoring.engine import WEIGHTS, ProductScoringEngine


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def _base_input(**overrides) -> ProductScoreInput:
    defaults = dict(
        product_name="Test product",
        trend=TrendInput(
            signal_count_7d=200,
            signal_count_prior_7d=100,
            avg_engagement_rate=0.12,
            distinct_sources=3,
            weeks_sustained=3,
        ),
        portugal_opportunity=PortugalOpportunityInput(
            pt_competitor_count=1,
            competitor_price_avg=20.0,
            our_target_price=19.0,
            differentiation_score=8.0,
        ),
        costs=CostInputs(
            sale_price=25.0,
            product_cost=5.0,
            shipping_cost=3.0,
            payment_fees=1.0,
            ad_cost_per_unit=5.0,
            returns_cost_estimate=1.0,
            other_costs=1.0,
        ),
        supplier=SupplierInput(
            identity_verified=True,
            vat_validated=True,
            eu_warehouse=True,
            dropshipping_confirmed=True,
            neutral_packaging_possible=True,
            tracking_available=True,
            returns_policy_clear=True,
            integration_available=True,
            test_order_completed=True,
            backup_supplier_identified=False,
        ),
        creative=CreativeInput(demo_video_feasibility=8.0, ugc_potential=7.0),
        logistics=LogisticsInput(weight_grams=150, fragile=False, avg_shipping_days=6, size_category="small"),
        risk_compliance=RiskComplianceInput(category_risk_level="low"),
    )
    defaults.update(overrides)
    return ProductScoreInput(**defaults)


def test_strong_candidate_is_recommended_for_test():
    result = ProductScoringEngine.score(_base_input())

    assert result.total_score >= 7.0
    assert result.recommendation == "test"
    assert set(result.dimensions) == set(WEIGHTS)


def test_saturated_market_without_differentiation_is_rejected_even_with_good_total():
    inp = _base_input(
        portugal_opportunity=PortugalOpportunityInput(
            pt_competitor_count=9,
            differentiation_score=1.0,
        )
    )

    result = ProductScoringEngine.score(inp)

    assert result.recommendation == "reject"
    assert "saturated" in result.recommendation_reason.lower()


def test_negative_margin_forces_reject():
    inp = _base_input(
        costs=CostInputs(
            sale_price=10.0,
            product_cost=6.0,
            shipping_cost=3.0,
            payment_fees=1.0,
            ad_cost_per_unit=3.0,
            returns_cost_estimate=1.0,
        )
    )

    result = ProductScoringEngine.score(inp)

    assert result.recommendation == "reject"
    assert "margin" in result.recommendation_reason.lower()
