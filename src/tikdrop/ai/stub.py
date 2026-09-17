from typing import Dict, Sequence

from tikdrop.schemas.store import StoreCopy


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

    def generate_store_copy(self, product_name: str, language: str = "pt") -> StoreCopy:
        # No real translation without a model - keeps English placeholder text regardless of
        # `language`, tagged so it's obvious this still needs a human (or GroqAIProvider).
        title = product_name.strip().title()
        return StoreCopy(
            title=title,
            tagline=f"Discover the {title}. [{language} placeholder - not translated]",
            description=f"The {title} - review and rewrite this placeholder copy before publishing.",
            benefits=["Placeholder benefit - edit before publishing"],
        )
