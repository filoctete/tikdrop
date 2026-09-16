"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { quickScore } from "@/lib/api";

export default function CompleteCandidateForm({ candidateKey }: { candidateKey: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    try {
      await quickScore({
        name: candidateKey,
        product_cost: Number(formData.get("product_cost")),
        sale_price: Number(formData.get("sale_price")),
        weight_grams: Number(formData.get("weight_grams")),
      });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <div className="flex flex-col">
        <label className="text-xs text-gray-500">Product cost</label>
        <input
          name="product_cost"
          type="number"
          step="0.01"
          required
          className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500">Sale price</label>
        <input
          name="sale_price"
          type="number"
          step="0.01"
          required
          className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500">Weight (g)</label>
        <input name="weight_grams" type="number" required className="w-20 rounded border border-gray-300 px-2 py-1 text-sm" />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-black px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {submitting ? "Scoring..." : "Score it"}
      </button>
      {error && <p className="w-full text-sm text-red-600">{error}</p>}
    </form>
  );
}
