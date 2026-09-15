"""First real (legal, free) slice of the Trend Hunter: pulls actual signals for a keyword,
following idea.pdf's core thesis - find it trending ABROAD first, then check if PT still has
room. The Trend dimension is driven by worldwide Google Trends interest (3 months of history in
one call); PT-only interest is checked separately just as a heads-up ("is this already known
here?"), since PT search volume alone is usually too thin to say much on its own. Then walks
you through the parts that still have no automated source (PT competition, costs, supplier -
including whether it has an EU warehouse/fulfilment, logistics, compliance) and scores the
candidate. If the recommendation is "test", it's saved to the local opportunities queue
(status=queued_for_store) - our stand-in for "enters the store" until a real Store Generator /
e-commerce integration exists.

Reddit is wired in (src/tikdrop/ingestion/reddit.py) but only runs if REDDIT_CLIENT_ID and
REDDIT_CLIENT_SECRET are set (Reddit currently requires a separate API-access approval before
even creating an app, so this stays opt-in for now). TikTok and Instagram are deliberately not
included at all: there is no free, ToS-compliant way to pull trend data from them.

Install: pip install -e ".[ingestion]"
Run: python examples/discover.py "pet hair roller"
"""

import os
import sys
from urllib.parse import quote_plus

from tikdrop.compliance import suggest_risk_compliance
from tikdrop.ingestion import SignalStore, ViesError, check_vat, fetch_google_trends_signal, fetch_reddit_signals
from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.score import ProductScoreInput
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.scoring.engine import ProductScoringEngine


def _ask_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    return float(raw) if raw else default


def _ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def _ask_bool(prompt: str, default: bool) -> bool:
    raw = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    if not raw:
        return default
    return raw.startswith("y")


