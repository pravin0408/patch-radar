import { fetchDemoPatches, fetchDemoVendorStatus } from "./demo-data";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface Patch {
  vendor: string;
  model: string;
  component_type: string;
  version: string;
  release_date: string;
  severity: Severity | null;
  cves: string[];
  advisory_url: string;
  download_url: string | null;
  requires_entitlement: boolean;
  is_latest: boolean;
  is_recommended: boolean;
}

export interface PatchListResponse {
  count: number;
  total: number;
  limit: number;
  offset: number;
  results: Patch[];
}

export interface VendorStatus {
  id: string;
  display_name: string;
  status: "OK" | "DEGRADED";
  last_success_at: string | null;
  consecutive_failures: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface PatchFilters {
  vendor?: string;
  model?: string;
  severity?: string;
  latest_only?: boolean;
  limit?: number;
  offset?: number;
}

export async function fetchPatches(filters: PatchFilters): Promise<PatchListResponse> {
  const params = new URLSearchParams();
  if (filters.vendor) params.set("vendor", filters.vendor);
  if (filters.model) params.set("model", filters.model);
  if (filters.severity) params.set("severity", filters.severity);
  params.set("latest_only", String(filters.latest_only ?? true));
  params.set("limit", String(filters.limit ?? 50));
  params.set("offset", String(filters.offset ?? 0));

  try {
    const res = await fetch(`${API_BASE}/patches?${params.toString()}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using demo data for patches", err);
    return fetchDemoPatches(filters);
  }
}

export async function fetchVendorStatus(): Promise<VendorStatus[]> {
  try {
    const res = await fetch(`${API_BASE}/vendors`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using demo data for vendors", err);
    return fetchDemoVendorStatus();
  }
}

export function getExportCsvUrl(filters: PatchFilters): string {
  const params = new URLSearchParams();
  if (filters.vendor) params.set("vendor", filters.vendor);
  if (filters.model) params.set("model", filters.model);
  if (filters.severity) params.set("severity", filters.severity);
  params.set("latest_only", String(filters.latest_only ?? true));
  return `${API_BASE}/patches/export.csv?${params.toString()}`;
}

export interface GapReportAsset {
  vendor: string;
  model: string;
  component_type: string;
  current_version: string;
}

export interface GapEntry {
  vendor: string;
  model: string;
  component_type: string;
  current_version: string;
  latest_version: string | null;
  latest_release_date: string | null;
  severity: Severity | null;
  cves: string[];
  advisory_url: string | null;
  is_behind: boolean;
  versions_behind: number;
}

export interface GapReportResponse {
  total_assets: number;
  assets_behind: number;
  critical_gaps: number;
  gaps: GapEntry[];
}

export async function submitGapReport(assets: GapReportAsset[]): Promise<GapReportResponse> {
  const res = await fetch(`${API_BASE}/inventory/gap-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assets }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to generate gap report: ${res.status}`);
  }
  return res.json();
}
