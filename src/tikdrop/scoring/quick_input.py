"""Builds a ProductScoreInput from a lightly-researched candidate (e.g. pulled from a supplier
platform's public "trending products" page) plus a real TrendInput. PT competition,
differentiation and supplier reliability are NOT knowable from a supplier listing alone, so
they're filled with explicit neutral placeholders - callers should treat any resulting
"test"/"watch" recommendation as provisional until those are replaced with real research.
"""

from tikdrop.compliance import suggest_risk_compliance
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.score import ProductScoreInput
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import TrendInput

# Neutral until a human actually checks PT competition (idea.pdf: this is the one dimension
# that must never be assumed away - the scoring engine's saturation override still kicks in if
# real numbers turn out worse than this).
_PLACEHOLDER_PT_COMPETITOR_COUNT = 5
_PLACEHOLDER_DIFFERENTIATION_SCORE = 5.0
_DEFAULT_AD_COST_RATIO = 0.25  # rough CAC-to-price assumption until real ad data exists


def build_quick_score_input(
    name: str,
    trend_input: TrendInput,
    product_cost: float,
    sale_price: float,
    weight_grams: float,
    demo_video_feasibility: float = 5.0,
    ugc_potential: float = 5.0,
    avg_shipping_days: float = 10.0,
) -> ProductScoreInput:
    return ProductScoreInput(
        product_name=name,
        trend=trend_input,
        portugal_opportunity=PortugalOpportunityInput(
            pt_competitor_count=_PLACEHOLDER_PT_COMPETITOR_COUNT,
            differentiation_score=_PLACEHOLDER_DIFFERENTIATION_SCORE,
        ),
        costs=CostInputs(
            sale_price=sale_price,
            product_cost=product_cost,
            shipping_cost=3.0,
            payment_fees=1.0,
            ad_cost_per_unit=sale_price * _DEFAULT_AD_COST_RATIO,
            returns_cost_estimate=1.0,
        ),
        supplier=SupplierInput(
            identity_verified=True,
            dropshipping_confirmed=True,
            neutral_packaging_possible=True,
            tracking_available=True,
            returns_policy_clear=True,
        ),
        creative=CreativeInput(demo_video_feasibility=demo_video_feasibility, ugc_potential=ugc_potential),
        logistics=LogisticsInput(weight_grams=weight_grams, avg_shipping_days=avg_shipping_days, size_category="small"),
        risk_compliance=suggest_risk_compliance(name),
    )
