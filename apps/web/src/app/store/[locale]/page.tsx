import Link from "next/link";
import { notFound } from "next/navigation";
import { listStoreProducts } from "@/lib/api";
import { getDictionary } from "@/lib/dictionary";
import { isValidLocale, SUPPORTED_LOCALES, LOCALE_NAMES } from "@/lib/i18n";

export function generateStaticParams() {
  return SUPPORTED_LOCALES.map((locale) => ({ locale }));
}

export default async function StorePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isValidLocale(locale)) notFound();

  const t = getDictionary(locale);
  const products = await listStoreProducts(locale);

  return (
    <main className="mx-auto max-w-5xl p-8">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="mb-1 text-3xl font-bold">{t.storeTitle}</h1>
          <p className="text-sm text-gray-500">{t.storeSubtitle}</p>
        </div>
        <div className="flex gap-2 text-sm">
          {SUPPORTED_LOCALES.map((l) => (
            <Link
              key={l}
              href={`/store/${l}`}
              className={`rounded-full px-3 py-1 ${
                l === locale ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {LOCALE_NAMES[l]}
            </Link>
          ))}
        </div>
      </div>

      {products.length === 0 ? (
        <p className="text-sm text-gray-500">{t.noProducts}</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
          {products.map((p) => (
            <Link
              key={p.candidate_key}
              href={`/store/${locale}/${encodeURIComponent(p.candidate_key)}`}
              className="rounded-lg border border-gray-200 p-5 transition hover:shadow-md"
            >
              <div className="mb-3 flex h-32 items-center justify-center rounded-md bg-gray-100 text-xs text-gray-400">
                {t.photoComingSoon}
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
