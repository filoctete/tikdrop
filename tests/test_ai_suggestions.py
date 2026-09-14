from tikdrop.ai.suggestions import suggest_creative_input
from tikdrop.ai.stub import StubAIProvider


def test_suggest_creative_input_uses_provider_score_for_both_fields():
    result = suggest_creative_input(StubAIProvider(), "a gadget")

    assert result.demo_video_feasibility == 5.0
    assert result.ugc_potential == 5.0
