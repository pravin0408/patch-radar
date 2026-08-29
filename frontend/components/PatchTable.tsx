import type { Patch } from "@/lib/api";
import SeverityBadge from "./SeverityBadge";

const VENDOR_LABELS: Record<string, string> = {
  dell: "Dell",
  cisco: "Cisco",
  netscaler: "NetScaler",
  hpe: "HPE",
  vmware: "VMware",
  paloalto: "Palo Alto",
  fortinet: "Fortinet",
  f5: "F5 Networks",
};

export default function PatchTable({ patches }: { patches: Patch[] }) {
  if (patches.length === 0) {
    return (
      <div className="rounded-lg border border-gray-800 bg-gray-900/30 p-8 text-center text-gray-500">
        No patches match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-900 text-xs uppercase tracking-wide text-gray-400">
          <tr>
            <th className="px-4 py-3">Vendor</th>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">Component</th>
            <th className="px-4 py-3">Latest Version</th>
            <th className="px-4 py-3">Released</th>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">CVEs</th>
            <th className="px-4 py-3">Links</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {patches.map((p, i) => (
            <tr key={`${p.vendor}-${p.model}-${p.component_type}-${i}`} className="hover:bg-gray-900/50">
              <td className="px-4 py-3 font-medium">{VENDOR_LABELS[p.vendor] ?? p.vendor}</td>
              <td className="px-4 py-3">{p.model}</td>
              <td className="px-4 py-3 text-gray-400">{p.component_type}</td>
              <td className="px-4 py-3 font-mono">{p.version}</td>
              <td className="px-4 py-3 text-gray-400">
                {new Date(p.release_date).toLocaleDateString("en-US", {
                  month: "short",
                  year: "numeric",
                })}
              </td>
              <td className="px-4 py-3">
                <SeverityBadge severity={p.severity} />
              </td>
              <td className="px-4 py-3 text-xs text-gray-500">
                {p.cves.length > 0 ? p.cves.join(", ") : "—"}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-3">
                  {p.advisory_url && (
                    <a
                      href={p.advisory_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline"
                    >
                      Advisory ↗
                    </a>
                  )}
                  {p.download_url && (
                    <a
                      href={p.download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline"
                    >
                      Download ↗
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
