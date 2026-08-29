"use client";

import { useCallback, useEffect, useState } from "react";
import FilterBar from "@/components/FilterBar";
import PatchTable from "@/components/PatchTable";
import Pagination from "@/components/Pagination";
import VendorStatusBadge from "@/components/VendorStatusBadge";
import {
  fetchPatches,
  fetchVendorStatus,
  getExportCsvUrl,
  type Patch,
  type PatchFilters,
  type PatchListResponse,
  type VendorStatus,
} from "@/lib/api";

export default function DashboardPage() {
  const [filters, setFilters] = useState<PatchFilters>({
    latest_only: true,
    limit: 50,
    offset: 0,
  });
  const [patchResponse, setPatchResponse] = useState<PatchListResponse>({
    count: 0,
    total: 0,
    limit: 50,
    offset: 0,
    results: [],
  });
  const [vendors, setVendors] = useState<VendorStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([fetchPatches(filters), fetchVendorStatus()])
      .then(([patchRes, vendorRes]) => {
        if (cancelled) return;
        setPatchResponse(patchRes);
        setVendors(vendorRes);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load data");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [filters]);

  const handlePageChange = useCallback(
    (newOffset: number) => {
      setFilters((prev) => ({ ...prev, offset: newOffset }));
    },
    []
  );

  const handleFiltersChange = useCallback(
    (newFilters: PatchFilters) => {
      // Reset offset when filters change
      setFilters({ ...newFilters, offset: 0, limit: filters.limit });
    },
    [filters.limit]
  );

  function handleExportCsv() {
    // Client-side CSV generation for the static demo site
    // (In full production with backend, use getExportCsvUrl)
    const header = [
      "vendor", "model", "component_type", "version", 
      "release_date", "severity", "cves", "advisory_url"
    ];
    const rows = patchResponse.results.map((p) =>
      [
        p.vendor, p.model, p.component_type, p.version, 
        p.release_date, p.severity ?? "", p.cves.join(";"), p.advisory_url
      ]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(",")
    );
    const csv = [header.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "patch-radar-export.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const degradedVendors = vendors.filter((v) => v.status === "DEGRADED");

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            Unified Hardware Patch & Advisory Radar
          </h1>
          <p className="text-sm text-gray-500">
            Aggregated patch, firmware, and advisory data across Dell EMC,
            Cisco, NetScaler, and HPE.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={patchResponse.total === 0}
            className="rounded border border-gray-700 bg-gray-900 px-4 py-2 text-sm font-medium hover:bg-gray-800 disabled:opacity-40"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Vendor Status Row */}
      <div className="mb-6 flex flex-wrap gap-2">
        {vendors.map((v) => (
          <VendorStatusBadge key={v.id} vendor={v} />
        ))}
      </div>

      {/* DEGRADED vendor warning */}
      {degradedVendors.length > 0 && (
        <div className="mb-4 rounded border border-amber-800 bg-amber-950/50 px-4 py-3 text-sm text-amber-300">
          <span className="font-semibold">Data Freshness Warning:</span>{" "}
          {degradedVendors.map((v) => v.display_name).join(", ")}{" "}
          {degradedVendors.length === 1 ? "is" : "are"} in DEGRADED state.
          Patch data may be stale due to consecutive ingestion failures.
        </div>
      )}

      <div className="mb-4">
        <FilterBar filters={filters} onChange={handleFiltersChange} />
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-800 bg-red-950 px-4 py-3 text-sm text-red-300">
          {error}. Is the backend running at{" "}
          <code>
            {process.env.NEXT_PUBLIC_API_BASE_URL ??
              "http://localhost:8000/api/v1"}
          </code>
          ?
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-8">
          <div className="flex items-center gap-3 text-gray-500">
            <svg
              className="h-5 w-5 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Loading patches...
          </div>
        </div>
      ) : (
        <>
          <PatchTable patches={patchResponse.results} />
          <Pagination
            total={patchResponse.total}
            limit={patchResponse.limit}
            offset={patchResponse.offset}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </main>
  );
}
