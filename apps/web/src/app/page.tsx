import Link from "next/link";
import { listOpportunities, listDiscoveredCandidates } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import QuickScoreForm from "@/components/QuickScoreForm";
import CompleteCandidateForm from "@/components/CompleteCandidateForm";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const [opportunities, discovered] = await Promise.all([
    listOpportunities(status),
    listDiscoveredCandidates(),
  ]);

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

      {discovered.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-1 text-lg font-semibold">Discovered - needs your input</h2>
          <p className="mb-3 text-xs text-gray-500">
            Found automatically from real Google Trends signal. Open a research link, find the real
            supplier cost, then fill in the 3 fields to score it.
          </p>
          <div className="space-y-3">
            {discovered.map((d) => (
              <div key={d.candidate_key} className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="font-semibold">{d.candidate_key}</span>
                  <span className="text-xs text-gray-500">
                    {d.trend_days} days with interest, {d.weeks_sustained} weeks sustained
                  </span>
                </div>
                <div className="mb-3 flex flex-wrap gap-3 text-sm">
                  {d.research_links.map((l) => (
                    <a
                      key={l.label}
                      href={l.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {l.label} ↗
                    </a>
                  ))}
                </div>
                <CompleteCandidateForm candidateKey={d.candidate_key} />
              </div>
            ))}
          </div>
        </section>
      )}

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
