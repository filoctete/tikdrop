import pytest

httpx = pytest.importorskip("httpx")

from tikdrop.ai.groq_provider import AIProviderError, GroqAIProvider


def _provider() -> GroqAIProvider:
    return GroqAIProvider(api_key="test-key")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(AIProviderError):
        GroqAIProvider(api_key=None)


def test_summarize_trend_signals_with_no_signals_skips_the_api_call():
    provider = _provider()
    assert provider.summarize_trend_signals([]) == "No trend signals available."


def test_estimate_creative_potential_parses_score(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(provider, "_chat", lambda messages, json_mode=False: '{"score": 7.5}')

    assert provider.estimate_creative_potential("a gadget") == 7.5


def test_estimate_creative_potential_clamps_out_of_range_scores(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(provider, "_chat", lambda messages, json_mode=False: '{"score": 15}')

    assert provider.estimate_creative_potential("a gadget") == 10.0


def test_estimate_creative_potential_raises_on_malformed_json(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(provider, "_chat", lambda messages, json_mode=False: "not json")

    with pytest.raises(AIProviderError):
        provider.estimate_creative_potential("a gadget")


def test_extract_product_attributes_parses_json(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(
        provider,
        "_chat",
        lambda messages, json_mode=False: '{"name": "Widget", "category": "Home"}',
    )

    attrs = provider.extract_product_attributes("some raw text")

    assert attrs == {"name": "Widget", "category": "Home"}


def test_generate_store_copy_parses_json(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(
        provider,
        "_chat",
        lambda messages, json_mode=False: (
            '{"title": "Widget", "tagline": "Great widget", "description": "A widget.", '
            '"benefits": ["Fast", "Durable"]}'
        ),
    )

    copy = provider.generate_store_copy("widget")

    assert copy.title == "Widget"
    assert copy.benefits == ["Fast", "Durable"]


def test_generate_store_copy_raises_on_malformed_json(monkeypatch):
    provider = _provider()
    monkeypatch.setattr(provider, "_chat", lambda messages, json_mode=False: "not json")

    with pytest.raises(AIProviderError):
        provider.generate_store_copy("widget")
