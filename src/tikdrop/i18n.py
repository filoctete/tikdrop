"""Single source of truth for which languages the public storefront supports. Add a language
here and it's immediately usable everywhere that imports this (AI copy generation, the API's
`lang` query params, Stripe checkout line items) - the frontend mirrors this list in
apps/web/src/lib/i18n.ts (kept in sync by hand, since the two apps don't share a build step).
"""

from typing import Dict

# code -> (English name shown to the AI prompt, native name for UI)
SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "pt": {"english_name": "European Portuguese (pt-PT)", "native_name": "Português"},
    "en": {"english_name": "English", "native_name": "English"},
    "es": {"english_name": "Spanish (Spain)", "native_name": "Español"},
}

DEFAULT_LANGUAGE = "pt"


def normalize_language(language: str) -> str:
    """Falls back to the default for anything not in SUPPORTED_LANGUAGES, rather than erroring -
    a typo'd or unsupported ?lang= shouldn't break the storefront."""
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
