"use client";

import { useState } from "react";
import { createCheckoutSession } from "@/lib/api";

export default function BuyButton({ candidateKey }: { candidateKey: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckoutSession(candidateKey);
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
        {loading ? "Redirecting to secure checkout..." : "Buy now"}
      </button>
      {error && (
        <p className="mt-2 text-sm text-red-600">
          {error.includes("503") ? "Payments aren't set up yet - check back soon." : error}
        </p>
      )}
      <p className="mt-2 text-center text-xs text-gray-400">
        Payment handled securely by Stripe - we never see your card details.
      </p>
    </div>
  );
}
