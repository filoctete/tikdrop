"use client";

import { useState } from "react";
import { createCheckoutSession } from "@/lib/api";
import { getDictionary } from "@/lib/dictionary";
import type { Locale } from "@/lib/i18n";

export default function BuyButton({ candidateKey, locale }: { candidateKey: string; locale: Locale }) {
  const t = getDictionary(locale);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckoutSession(candidateKey, locale);
      window.location.href = checkout_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="w-full rounded-md bg-black px-6 py-3 text-base font-semibold text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {loading ? t.redirecting : t.buyNow}
      </button>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error.includes("503") ? t.paymentsNotSetUp : error}</p>
      )}
      <p className="mt-2 text-center text-xs text-gray-400">{t.paymentNote}</p>
    </div>
  );
}
