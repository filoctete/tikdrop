import Link from "next/link";
import { listStoreProducts } from "@/lib/api";

export const metadata = {
  title: "TikDrop Store",
};

export default async function StorePage() {
  const products = await listStoreProducts();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-1 text-3xl font-bold">TikDrop</h1>
      <p className="mb-8 text-sm text-gray-500">Products we found, validated and stand behind.</p>

      {products.length === 0 ? (
        <p className="text-sm text-gray-500">No products published yet - check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
          {products.map((p) => (
            <Link
              key={p.candidate_key}
              href={`/store/${encodeURIComponent(p.candidate_key)}`}
              className="rounded-lg border border-gray-200 p-5 transition hover:shadow-md"
            >
              <div className="mb-3 flex h-32 items-center justify-center rounded-md bg-gray-100 text-xs text-gray-400">
                Photo coming soon
              </div>
              <h2 className="font-semibold">{p.title}</h2>
              <p className="mt-1 text-lg font-bold">€{p.sale_price.toFixed(2)}</p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
