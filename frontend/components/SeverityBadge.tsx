import type { Severity } from "@/lib/api";

const STYLES: Record<Severity, string> = {
  CRITICAL: "bg-red-950 text-red-300 border-red-700",
  HIGH: "bg-orange-950 text-orange-300 border-orange-700",
  MEDIUM: "bg-yellow-950 text-yellow-300 border-yellow-700",
  LOW: "bg-gray-800 text-gray-300 border-gray-600",
};

export default function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) {
    return <span className="text-xs text-gray-500">—</span>;
  }
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 text-xs font-semibold tracking-wide ${STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
