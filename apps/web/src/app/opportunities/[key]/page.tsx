import Link from "next/link";
import { getOpportunity } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

const STATUS_BY_RECOMMENDATION: Record<string, string> = {
  test: "queued_for_store",
  watch: "watching",
  reject: "rejected",
};

export default async function OpportunityDetail({
  params,
}: {
  params: Promise<{ key: string }>;
}) {
  const { key } = await params;
  const { result, input } = await getOpportunity(decodeURIComponent(key));

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href="/" className="text-sm text-blue-600 hover:underline">
        &larr; Back to inbox
      </Link>

      <div className="mt-4 mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{result.product_name}</h1>
        <StatusBadge status={STATUS_BY_RECOMMENDATION[result.recommendation] ?? result.recommendation} />
      </div>

      <div className="mb-6 rounded-lg border border-gray-200 p-4">
        <p className="text-3xl font-mono font-bold">{result.total_score.toFixed(2)}/10</p>
        <p className="mt-1 text-sm text-gray-600">{result.recommendation_reason}</p>
      </div>

      <h2 className="mb-2 text-sm font-semibold text-gray-500">Score breakdown</h2>
      <table className="mb-8 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-gray-500">
            <th className="py-2 pr-4">Dimension</th>
            <th className="py-2 pr-4">Raw</th>
            <th className="py-2 pr-4">Weight</th>
            <th className="py-2 pr-4">Contribution</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(result.dimensions).map(([name, d]) => (
            <tr key={name} className="border-b border-gray-100">
              <td className="py-2 pr-4 capitalize">{name.replace(/_/g, " ")}</td>
              <td className="py-2 pr-4 font-mono">{d.raw_score.toFixed(2)}</td>
              <td className="py-2 pr-4 font-mono">{(d.weight * 100).toFixed(0)}%</td>
              <td className="py-2 pr-4 font-mono">{d.weighted_contribution.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {input && (
        <>
          <h2 className="mb-2 text-sm font-semibold text-gray-500">Inputs used</h2>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <dt className="text-gray-500">PT competitors</dt>
            <dd>{input.portugal_opportunity.pt_competitor_count}</dd>
            <dt className="text-gray-500">Differentiation</dt>
            <dd>{input.portugal_opportunity.differentiation_score}/10</dd>
            <dt className="text-gray-500">Sale price</dt>
            <dd>{input.costs.sale_price}</dd>
            <dt className="text-gray-500">Product cost</dt>
            <dd>{input.costs.product_cost}</dd>
            <dt className="text-gray-500">Ad cost/unit</dt>
            <dd>{input.costs.ad_cost_per_unit}</dd>
            <dt className="text-gray-500">Weight</dt>
            <dd>{input.logistics.weight_grams}g</dd>
            <dt className="text-gray-500">Avg shipping</dt>
            <dd>{input.logistics.avg_shipping_days} days</dd>
            <dt className="text-gray-500">VAT validated</dt>
            <dd>{input.supplier.vat_validated ? "Yes" : "No"}</dd>
          </dl>
          <p className="mt-4 text-xs text-gray-400">
            PT competitors and differentiation are placeholders unless manually confirmed via
            examples/discover.py.
          </p>
        </>
      )}
    </main>
  );
}