def _pt_market_research_links(keyword: str) -> list:
    # No free/legal automated PT competitor search exists (checked: Bing API retired, Google
    # Custom Search closed to new signups, DuckDuckGo API bars commercial use, SerpApi/Serper
    # free tiers too small to run continuously) - so we just make the manual check one click
    # instead of automating it.
    q = quote_plus(keyword)
    return [
        ("Google (PT)", f"https://www.google.com/search?q={q}&gl=pt&hl=pt-PT"),
        ("Worten", f"https://www.worten.pt/search?query={q}"),
        ("Fnac", f"https://www.fnac.pt/SearchResult/ResultList.aspx?Search={q}"),
        ("Amazon (ES, ships to PT)", f"https://www.amazon.es/s?k={q}"),
        ("Continente", f"https://www.continente.pt/pesquisa?q={q}"),
    ]


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python examples/discover.py "product keyword"')
        return
    keyword = " ".join(sys.argv[1:])

    store = SignalStore()

    print(f"Fetching real signals for '{keyword}'...")

    # The core idea (idea.pdf): find it trending ABROAD first, then check if PT still has
    # room. Worldwide interest is the Trend dimension's main signal - PT-only search volume is
    # usually too thin to say anything (a product can be huge on TikTok globally and still show
    # 0 on Google Trends PT, simply because Portugal is a small market).
    signals = []
    try:
        signals += fetch_google_trends_signal(keyword, geo="")  # "" = worldwide
    except Exception as exc:
        print(f"  Google Trends (worldwide) fetch failed: {exc}")

    try:
        pt_signals = fetch_google_trends_signal(keyword, geo="PT")
    except Exception as exc:
        print(f"  Google Trends (PT) fetch failed: {exc}")
        pt_signals = []

    # Google Trends normalizes each query's 0-100 scale independently per geo/time window, so
    # the worldwide and PT numbers are NOT directly comparable in magnitude - only how many days
    # show any measurable interest at all is roughly comparable across the two.
    if not pt_signals:
        print("  PT: 0 days with measurable interest - looks like it hasn't caught on here yet (the opportunity gap).")
    elif not signals:
        print(f"  PT: interest on {len(pt_signals)} day(s), but the worldwide check found nothing to compare against.")
    elif len(pt_signals) < len(signals) / 2:
        print(f"  PT: interest on only {len(pt_signals)}/{len(signals)} of the days worldwide showed interest - still looks like an early opportunity.")
    else:
        print(f"  PT: interest on {len(pt_signals)}/{len(signals)} of the days worldwide showed interest - may already be fairly known here.")

    if os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"):
        try:
            signals += fetch_reddit_signals(keyword)
        except Exception as exc:
            print(f"  Reddit fetch failed: {exc}")
    else:
        print("  Reddit skipped (REDDIT_CLIENT_ID/SECRET not set) - continuing with Google Trends only.")

    if signals:
        store.save(keyword, signals)
        print(f"  Collected {len(signals)} signal(s) this run (worldwide Google Trends + Reddit, if available).")
    else:
        print("  No signals found this run - you can still continue with manual data below.")

    trend_input = store.build_trend_input(keyword)
    print(f"\nTrendInput built from stored history: {trend_input}")
    print("(TikTok/Instagram not included - no free/legal API for this; check those by hand.)\n")

    previous = store.get_candidate_input(keyword)
    if previous:
        print("Found a previous entry for this candidate - press Enter on any question to keep the old answer.\n")

    print("--- The rest isn't automated yet - fill in what you've found manually ---\n")

    print("Portugal market (no free/legal automated search exists for this - open these to check):")
    for label, url in _pt_market_research_links(keyword):
        print(f"  {label:<24} {url}")
    print()
    portugal_opportunity = PortugalOpportunityInput(
        pt_competitor_count=_ask_int("  PT competitor count", previous.portugal_opportunity.pt_competitor_count if previous else 5),
        differentiation_score=_ask_float(
            "  Differentiation score (0-10)", previous.portugal_opportunity.differentiation_score if previous else 5.0
        ),
    )

    print("\nUnit economics:")
    costs = CostInputs(
        sale_price=_ask_float("  Sale price", previous.costs.sale_price if previous else 20.0),
        product_cost=_ask_float("  Product cost", previous.costs.product_cost if previous else 5.0),
        shipping_cost=_ask_float("  Shipping cost", previous.costs.shipping_cost if previous else 3.0),
        payment_fees=_ask_float("  Payment fees", previous.costs.payment_fees if previous else 1.0),
        ad_cost_per_unit=_ask_float("  Ad cost per unit (CAC)", previous.costs.ad_cost_per_unit if previous else 5.0),
        returns_cost_estimate=_ask_float(
            "  Returns cost estimate", previous.costs.returns_cost_estimate if previous else 1.0
        ),
    )

    print("\nSupplier (Anexo A checklist):")

    vat_validated = _ask_bool("  VAT validated", previous.supplier.vat_validated if previous else True)
    vat_country = input("    EU VAT country code to check live via VIES, or Enter to skip [e.g. PT]: ").strip()
    if vat_country:
        vat_number = input("    VAT number (digits only, no country prefix): ").strip()
        try:
            vat_result = check_vat(vat_country, vat_number)
            vat_validated = vat_result.valid
            print(f"    -> VIES says: {'VALID' if vat_result.valid else 'NOT VALID'}" + (f" ({vat_result.name})" if vat_result.name else ""))
        except ViesError as exc:
            print(f"    VIES check failed, keeping manual answer above: {exc}")

    s = previous.supplier if previous else None
    supplier = SupplierInput(
        identity_verified=_ask_bool("  Identity verified", s.identity_verified if s else True),
        vat_validated=vat_validated,
        eu_warehouse=_ask_bool("  EU warehouse", s.eu_warehouse if s else False),
        dropshipping_confirmed=_ask_bool("  Dropshipping confirmed", s.dropshipping_confirmed if s else True),
        neutral_packaging_possible=_ask_bool("  Neutral packaging possible", s.neutral_packaging_possible if s else True),
        tracking_available=_ask_bool("  Tracking available", s.tracking_available if s else True),
        returns_policy_clear=_ask_bool("  Returns policy clear", s.returns_policy_clear if s else True),
        integration_available=_ask_bool("  API/CSV integration available", s.integration_available if s else False),
        test_order_completed=_ask_bool("  Test order completed", s.test_order_completed if s else False),
        backup_supplier_identified=_ask_bool("  Backup supplier identified", s.backup_supplier_identified if s else False),
    )

    print("\nLogistics:")
    logistics = LogisticsInput(
        weight_grams=_ask_float("  Weight (grams)", previous.logistics.weight_grams if previous else 300.0),
        fragile=_ask_bool("  Fragile", previous.logistics.fragile if previous else False),
        avg_shipping_days=_ask_float("  Avg shipping days", previous.logistics.avg_shipping_days if previous else 10.0),
        size_category="small",
    )

    print("\nCreative (or press Enter to accept a neutral placeholder):")
    creative = CreativeInput(
        demo_video_feasibility=_ask_float(
            "  Demo video feasibility (0-10)", previous.creative.demo_video_feasibility if previous else 5.0
        ),
        ugc_potential=_ask_float("  UGC potential (0-10)", previous.creative.ugc_potential if previous else 5.0),
    )

    print("\nCompliance (idea.pdf section 12 - categories to avoid initially):")
    suggested_risk = suggest_risk_compliance(keyword)
    if suggested_risk.category_risk_level != "low":
        print(f"  Heads up: '{keyword}' matches a keyword for a category the doc says to avoid initially.")
    risk_level = input(f"  Category risk level low/medium/high [{suggested_risk.category_risk_level}]: ").strip().lower() or suggested_risk.category_risk_level
    risk_compliance = RiskComplianceInput(
        category_risk_level=risk_level,
        requires_technical_documentation=_ask_bool(
            "  Requires technical documentation", suggested_risk.requires_technical_documentation
        ),
        is_regulated_category=_ask_bool("  Regulated category", suggested_risk.is_regulated_category),
    )

    product_input = ProductScoreInput(
        product_name=keyword,
        trend=trend_input,
        portugal_opportunity=portugal_opportunity,
        costs=costs,
        supplier=supplier,
        creative=creative,
        logistics=logistics,
        risk_compliance=risk_compliance,
    )

    result = ProductScoringEngine.score(product_input)
    store.save_score_result(keyword, result, product_input=product_input)

    print(f"\n=== {result.product_name} ===")
    print(f"Total score: {result.total_score:.2f}/10")
    print(f"Recommendation: {result.recommendation} ({result.recommendation_reason})")
    for name, d in result.dimensions.items():
        print(f"  {name:20s} raw={d.raw_score:5.2f}  weight={d.weight:.2f}  contribution={d.weighted_contribution:.2f}")

    if result.recommendation == "test":
        print("\n-> Saved to the local opportunities queue as 'queued_for_store'.")


if __name__ == "__main__":
    main()
