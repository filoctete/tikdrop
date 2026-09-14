"""Opportunity Inbox (development_guide.pdf section 15): lists every product candidate scored
so far, ordered by score, and can show the full per-dimension breakdown for one of them.

Run with:
  python examples/inbox.py                  # list everything
  python examples/inbox.py --status test     # filter by status: queued_for_store, watching, rejected
  python examples/inbox.py --detail "pet hair roller"
"""

import sys

from tikdrop.ingestion import SignalStore

_STATUS_ALIASES = {"test": "queued_for_store", "watch": "watching", "reject": "rejected"}


def _print_list(store: SignalStore, status: str = None) -> None:
    opportunities = store.list_opportunities(status=status)
    if not opportunities:
        print("No opportunities scored yet. Run examples/discover.py first.")
        return

    print(f"{'score':>6}  {'status':<16}  {'product':<40}  scored_at")
    print("-" * 90)
    for o in opportunities:
        print(f"{o['total_score']:>6.2f}  {o['status']:<16}  {o['candidate_key'][:40]:<40}  {o['scored_at']}")


def _print_detail(store: SignalStore, candidate_key: str) -> None:
    result = store.get_opportunity_detail(candidate_key)
    if result is None:
        print(f"No scored opportunity found for '{candidate_key}'.")
        return

    print(f"=== {result.product_name} ===")
    print(f"Total score: {result.total_score:.2f}/10")
    print(f"Recommendation: {result.recommendation} ({result.recommendation_reason})")
    for name, d in result.dimensions.items():
        print(f"  {name:20s} raw={d.raw_score:5.2f}  weight={d.weight:.2f}  contribution={d.weighted_contribution:.2f}")

    product_input = store.get_candidate_input(candidate_key)
    if product_input:
        print("\nInputs used:")
        print(f"  PT competitors: {product_input.portugal_opportunity.pt_competitor_count}")
        print(f"  Differentiation: {product_input.portugal_opportunity.differentiation_score}/10")
        print(f"  Sale price: {product_input.costs.sale_price}")
        print(f"  Product cost: {product_input.costs.product_cost}")
        print(f"  VAT validated: {product_input.supplier.vat_validated}")
        print(f"  Weight: {product_input.logistics.weight_grams}g, ships in ~{product_input.logistics.avg_shipping_days} days")


def main() -> None:
    args = sys.argv[1:]
    store = SignalStore()

    if "--detail" in args:
        idx = args.index("--detail")
        candidate_key = " ".join(args[idx + 1 :])
        _print_detail(store, candidate_key)
        return

    status = None
    if "--status" in args:
        idx = args.index("--status")
        raw_status = args[idx + 1]
        status = _STATUS_ALIASES.get(raw_status, raw_status)

    _print_list(store, status=status)


if __name__ == "__main__":
    main()
