import Link from "next/link";
import { listOpportunities } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import QuickScoreForm from "@/components/QuickScoreForm";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const opportunities = await listOpportunities(status);

  const filters = [
    { label: "All", value: undefined },
    { label: "Queued for store", value: "queued_for_store" },
    { label: "Watching", value: "watching" },
    { label: "Rejected", value: "rejected" },
  ];

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="mb-1 text-2xl font-bold">TikDrop — Opportunity Inbox</h1>
      <p className="mb-6 text-sm text-gray-500">
        Product Intelligence candidates, ordered by score.
      </p>

      <QuickScoreForm />

      <div className="mb-4 flex gap-2">
        {filters.map((f) => (
          <Link
            key={f.label}
            href={f.value ? `/?status=${f.value}` : "/"}
            className={`rounded-full px-3 py-1 text-sm ${
              status === f.value
                ? "bg-black text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {f.label}
          </Link>
        ))}
      </div>

      {opportunities.length === 0 ? (
        <p className="text-sm text-gray-500">
          No opportunities scored yet. Add a candidate above.
        </p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="py-2 pr-4">Score</th>
              <th className="py-2 pr-4">Product</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Scored at</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((o) => (
              <tr key={o.candidate_key} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 pr-4 font-mono font-medium">{o.total_score.toFixed(2)}</td>
                <td className="py-2 pr-4">
                  <Link
                    href={`/opportunities/${encodeURIComponent(o.candidate_key)}`}
                    className="text-blue-600 hover:underline"
                  >
                    {o.candidate_key}
                  </Link>
                </td>
                <td className="py-2 pr-4">
                  <StatusBadge status={o.status} />
                </td>
                <td className="py-2 pr-4 text-gray-500">{o.scored_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
