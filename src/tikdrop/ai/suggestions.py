"""Advisory-only helpers that call an AIProvider to pre-fill scoring inputs. A human should
still review the result before trusting it - development_guide.pdf section 11 is explicit that
AI must not be the sole source for anything feeding the deterministic ProductScoringEngine.
Nothing here is called automatically by the scoring engine; callers opt in explicitly.
"""

from tikdrop.ai.provider import AIProvider
from tikdrop.schemas.creative import CreativeInput


def suggest_creative_input(ai: AIProvider, product_description: str) -> CreativeInput:
    """Coarse starting point for CreativeInput: the same AI score is used for both sub-fields,
    since AIProvider only exposes one combined creative-potential estimate. Treat this as a
    first draft to adjust by hand, not two independently measured judgments.
    """
    score = ai.estimate_creative_potential(product_description)
    return CreativeInput(demo_video_feasibility=score, ugc_potential=score)
