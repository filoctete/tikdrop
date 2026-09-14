"""End-to-end example: researched-by-hand inputs (trend, PT market, costs, supplier, logistics,
compliance) plus one AI-suggested field (Creative), fed into the deterministic
ProductScoringEngine. Needs GROQ_API_KEY (see examples/groq_ai_demo.py for setup).

Run with: python examples/ai_assisted_scoring.py
"""

import os

from _env import load_dotenv_if_present

load_dotenv_if_present()

from tikdrop.ai.groq_provider import AIProviderError, GroqAIProvider
from tikdrop.ai.suggestions import suggest_creative_input
from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.score import ProductScoreInput
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import TrendInput
from tikdrop.scoring.engine import ProductScoringEngine

PRODUCT_DESCRIPTION = (
    "Reusable, self-cleaning silicone roller that removes pet hair from clothes, sofas and car "
    "seats without needing lint sheets."
)


def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("Set GROQ_API_KEY first (free key at https://console.groq.com/keys).")
        return

    with GroqAIProvider() as ai:
        try:
            creative = suggest_creative_input(ai, PRODUCT_DESCRIPTION)
        except AIProviderError as exc:
            print(f"AI suggestion failed, falling back to manual review: {exc}")
            return

    print(f"AI-suggested creative input: {creative}\n(review this before trusting it)\n")

    product_input = ProductScoreInput(
        product_name="Reusable self-cleaning pet hair roller",
        trend=TrendInput(
            signal_count_7d=180,
            signal_count_prior_7d=120,
            avg_engagement_rate=0.10,
            distinct_sources=3,
            weeks_sustained=3,
        ),
        portugal_opportunity=PortugalOpportunityInput(
            pt_competitor_count=8,
            competitor_price_avg=14.0,
            our_target_price=14.5,
            differentiation_score=2.0,
        ),
        costs=CostInputs(
            sale_price=17.99,
            product_cost=3.5,
            shipping_cost=2.5,
            payment_fees=0.6,
            ad_cost_per_unit=4.0,
            returns_cost_estimate=0.8,
            other_costs=0.5,
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
            test_order_completed=False,
            backup_supplier_identified=False,
        ),
        creative=creative,
        logistics=LogisticsInput(weight_grams=120, fragile=False, avg_shipping_days=8, size_category="small"),
        risk_compliance=RiskComplianceInput(category_risk_level="low"),
    )

    result = ProductScoringEngine.score(product_input)

    print(f"Total score: {result.total_score:.2f}/10")
    print(f"Recommendation: {result.recommendation} ({result.recommendation_reason})")
    print("Breakdown:")
    for name, d in result.dimensions.items():
        print(f"  {name:20s} raw={d.raw_score:5.2f}  weight={d.weight:.2f}  contribution={d.weighted_contribution:.2f}")


if __name__ == "__main__":
    main()
