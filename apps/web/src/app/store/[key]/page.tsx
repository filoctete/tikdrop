import Link from "next/link";
import { getStoreProduct } from "@/lib/api";
import BuyButton from "@/components/BuyButton";

export default async function StoreProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ key: string }>;
  searchParams: Promise<{ success?: string; canceled?: string }>;
}) {
  const { key } = await params;
  const { success, canceled } = await searchParams;
  const product = await getStoreProduct(decodeURIComponent(key));

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href="/store" className="text-sm text-blue-600 hover:underline">
        &larr; Back to all products
      </Link>

      {success && (
        <div className="mt-4 rounded-md bg-green-50 p-3 text-sm text-green-800">
          Thank you! Your payment went through.
        </div>
      )}
      {canceled && (
        <div className="mt-4 rounded-md bg-gray-50 p-3 text-sm text-gray-600">
          Checkout was canceled - your card was not charged.
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-2">
        <div className="flex h-64 items-center justify-center rounded-lg bg-gray-100 text-sm text-gray-400">
          Photo coming soon
        </div>

        <div>
          <h1 className="text-2xl font-bold">{product.title}</h1>
          <p className="mt-1 text-gray-500">{product.tagline}</p>
          <p className="mt-4 text-3xl font-bold">€{product.sale_price.toFixed(2)}</p>

          <ul className="mt-4 space-y-1 text-sm">
            {product.benefits.map((b, i) => (
              <li key={i} className="flex items-start gap-2">
                <span>✓</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>

          <p className="mt-4 text-sm text-gray-600">{product.description}</p>

          <div className="mt-6">
            <BuyButton candidateKey={key} />
          </div>
        </div>
      </div>
    </main>
  );
}
