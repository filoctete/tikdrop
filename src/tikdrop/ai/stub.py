from typing import Dict, Sequence


class StubAIProvider:
    """Placeholder implementation of AIProvider: no external API calls, no model chosen yet.
    Good enough to wire the rest of the system end-to-end; replace with a real provider
    (e.g. Claude) behind the same AIProvider interface when one is picked.
    """

    def summarize_trend_signals(self, signals: Sequence[str]) -> str:
        if not signals:
            return "No trend signals available."
        return f"{len(signals)} signal(s) collected; first: \"{signals[0]}\""

    def estimate_creative_potential(self, product_description: str) -> float:
        return 5.0  # neutral placeholder - always review manually before trusting this

    def extract_product_attributes(self, raw_text: str) -> Dict[str, str]:
        return {}
