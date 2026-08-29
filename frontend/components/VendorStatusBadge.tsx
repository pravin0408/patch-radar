import type { VendorStatus } from "@/lib/api";

function formatTimeAgo(dateStr: string | null): string {
  if (!dateStr) return "never";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export default function VendorStatusBadge({ vendor }: { vendor: VendorStatus }) {
  const ok = vendor.status === "OK";
  return (
    <div
      className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm ${
        ok
          ? "border-emerald-800 bg-emerald-950 text-emerald-300"
          : "border-red-800 bg-red-950 text-red-300"
      }`}
      title={
        ok
          ? `Last successful ingestion: ${vendor.last_success_at ?? "never"}`
          : `${vendor.consecutive_failures} consecutive ingestion failures. Data may be stale.`
      }
    >
      <span
        className={`h-2 w-2 rounded-full ${
          ok ? "bg-emerald-400 animate-pulse" : "bg-red-400 animate-pulse"
        }`}
      />
      <span className="font-medium">{vendor.display_name}</span>
      <span className="text-xs uppercase opacity-70">
        {vendor.status}
      </span>
      <span className="text-xs opacity-50">
        {ok
          ? formatTimeAgo(vendor.last_success_at)
          : `${vendor.consecutive_failures} failures`}
      </span>
    </div>
  );
}
