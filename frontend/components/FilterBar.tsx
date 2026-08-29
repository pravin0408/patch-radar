"use client";

import type { PatchFilters } from "@/lib/api";

const VENDORS = [
  { value: "", label: "All Vendors" },
  { value: "dell", label: "Dell EMC" },
  { value: "cisco", label: "Cisco" },
  { value: "netscaler", label: "NetScaler" },
  { value: "hpe", label: "HPE" },
];

const SEVERITIES = [
  { value: "", label: "All Severities" },
  { value: "CRITICAL", label: "Critical" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
];

interface Props {
  filters: PatchFilters;
  onChange: (filters: PatchFilters) => void;
}

export default function FilterBar({ filters, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-800 bg-gray-900/50 p-3">
      <select
        className="rounded border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm"
        value={filters.vendor ?? ""}
        onChange={(e) => onChange({ ...filters, vendor: e.target.value || undefined })}
      >
        {VENDORS.map((v) => (
          <option key={v.value} value={v.value}>
            {v.label}
          </option>
        ))}
      </select>

      <select
        className="rounded border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm"
        value={filters.severity ?? ""}
        onChange={(e) => onChange({ ...filters, severity: e.target.value || undefined })}
      >
        {SEVERITIES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      <input
        type="text"
        placeholder="Search model (e.g. PowerEdge, Catalyst)..."
        className="min-w-[240px] flex-1 rounded border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm"
        value={filters.model ?? ""}
        onChange={(e) => onChange({ ...filters, model: e.target.value || undefined })}
      />

      <label className="flex items-center gap-2 text-sm text-gray-400">
        <input
          type="checkbox"
          checked={filters.latest_only ?? true}
          onChange={(e) => onChange({ ...filters, latest_only: e.target.checked })}
        />
        Latest only
      </label>
    </div>
  );
}
