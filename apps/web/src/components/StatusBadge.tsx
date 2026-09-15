const STYLES: Record<string, string> = {
  queued_for_store: "bg-green-100 text-green-800",
  watching: "bg-amber-100 text-amber-800",
  rejected: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }: { status: string }) {
  const style = STYLES[status] ?? "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
