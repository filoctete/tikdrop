"""Demonstrates the real (free-tier) AI provider. Needs:
  1. pip install -e ".[groq]"
  2. A free key from https://console.groq.com/keys, set as: GROQ_API_KEY=...

Run with: python examples/groq_ai_demo.py
"""

import os

from _env import load_dotenv_if_present

from tikdrop.ai.groq_provider import AIProviderError, GroqAIProvider

load_dotenv_if_present()

PRODUCT_DESCRIPTION = (
    "Reusable, self-cleaning silicone roller that removes pet hair from clothes, sofas and car "
    "seats without needing lint sheets."
)

TREND_SIGNALS = [
    "TikTok video demoing the roller on a couch has 2.3M views and 40k saves",
    "Reddit r/BuyItForLife thread asking for a durable pet-hair-removal tool, 300+ upvotes",
    "Google Trends shows steady search growth for 'pet hair roller' over the last 6 weeks",
]


def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("Set GROQ_API_KEY first (free key at https://console.groq.com/keys).")
        return

    with GroqAIProvider() as ai:
        try:
            print("Trend summary:")
            print(" ", ai.summarize_trend_signals(TREND_SIGNALS))

            print("\nCreative potential (0-10):")
            print(" ", ai.estimate_creative_potential(PRODUCT_DESCRIPTION))

            print("\nExtracted attributes:")
            print(" ", ai.extract_product_attributes(PRODUCT_DESCRIPTION))
        except AIProviderError as exc:
            print(f"AI call failed: {exc}")


if __name__ == "__main__":
    main()
