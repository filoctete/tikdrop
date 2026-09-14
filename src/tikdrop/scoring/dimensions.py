"""One deterministic 0-10 scorer per Product Score dimension (idea.pdf Anexo B /
development_guide.pdf section 7). Kept as pure functions so each dimension stays
independently testable and explainable.
"""

from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import TrendInput


def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def score_trend(inp: TrendInput) -> float:
    growth = (inp.signal_count_7d - inp.signal_count_prior_7d) / max(inp.signal_count_prior_7d, 1)
    growth_component = _clamp((growth / 1.5) * 10)

    engagement_component = _clamp((inp.avg_engagement_rate / 0.15) * 10)

    breadth_component = _clamp((inp.distinct_sources / 4) * 10)

    # rewards sustained presence over a few viral days, per idea.pdf's "está realmente a
    # crescer ou é apenas viral durante alguns dias?"
    sustain_component = _clamp((inp.weeks_sustained / 4) * 10)

    return _clamp((growth_component + engagement_component + breadth_component + sustain_component) / 4)


def score_portugal_opportunity(inp: PortugalOpportunityInput) -> float:
    saturation_component = _clamp(10 - min(inp.pt_competitor_count, 10))

    price_component = 5.0  # neutral default when we don't have both prices yet
    if inp.competitor_price_avg is not None and inp.our_target_price is not None and inp.competitor_price_avg > 0:
        price_ratio = inp.our_target_price / inp.competitor_price_avg
        price_component = _clamp(10 - max(price_ratio - 1, 0) * 20)

    return _clamp(0.5 * saturation_component + 0.3 * inp.differentiation_score + 0.2 * price_component)


def score_margin(net_contribution_pct: float) -> float:
    # 0% net contribution -> 0, 60%+ -> 10, linear in between
    return _clamp((net_contribution_pct / 0.6) * 10)


def score_supplier(inp: SupplierInput) -> float:
    flags = [
        inp.identity_verified,
        inp.vat_validated,
        inp.eu_warehouse,
        inp.dropshipping_confirmed,
        inp.neutral_packaging_possible,
        inp.tracking_available,
        inp.returns_policy_clear,
        inp.integration_available,
        inp.test_order_completed,
        inp.backup_supplier_identified,
    ]
    return _clamp((sum(flags) / len(flags)) * 10)


def score_creative(inp: CreativeInput) -> float:
    return _clamp((inp.demo_video_feasibility + inp.ugc_potential) / 2)


def score_logistics(inp: LogisticsInput) -> float:
    if inp.weight_grams <= 200:
        weight_component = 10.0
    elif inp.weight_grams <= 500:
        weight_component = 8.0
    elif inp.weight_grams <= 1000:
        weight_component = 6.0
    elif inp.weight_grams <= 2000:
        weight_component = 4.0
    else:
        weight_component = 2.0

    if inp.avg_shipping_days <= 7:
        shipping_component = 10.0
    elif inp.avg_shipping_days <= 14:
        shipping_component = 7.0
    elif inp.avg_shipping_days <= 21:
        shipping_component = 4.0
    else:
        shipping_component = 1.0

    size_component = {"small": 10.0, "medium": 6.0, "large": 2.0}[inp.size_category]

    score = (weight_component + shipping_component + size_component) / 3
    if inp.fragile:
        score -= 3
    return _clamp(score)


def score_risk_compliance(inp: RiskComplianceInput) -> float:
    base = {"low": 10.0, "medium": 5.0, "high": 1.0}[inp.category_risk_level]
    if inp.requires_technical_documentation:
        base -= 2
    if inp.is_regulated_category:
        base -= 4
    return _clamp(base)
