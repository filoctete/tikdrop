"""Opportunity Inbox (development_guide.pdf section 15): lists every product candidate scored
so far, ordered by score, and can show the full per-dimension breakdown for one of them.

Run with:
  python examples/inbox.py                  # list everything
  python examples/inbox.py --status test     # filter by status: queued_for_store, watching, rejected
  python examples/inbox.py --detail "pet hair roller"
  python examples/inbox.py --export opportunities.csv
"""

import csv
import sys

from tikdrop.ingestion import SignalStore
from tikdrop.scoring import WEIGHTS

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


def _export_csv(store: SignalStore, path: str) -> None:
    opportunities = store.list_opportunities()
    dimension_names = list(WEIGHTS)
    fieldnames = [
        "candidate_key", "total_score", "recommendation", "status", "scored_at",
        *[f"dim_{d}" for d in dimension_names],
        "sale_price", "product_cost", "pt_competitor_count", "differentiation_score",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for o in opportunities:
            row = {
                "candidate_key": o["candidate_key"],
                "total_score": round(o["total_score"], 2),
                "recommendation": o["recommendation"],
                "status": o["status"],
                "scored_at": o["scored_at"],
            }

            detail = store.get_opportunity_detail(o["candidate_key"])
            for d in dimension_names:
                row[f"dim_{d}"] = round(detail.dimensions[d].raw_score, 2) if detail and d in detail.dimensions else ""

            candidate_input = store.get_candidate_input(o["candidate_key"])
            if candidate_input:
                row["sale_price"] = candidate_input.costs.sale_price
                row["product_cost"] = candidate_input.costs.product_cost
                row["pt_competitor_count"] = candidate_input.portugal_opportunity.pt_competitor_count
                row["differentiation_score"] = candidate_input.portugal_opportunity.differentiation_score

            writer.writerow(row)

    print(f"Exported {len(opportunities)} opportunity(ies) to {path}")


def main() -> None:
    args = sys.argv[1:]
    store = SignalStore()

    if "--export" in args:
        idx = args.index("--export")
        path = args[idx + 1] if idx + 1 < len(args) else "opportunities.csv"
        _export_csv(store, path)
        return

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
