import Link from "next/link";
import { notFound } from "next/navigation";
import { getStoreProduct } from "@/lib/api";
import { getDictionary } from "@/lib/dictionary";
import { isValidLocale } from "@/lib/i18n";
import BuyButton from "@/components/BuyButton";

export default async function StoreProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; key: string }>;
  searchParams: Promise<{ success?: string; canceled?: string }>;
}) {
  const { locale, key } = await params;
  if (!isValidLocale(locale)) notFound();

  const t = getDictionary(locale);
  const { success, canceled } = await searchParams;
  const product = await getStoreProduct(decodeURIComponent(key), locale);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href={`/store/${locale}`} className="text-sm text-blue-600 hover:underline">
        &larr; {t.backToAll}
      </Link>

      {success && (
        <div className="mt-4 rounded-md bg-green-50 p-3 text-sm text-green-800">{t.thankYou}</div>
      )}
      {canceled && (
        <div className="mt-4 rounded-md bg-gray-50 p-3 text-sm text-gray-600">{t.checkoutCanceled}</div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-2">
        <div className="flex h-64 items-center justify-center rounded-lg bg-gray-100 text-sm text-gray-400">
          {t.photoComingSoon}
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
            <BuyButton candidateKey={key} locale={locale} />
          </div>
        </div>
      </div>
    </main>
  );
}
