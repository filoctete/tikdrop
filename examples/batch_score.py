"""Scores a batch of lightly-researched candidates (e.g. pulled from a supplier platform's
public "trending products" page) using real worldwide Google Trends data, with PT competition
and differentiation left as explicit placeholders (see quick_input.py) until a human confirms
them. This is the formalized version of the one-off scripts used to source the first real
candidates - add more entries to candidates_seed.json (or point at your own file) to keep going.

Run with:
  python examples/batch_score.py                       # uses candidates_seed.json
  python examples/batch_score.py my_candidates.json
"""

import json
import sys
from pathlib import Path

from tikdrop.ingestion import SignalStore, fetch_google_trends_signal
from tikdrop.scoring import ProductScoringEngine, build_quick_score_input

_DEFAULT_SEED = Path(__file__).parent / "candidates_seed.json"


def score_candidate(store: SignalStore, candidate: dict):
    name = candidate["name"]

    try:
        worldwide_signals = fetch_google_trends_signal(name, geo="")
    except Exception as exc:
        print(f"  Google Trends fetch failed for '{name}': {exc}")
        worldwide_signals = []

    if worldwide_signals:
        store.save(name, worldwide_signals)
    trend_input = store.build_trend_input(name)

    product_input = build_quick_score_input(
        name=name,
        trend_input=trend_input,
        product_cost=candidate["product_cost"],
        sale_price=candidate["sale_price"],
        weight_grams=candidate["weight_grams"],
        demo_video_feasibility=candidate.get("demo_video_feasibility", 5.0),
        ugc_potential=candidate.get("ugc_potential", 5.0),
    )

    result = ProductScoringEngine.score(product_input)
    store.save_score_result(name, result, product_input=product_input)
    return result


def main() -> None:
    seed_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_SEED
    candidates = json.loads(seed_path.read_text(encoding="utf-8"))

    store = SignalStore()

    for candidate in candidates:
        print(f"\n{'=' * 60}\n{candidate['name']}\n{'=' * 60}")
        if candidate.get("source"):
            print(f"Source: {candidate['source']}")

        result = score_candidate(store, candidate)

        print(f"Score: {result.total_score:.2f}/10 -> {result.recommendation} ({result.recommendation_reason})")
        for dim_name, d in result.dimensions.items():
            print(f"  {dim_name:20s} raw={d.raw_score:5.2f}")

    print(f"\nAll {len(candidates)} candidate(s) saved to the opportunities queue. Run examples/inbox.py to review.")


if __name__ == "__main__":
    main()
