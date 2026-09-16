"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { quickScore } from "@/lib/api";

export default function QuickScoreForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    try {
      await quickScore({
        name: String(formData.get("name")),
        product_cost: Number(formData.get("product_cost")),
        sale_price: Number(formData.get("sale_price")),
        weight_grams: Number(formData.get("weight_grams")),
        avg_shipping_days: Number(formData.get("avg_shipping_days")) || undefined,
        listing_url: String(formData.get("listing_url") || "") || undefined,
      });
      setOpen(false);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        + New candidate
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 p-4"
    >
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="name">
          Product name (used as the Google Trends search term)
        </label>
        <input
          id="name"
          name="name"
          required
          className="w-64 rounded border border-gray-300 px-2 py-1 text-sm"
          placeholder="wooden wireless mouse"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="product_cost">
          Product cost
        </label>
        <input
          id="product_cost"
          name="product_cost"
          type="number"
          step="0.01"
          required
          className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="sale_price">
          Sale price
        </label>
        <input
          id="sale_price"
          name="sale_price"
          type="number"
          step="0.01"
          required
          className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="weight_grams">
          Weight (g)
        </label>
        <input
          id="weight_grams"
          name="weight_grams"
          type="number"
          required
          className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="avg_shipping_days">
          Shipping (days)
        </label>
        <input
          id="avg_shipping_days"
          name="avg_shipping_days"
          type="number"
          placeholder="10"
          className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs text-gray-500" htmlFor="listing_url">
          Listing URL
        </label>
        <input
          id="listing_url"
          name="listing_url"
          type="url"
          placeholder="https://..."
          className="w-56 rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {submitting ? "Scoring..." : "Score it"}
      </button>
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700"
      >
        Cancel
      </button>
      {error && <p className="w-full text-sm text-red-600">{error}</p>}
      <p className="w-full text-xs text-gray-400">
        PT competition, differentiation and margin defaults are placeholders until confirmed
        manually - see the detail page.
      </p>
    </form>
  );
}
