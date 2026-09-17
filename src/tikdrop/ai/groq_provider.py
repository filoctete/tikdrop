"""Real AIProvider implementation backed by Groq's free-tier API (OpenAI-compatible chat
completions). Needs httpx: `pip install -e ".[groq]"`.

Setup:
  1. Free key at https://console.groq.com/keys
  2. Set it as an environment variable: GROQ_API_KEY=... (never hardcode it, never commit it)

This is deliberately the only file in tikdrop that talks to a specific AI vendor - everything
else in the system depends on the AIProvider protocol, so swapping vendors later means adding a
new file here, not touching callers.
"""

import json
import os
from typing import Dict, List, Optional, Sequence

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    raise ImportError('GroqAIProvider needs httpx. Install with: pip install -e ".[groq]"') from exc

from tikdrop.schemas.store import StoreCopy

_DEFAULT_MODEL = "openai/gpt-oss-20b"
_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class AIProviderError(RuntimeError):
    """Raised when the Groq API call fails or returns something we can't use."""


class GroqAIProvider:
    def __init__(self, api_key: Optional[str] = None, model: str = _DEFAULT_MODEL, timeout: float = 30.0) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            raise AIProviderError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys "
                "and set it as an environment variable."
            )
        self._model = model
        self._client = httpx.Client(timeout=timeout)

    def _chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        payload: Dict[str, object] = {"model": self._model, "messages": messages, "temperature": 0.2}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = self._client.post(
            _API_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
        )
        if response.status_code != 200:
            raise AIProviderError(f"Groq API error {response.status_code}: {response.text}")

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(f"Unexpected Groq response shape: {data}") from exc

    def summarize_trend_signals(self, signals: Sequence[str]) -> str:
        if not signals:
            return "No trend signals available."
        prompt = (
            "Summarize these product trend signals in 2-3 sentences, focused on whether demand "
            "looks real and growing vs. a short-lived spike:\n" + "\n".join(f"- {s}" for s in signals)
        )
        return self._chat([{"role": "user", "content": prompt}]).strip()

    def estimate_creative_potential(self, product_description: str) -> float:
        prompt = (
            "Rate from 0 to 10 how easy it is to demonstrate this product's benefit in a short "
            "(15-30s) social video, and how likely it is to generate organic UGC, as a single "
            "combined score.\n"
            f"Product: {product_description}\n"
            'Respond with exactly this JSON shape and no other keys or text: {"score": 7.5}'
        )
        content = self._chat([{"role": "user", "content": prompt}], json_mode=True)
        try:
            score = float(json.loads(content)["score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise AIProviderError(f"Could not parse creative potential score from: {content}") from exc
        return max(0.0, min(10.0, score))

    def extract_product_attributes(self, raw_text: str) -> Dict[str, str]:
        prompt = (
            "Extract product attributes (name, category, material, key_benefit, target_audience) "
            f"from this text. Respond with a flat JSON object of strings only:\n{raw_text}"
        )
        content = self._chat([{"role": "user", "content": prompt}], json_mode=True)
        try:
            attrs = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"Could not parse attributes JSON from: {content}") from exc
        return {str(k): str(v) for k, v in attrs.items()}

    def generate_store_copy(self, product_name: str, language: str = "pt") -> StoreCopy:
        from tikdrop.i18n import SUPPORTED_LANGUAGES, normalize_language

        language_name = SUPPORTED_LANGUAGES[normalize_language(language)]["english_name"]
        prompt = (
            f"Write short, honest marketing copy in {language_name} for this dropshipping "
            "product listing. No exaggerated claims, no medical/health claims, no invented "
            "facts. All text (title, tagline, description, benefits) must be in "
            f"{language_name}, not English, unless that is the requested language.\n"
            f"Product: {product_name}\n"
            "Respond with exactly this JSON shape and no other keys or text: "
            '{"title": "...", "tagline": "...", "description": "...", "benefits": ["...", "...", "..."]}'
        )
        content = self._chat([{"role": "user", "content": prompt}], json_mode=True)
        try:
            data = json.loads(content)
            return StoreCopy(
                title=str(data["title"]),
                tagline=str(data["tagline"]),
                description=str(data["description"]),
                benefits=[str(b) for b in data["benefits"]],
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise AIProviderError(f"Could not parse store copy from: {content}") from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GroqAIProvider":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
