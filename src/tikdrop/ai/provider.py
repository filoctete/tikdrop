from typing import Dict, Protocol, Sequence

from tikdrop.schemas.store import StoreCopy


class AIProvider(Protocol):
    """Abstraction layer so the underlying model/vendor can be swapped without touching callers
    (development_guide.pdf section 4/11). Deliberately advisory-only: per section 11, the AI must
    never be the sole source for compliance decisions, financial calculations, or order state -
    those stay in ProfitEngine/ProductScoringEngine as deterministic code. No provider has been
    chosen yet, so only StubAIProvider (no external calls) implements this for now.
    """

    def summarize_trend_signals(self, signals: Sequence[str]) -> str:
        """Turn raw trend signal snippets into a short human-readable summary."""
        ...

    def estimate_creative_potential(self, product_description: str) -> float:
        """Rough 0-10 suggestion for CreativeInput fields; a human should still confirm it."""
        ...

    def extract_product_attributes(self, raw_text: str) -> Dict[str, str]:
        """Pull structured attributes (name, category, materials, ...) out of free text."""
        ...

    def generate_store_copy(self, product_name: str) -> StoreCopy:
        """Draft a public product page - a human should review before it goes live."""
        ...
